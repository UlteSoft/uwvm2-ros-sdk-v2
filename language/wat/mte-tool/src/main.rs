//! Core-only WAT parser and binary validator for the SDK's linear WasmMTE profile.
#![forbid(unsafe_code)]

use std::error::Error;
use std::fs::{self, File};
use std::io::{self, Read};
use std::path::Path;
use wasmparser::{BinaryReader, MemoryType, Operator, Parser, Payload, TypeRef, Validator, WasmFeatures};
use wast::core::{EncodeOptions, GenerateDwarf};
use wast::parser::{ParseBuffer, parse};

type Result<T> = std::result::Result<T, Box<dyn Error>>;
const SOURCE_LIMIT: usize = 8 << 20;
const MODULE_LIMIT: usize = 64 << 20;

fn switch(text: &str) -> Result<bool> {
    match text {
        "on" => Ok(true),
        "off" => Ok(false),
        _ => Err("expected on or off".into()),
    }
}

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

fn check_binary(bytes: &[u8], features: WasmFeatures) -> Result<usize> {
    if !bytes.starts_with(b"\0asm\x01\0\0\0") {
        return Err("expected a core WebAssembly module".into());
    }
    Validator::new_with_features(features).validate_all(bytes)?;
    let mut tag_writes = 0;
    let mut memories = Vec::new();
    let mut globals = None;
    for payload in Parser::new(0).parse_all(bytes) {
        match payload? {
            Payload::ImportSection(section) => {
                for import in section.into_imports() {
                    if let TypeRef::Memory(memory) = import?.ty {
                        memories.push(memory);
                    }
                }
            }
            Payload::MemorySection(section) => {
                for memory in section {
                    memories.push(memory?);
                }
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
    Ok(tag_writes)
}

fn run() -> Result<()> {
    let argv: Vec<_> = std::env::args().skip(1).collect();
    let [source, output, core, target, eh, threads, mte, debug] = argv.as_slice() else {
        return Err("expected source, output, core, target, EH, threads, MTE and debug".into());
    };
    let eh = switch(eh)?;
    let threads = switch(threads)?;
    let mte = switch(mte)?;
    let debug = switch(debug)?;
    let memory64 = match target.as_str() {
        "wasm32" => false,
        "wasm64" => true,
        _ => return Err("expected wasm32 or wasm64".into()),
    };
    let mut features = match core.as_str() {
        "mvp" if !eh && !threads && !memory64 => WasmFeatures::MVP,
        "3.0" => WasmFeatures::WASM3,
        _ => return Err("incompatible core profile".into()),
    };
    features.set(WasmFeatures::EXCEPTIONS, eh);
    features.set(WasmFeatures::THREADS, threads);
    features.set(WasmFeatures::MEMORY64, memory64);
    features.set(WasmFeatures::MEMTAG_EXTENSION, mte && core == "3.0");

    let mut text = String::new();
    File::open(source)?.take((SOURCE_LIMIT + 1) as u64).read_to_string(&mut text)?;
    if text.is_empty() || text.len() > SOURCE_LIMIT {
        return Err("WAT source exceeds the assembly budget".into());
    }
    let parse_buffer = ParseBuffer::new(&text)?;
    let mut module = parse(&parse_buffer).map_err(|mut error| {
        error.set_path(Path::new(source));
        error
    })?;
    let mut options = EncodeOptions::new();
    if debug {
        options.dwarf(Path::new(source), &text, GenerateDwarf::Full);
    }
    let bytes = options.encode_wat(&mut module).map_err(|mut error| {
        error.set_path(Path::new(source));
        error.set_text(&text);
        error
    })?;
    if bytes.len() > MODULE_LIMIT {
        return Err("assembled module exceeds the output budget".into());
    }
    let tag_writes = check_binary(&bytes, features)?;
    fs::write(output, bytes)?;
    println!("{tag_writes}");
    Ok(())
}

fn main() -> std::process::ExitCode {
    match run() {
        Ok(()) => std::process::ExitCode::SUCCESS,
        Err(error) => {
            use io::Write;
            let _ = writeln!(io::stderr().lock(), "{error}");
            std::process::ExitCode::FAILURE
        }
    }
}
