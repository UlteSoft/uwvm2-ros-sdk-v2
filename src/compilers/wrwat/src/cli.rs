use super::Result;
use std::collections::BTreeSet;
use std::ffi::{OsStr, OsString};
use std::path::PathBuf;
use wasmparser::WasmFeatures;

const HELP: &str = "\
Usage: wrwat [OPTIONS] SOURCE.wat -o OUTPUT.wasm
Assemble and validate a core WebAssembly text module.

  -o, --output PATH            Output WebAssembly module
      --target wasm32|wasm64   Memory and table address width (default wasm32)
      --core mvp|3.0           Core feature profile (default 3.0)
      --eh | --no-eh           Enable or disable modern exception handling
      --threads                Enable shared memory and atomics
      --shared-memory MOD KEY  Select a bounded shared memory import
      --mte | --no-mte         Enable or disable WasmMTE (default enabled)
      --ros-operation NAME     Allow one exact ROSv2 import (repeatable)
      --build-receipt          Write OUTPUT.wasm.wros-wat.json
  -g                          Emit source-level DWARF
  -h, --help                  Show this help";

pub(crate) struct Options {
    pub source: PathBuf,
    pub output: PathBuf,
    pub memory64: bool,
    pub mvp: bool,
    pub eh: Option<bool>,
    pub threads: bool,
    pub shared: Option<[String; 2]>,
    pub mte: bool,
    pub operations: BTreeSet<String>,
    pub receipt: bool,
    pub debug: bool,
}

pub(crate) fn parse() -> Result<Option<Options>> {
    let mut args = std::env::args_os().skip(1);
    let mut options = Options {
        source: PathBuf::new(), output: PathBuf::new(), memory64: false, mvp: false,
        eh: None, threads: false, shared: None, mte: true, operations: BTreeSet::new(),
        receipt: false, debug: false,
    };
    let mut positional = false;
    while let Some(arg) = args.next() {
        if positional || !arg.as_encoded_bytes().starts_with(b"-") || arg == "-" {
            if !options.source.as_os_str().is_empty() {
                return Err("expected exactly one WAT source".into());
            }
            options.source = PathBuf::from(arg);
            continue;
        }
        let arg = arg.to_str().ok_or("invalid option name")?;
        let (name, inline) = if let Some(rest) = arg.strip_prefix("-o").filter(|s| !s.is_empty()) {
            ("-o", Some(rest))
        } else if arg.starts_with("--") {
            arg.split_once('=').map_or((arg, None), |(k, v)| (k, Some(v)))
        } else {
            (arg, None)
        };
        if inline.is_some() && !matches!(name, "-o" | "--output" | "--core" | "--target" | "--ros-operation") {
            return Err(format!("unexpected attached value for {name}").into());
        }
        let mut value = || -> Result<OsString> {
            inline.map(OsString::from).or_else(|| args.next()).ok_or_else(|| format!("{name} needs a value").into())
        };
        let text = |v: OsString| v.into_string().map_err(|_| "a UTF-8 option value is required");
        match name {
            "-h" | "--help" => { println!("{HELP}"); return Ok(None); }
            "--" => positional = true,
            "-o" | "--output" => options.output = value()?.into(),
            "--target" => options.memory64 = match text(value()?)?.as_str() {
                "wasm32" => false, "wasm64" => true, _ => return Err("expected --target wasm32 or wasm64".into()),
            },
            "--core" => options.mvp = match text(value()?)?.as_str() {
                "mvp" => true, "3.0" => false, _ => return Err("expected --core mvp or 3.0".into()),
            },
            "--eh" => options.eh = Some(true),
            "--no-eh" => options.eh = Some(false),
            "--threads" => options.threads = true,
            "--shared-memory" => options.shared = Some([text(value()?)?, text(value()?)?]),
            "--mte" => options.mte = true,
            "--no-mte" => options.mte = false,
            "--ros-operation" => {
                if !options.operations.insert(text(value()?)?) {
                    return Err("select distinct operations from the installed ROSv2 catalogue".into());
                }
            }
            "--build-receipt" => options.receipt = true,
            "-g" => options.debug = true,
            _ => return Err(format!("unknown option {name}").into()),
        }
    }
    if options.source.extension() != Some(OsStr::new("wat")) || options.output.extension() != Some(OsStr::new("wasm")) {
        return Err("use a .wat source and a .wasm output".into());
    }
    if options.mvp && (options.memory64 || options.threads || options.eh == Some(true)) {
        return Err("MVP requires wasm32 without EH or threads".into());
    }
    Ok(Some(options))
}

impl Options {
    pub fn target(&self) -> &'static str { if self.memory64 { "wasm64" } else { "wasm32" } }

    pub fn features(&self) -> WasmFeatures {
        let mut features = if self.mvp { WasmFeatures::MVP } else { WasmFeatures::WASM3 };
        features.set(WasmFeatures::EXCEPTIONS, !self.mvp && self.eh != Some(false));
        features.set(WasmFeatures::THREADS, self.threads);
        features.set(WasmFeatures::MEMORY64, self.memory64);
        features.set(WasmFeatures::MEMTAG_EXTENSION, self.mte && !self.mvp);
        features
    }

    pub fn feature_names(&self) -> String {
        if self.mvp { return "mvp".to_owned(); }
        let mut names = vec!["wasm3", "-component-model", "-legacy-exceptions",
                             if self.threads { "threads" } else { "-threads" }];
        if !self.memory64 { names.push("-memory64"); }
        if self.eh == Some(false) { names.push("-exceptions"); }
        if self.mte { names.push("memtag-extension"); }
        names.join(",")
    }
}
