//! Core-only WAT parser and binary validator for the SDK's linear WasmMTE profile.
#![forbid(unsafe_code)]

mod cli;
mod policy;

use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::error::Error;
use std::fs::{self, File};
use std::io::{self, Read, Write};
use std::path::Path;
use wasmparser::{BinaryReader, MemoryType, Operator, Parser, Payload, TypeRef, Validator, WasmFeatures};
use wast::core::{EncodeOptions, GenerateDwarf};
use wast::parser::{ParseBuffer, parse};

type Result<T> = std::result::Result<T, Box<dyn Error>>;
const SOURCE_LIMIT: usize = 8 << 20;
const MODULE_LIMIT: usize = 64 << 20;

fn check_globals(data: &[u8], memories: &[MemoryType]) -> Result<()> {
    let mut input = BinaryReader::new(data, 0);
    if input.read_var_u64()? != 2 {
        return Err("expected WasmMTE globals version 2".into());
    }
    let count = input.read_var_u64()?;
    if count > (input.bytes_remaining() / 3) as u64 {
        return Err("truncated WasmMTE globals descriptors".into());
    }
    let mut ranges = Vec::new();
    for _ in 0..count {
        let index = input.read_var_u32()?;
        let address = input.read_var_u64()?;
        let length = input.read_var_u64()?;
        let memory = memories.get(index as usize).ok_or("invalid WasmMTE globals memory index")?;
        let end = address.checked_add(length).ok_or("WasmMTE globals range overflows")?;
        let capacity = (memory.initial as u128) << memory.page_size_log2.unwrap_or(16);
        if end as u128 > capacity {
            return Err("WasmMTE globals range exceeds minimum memory size".into());
        }
        if length != 0 {
            ranges.push((index, address / 16, (end - 1) / 16));
        }
    }
    if !input.eof() {
        return Err("trailing WasmMTE globals descriptor bytes".into());
    }
    ranges.sort_unstable();
    if ranges.windows(2).any(|pair| pair[0].0 == pair[1].0 && pair[0].2 >= pair[1].1) {
        return Err("overlapping WasmMTE globals granules".into());
    }
    Ok(())
}

fn check_binary(bytes: &[u8], features: WasmFeatures, policy: &mut policy::ImportPolicy<'_>) -> Result<(usize, bool)> {
    if !bytes.starts_with(b"\0asm\x01\0\0\0") {
        return Err("expected a core WebAssembly module".into());
    }
    let types = Validator::new_with_features(features).validate_all(bytes)?;
    if types.as_ref().core_type_count_in_module() > 100_000 { return Err("expanded Wasm type budget exceeded".into()); }
    let mut memory_free = true;
    let mut tag_writes = 0;
    let mut memories = Vec::new();
    let mut globals = None;
    for payload in Parser::new(0).parse_all(bytes) {
        match payload? {
            Payload::ImportSection(section) => {
                if section.count() > 100_000 { return Err("Wasm import budget exceeded".into()); }
                for import in section.into_imports() {
                    let import = import?;
                    policy.import(import, &types)?;
                    if let TypeRef::Memory(memory) = import.ty {
                        memory_free = false;
                        memories.push(memory);
                    }
                }
            }
            Payload::MemorySection(section) => {
                memory_free &= section.count() == 0;
                for memory in section {
                    memories.push(memory?);
                }
            }
            Payload::ExportSection(section) => {
                if section.count() > 100_000 { return Err("Wasm export budget exceeded".into()); }
                for export in section { policy::check_interface(export?.name)?; }
            }
            Payload::DataSection(section) => memory_free &= section.count() == 0,
            Payload::DataCountSection { count, .. } => memory_free &= count == 0,
            Payload::CustomSection(section) if section.name().starts_with("component-type") || section.name() == "component-name" => {
                return Err(format!("Component Model custom sections are prohibited: {}", section.name()).into());
            }
            Payload::CodeSectionEntry(body) => {
                let mut ops = body.get_operators_reader()?;
                while !ops.eof() {
                    if matches!(
                        ops.read()?,
                        Operator::MemtagStore { .. }
                            | Operator::MemtagStorez { .. }
                            | Operator::MemtagUntagstore { .. }
                            | Operator::MemtagUntagstorez { .. }
                            | Operator::MemtagRandomstore { .. }
                            | Operator::MemtagRandomstorez { .. }
                            | Operator::MemtagHintstore { .. }
                            | Operator::MemtagHintstorez { .. }
                            | Operator::MemtagClaim { .. }
                            | Operator::MemtagClaimz { .. }
                            | Operator::MemtagActivate { .. }
                    ) {
                        tag_writes += 1;
                    }
                }
            }
            Payload::CustomSection(section) if section.name() == "memtag.globals" => {
                return Err("obsolete WasmMTE globals section".into());
            }
            Payload::CustomSection(section) if section.name() == "uwvm.memtag.linear.globals" => {
                if !features.contains(WasmFeatures::MEMTAG_EXTENSION) {
                    return Err("WasmMTE globals requires the MTE feature".into());
                }
                if globals.replace(section.data()).is_some() {
                    return Err("duplicate WasmMTE globals sections".into());
                }
            }
            _ => {}
        }
    }
    if let Some(data) = globals {
        check_globals(data, &memories)?;
    }
    policy.finish()?;
    Ok((tag_writes, memory_free))
}

fn read_bounded(path: &Path, limit: usize) -> Result<Vec<u8>> {
    let mut data = Vec::new();
    File::open(path)?.take((limit + 1) as u64).read_to_end(&mut data)?;
    if data.is_empty() || data.len() > limit {
        return Err(format!("{} must contain 1 to {limit} bytes", path.display()).into());
    }
    Ok(data)
}

fn sha(data: &[u8]) -> String { format!("{:x}", Sha256::digest(data)) }

fn run() -> Result<()> {
    let Some(args) = cli::parse()? else { return Ok(()); };
    let executable = std::env::current_exe()?;
    let sdk = executable.parent().and_then(Path::parent).ok_or("expected installed bin/wrwat")?;
    let lock: Value = serde_json::from_slice(&read_bounded(&sdk.join("third-parties/wat-mte/release.json"), 16 << 10)?)?;
    let binary = read_bounded(Path::new("/proc/self/exe"), 32 << 20)?;
    let tool_digest = sha(&binary);
    if lock["binary_bytes"].as_u64() != Some(binary.len() as u64) || lock["binary_sha256"].as_str() != Some(&tool_digest) {
        return Err("WAT assembler differs from the pinned release".into());
    }
    let catalogue: Value = serde_json::from_slice(&read_bounded(&sdk.join("share/abi/ros.json"), 2 << 20)?)?;
    let mut policy = policy::ImportPolicy::new(&args, &catalogue)?;
    let source = read_bounded(&args.source, SOURCE_LIMIT)?;
    if source.starts_with(b"\0asm") { return Err("wrwat expects text input".into()); }
    let text = std::str::from_utf8(&source)?;
    let basename = Path::new(args.source.file_name().ok_or("missing WAT filename")?);
    let parse_buffer = ParseBuffer::new(text)?;
    let mut module = parse(&parse_buffer).map_err(|mut error| {
        error.set_path(basename);
        error
    })?;
    let mut options = EncodeOptions::new();
    if args.debug { options.dwarf(basename, text, GenerateDwarf::Full); }
    let bytes = options.encode_wat(&mut module).map_err(|mut error| {
        error.set_path(basename);
        error.set_text(text);
        error
    })?;
    if bytes.len() > MODULE_LIMIT { return Err("assembled module exceeds the output budget".into()); }
    let (tag_writes, memory_free) = check_binary(&bytes, args.features(), &mut policy)?;
    let parent = args.output.parent().filter(|p| !p.as_os_str().is_empty()).unwrap_or(Path::new("."));
    let stage = tempfile::tempdir_in(parent)?;
    let guest = stage.path().join("guest.wasm");
    fs::write(&guest, &bytes)?;
    let proof = stage.path().join("receipt.json");
    let sidecar = args.output.with_extension("wasm.wros-wat.json");
    if args.receipt {
        let receipt = json!({
            "language": "wat", "target": args.target(), "validation_features": args.feature_names(),
            "mte_requested": args.mte, "linear_memory_free": memory_free, "authored_tag_writes": tag_writes,
            "shared_memory": args.shared, "thread_spawn": policy.spawn, "ros_operations": args.operations,
            "assembler_sha256": tool_digest, "source_sha256": sha(&source), "wasm_sha256": sha(&bytes)
        });
        let mut file = File::create(&proof)?;
        serde_json::to_writer_pretty(&mut file, &receipt)?;
        file.write_all(b"\n")?;
    }
    // Serialize publication by cooperating compilers, including builds without a receipt.
    let directory = File::open(parent)?;
    directory.lock()?;
    if args.output.is_dir() { return Err("output must be a regular module path".into()); }
    if args.receipt {
        fs::rename(proof, sidecar)?;
    } else {
        match fs::remove_file(sidecar) {
            Err(e) if e.kind() != io::ErrorKind::NotFound => return Err(e.into()),
            _ => {}
        }
    }
    fs::rename(guest, &args.output)?;
    Ok(())
}

fn main() -> std::process::ExitCode {
    // Keep the same wall-time budget as the release assembler driver.
    std::thread::spawn(|| {
        std::thread::sleep(std::time::Duration::from_secs(60));
        eprintln!("wrwat: WAT assembly timed out");
        std::process::exit(1);
    });
    match run() {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(error) => {
            let _ = writeln!(io::stderr().lock(), "wrwat: {error}");
            std::process::ExitCode::FAILURE
        }
    }
}
