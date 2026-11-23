// WROS additions to the native rustc process entry point. Each crate is compiled
// by this same executable through rustc_driver, in a fresh compiler session.
use std::collections::BTreeSet;
use std::env;
use std::ffi::{OsStr, OsString};
use std::fs;
use std::io::{self, ErrorKind};
use std::os::unix::fs::DirBuilderExt;
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode};

const USAGE: &str = "wrrs [OPTIONS] CRATE_ROOT.rs -o GUEST.wasm
  --target wasm32|wasm64        Guest pointer ABI (default wasm32)
  --core 3.0|mvp               WebAssembly core version (default 3.0)
  --[no-]memory64              VM memory64 capability (default on for Core 3)
  --[no-]eh                    Standard Wasm exceptions and Rust cleanup pads (default on)
  --[no-]mte                   WasmMTE stack and global instrumentation (default on)
  --[no-]threads               Shared-memory wasm32 guest (default off)
  --shared-memory-pages N      Imported shared memory maximum (default 256 pages with threads)
  --platform NAME              Check the platform installed in this SDK
  --library NAME ROOT.rs       Build a local no_std dependency (repeat in dependency order)
  --edition 2018|2021|2024     Edition for application and local crates (default 2021)
  -O0|-O1|-O2|-O3|-Os|-Oz     Final LLVM optimization level (default -O2)
  -g                           Retain debug information";

fn invalid(message: impl Into<String>) -> io::Error {
    io::Error::new(ErrorKind::InvalidInput, message.into())
}

struct Options {
    target: String,
    core: String,
    memory64: Option<bool>,
    eh: bool,
    mte: bool,
    threads: bool,
    pages: Option<u32>,
    platform: Option<String>,
    libraries: Vec<(String, PathBuf)>,
    edition: String,
    optimization: String,
    debug: bool,
    source: PathBuf,
    output: PathBuf,
}

fn parse() -> io::Result<Options> {
    let mut args = env::args_os().skip(1);
    let mut opts = Options {
        target: "wasm32".into(), core: "3.0".into(), memory64: None, eh: true,
        mte: true, threads: false, pages: None, platform: None, libraries: vec![],
        edition: "2021".into(), optimization: "2".into(), debug: false,
        source: PathBuf::new(), output: PathBuf::new(),
    };
    let mut names: BTreeSet<String> = ["std", "alloc", "test", "proc_macro", "core", "compiler_builtins",
        "uwrosv2", "u2rosv2", "abb", "wros_observation", "unitree_go2", "wros_guest", "wros_runtime"]
        .into_iter().map(str::to_owned).collect();
    while let Some(arg) = args.next() {
        let mut next = || args.next().ok_or_else(|| invalid(format!("missing value for {}", arg.to_string_lossy())));
        let word = |s: OsString| s.into_string().map_err(|_| invalid("expected a UTF-8 option value"));
        match arg.to_str() {
            Some("--target") => opts.target = word(next()?)?,
            Some("--core") => opts.core = word(next()?)?,
            Some("--edition") => opts.edition = word(next()?)?,
            Some("--platform") => opts.platform = Some(word(next()?)?),
            Some("--memory64") => opts.memory64 = Some(true),
            Some("--no-memory64") => opts.memory64 = Some(false),
            Some("--eh") => opts.eh = true,
            Some("--no-eh") => opts.eh = false,
            Some("--mte") => opts.mte = true,
            Some("--no-mte") => opts.mte = false,
            Some("--threads" | "-pthread") => opts.threads = true,
            Some("--no-threads") => opts.threads = false,
            Some("--shared-memory-pages") => {
                opts.pages = Some(word(next()?)?.parse().map_err(|_| invalid("invalid shared memory limit"))?)
            }
            Some("--library") => {
                let name = word(next()?)?;
                let mut chars = name.bytes();
                if !chars.next().is_some_and(|c| c == b'_' || c.is_ascii_alphabetic())
                    || !chars.all(|c| c == b'_' || c.is_ascii_alphanumeric()) || !names.insert(name.clone()) {
                    return Err(invalid(format!("reserved, repeated or invalid crate name {name}")));
                }
                opts.libraries.push((name, crate_path(PathBuf::from(next()?))?));
            }
            Some("-o" | "--output") => opts.output = PathBuf::from(next()?),
            Some("-g") => opts.debug = true,
            Some("-O0" | "-O1" | "-O2" | "-O3" | "-Os" | "-Oz") => opts.optimization = arg.to_string_lossy()[2..].into(),
            Some(s) if s.starts_with('-') => return Err(invalid(format!("unknown option {s}"))),
            _ if opts.source.as_os_str().is_empty() => opts.source = crate_path(PathBuf::from(arg))?,
            _ => return Err(invalid("supply one application crate root and use --library for dependencies")),
        }
    }
    if !matches!(opts.target.as_str(), "wasm32" | "wasm64") || !matches!(opts.core.as_str(), "3.0" | "mvp")
        || !matches!(opts.edition.as_str(), "2018" | "2021" | "2024") {
        return Err(invalid("unsupported target, core version or Rust edition"));
    }
    let memory64 = *opts.memory64.get_or_insert(opts.core == "3.0");
    if opts.core == "mvp" && (opts.eh || opts.threads || memory64) {
        return Err(invalid("MVP requires --no-eh --no-threads --no-memory64"));
    }
    if opts.target == "wasm64" && (!memory64 || opts.threads) {
        return Err(invalid("the UWVM wasm64 Preview 1 ABI requires memory64 and single-threaded execution"));
    }
    if opts.pages.is_some() && !opts.threads {
        return Err(invalid("--shared-memory-pages requires --threads"));
    }
    if opts.threads {
        let pages = *opts.pages.get_or_insert(256);
        let maximum = if opts.mte { 4096 } else { 65536 };
        if pages == 0 || pages > maximum {
            return Err(invalid("shared memory maximum is outside the selected memory layout"));
        }
    }
    if opts.source.as_os_str().is_empty() || opts.output.extension() != Some(OsStr::new("wasm")) {
        return Err(invalid("supply a .rs crate root and -o GUEST.wasm"));
    }
    opts.output = std::path::absolute(opts.output)?;
    Ok(opts)
}

fn crate_path(path: PathBuf) -> io::Result<PathBuf> {
    if path.extension() != Some(OsStr::new("rs")) || !path.is_file() {
        return Err(invalid(format!("expected a Rust crate root at {}", path.display())));
    }
    fs::canonicalize(path)
}

struct Scratch(PathBuf);
impl Scratch {
    fn create(parent: &Path) -> io::Result<Self> {
        let mut dir = fs::DirBuilder::new();
        dir.mode(0o700);
        for attempt in 0..256 {
            let path = parent.join(format!(".wrrs-{}-{attempt}", std::process::id()));
            match dir.create(&path) {
                Ok(()) => return Ok(Self(path)),
                Err(e) if e.kind() == ErrorKind::AlreadyExists => continue,
                Err(e) => return Err(e),
            }
        }
        Err(invalid("could not reserve an output staging directory"))
    }
}
impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn run(command: &mut Command, stage: &str) -> io::Result<()> {
    let status = command.status()?;
    if !status.success() {
        return Err(io::Error::other(format!("{stage} failed ({status})")));
    }
    Ok(())
}

fn selected_platform(sdk: &Path) -> io::Result<String> {
    let root = sdk.join("include/u2rosv2/platform");
    let mut platforms = Vec::new();
    if root.is_dir() {
        for entry in fs::read_dir(root)? {
            let entry = entry?;
            if entry.path().join("rust/lib.rs").is_file() {
                platforms.push(entry.file_name().into_string().map_err(|_| invalid("invalid SDK platform directory"))?);
            }
        }
    }
    match platforms.len() {
        0 => Ok("generic".to_owned()),
        1 => Ok(platforms.remove(0)),
        _ => Err(invalid("the installed SDK must contain one selected platform")),
    }
}

struct Compiler<'a> {
    opts: &'a Options,
    exe: PathBuf,
    work: &'a Path,
    triple: String,
    metadata: PathBuf,
    crates: Vec<String>,
    externs: Vec<(String, String)>,
}
impl Compiler<'_> {
    fn compile(&mut self, name: &str, source: &Path, edition: &str, flags: &[&str]) -> io::Result<()> {
        let mut rustc = Command::new(&self.exe);
        rustc.arg0("rustc").current_dir(self.work).env("RUSTC_BOOTSTRAP", "1")
            .env("TMPDIR", self.work).env_remove("RUSTC_LOG")
            .args(["--target", &self.triple, "--crate-type=rlib", "--edition", edition, "--crate-name", name])
            .arg("--sysroot").arg(self.work).args(["-Copt-level=3", "-Cno-prepopulate-passes",
                "-Clto=off", "-Ccodegen-units=1", "-Zmir-opt-level=0", "-Cembed-bitcode=no", "-Ctarget-cpu=mvp"]);
        if self.opts.core == "3.0" {
            rustc.arg("-Ctarget-feature=+bulk-memory,+mutable-globals,+multivalue,+sign-ext,+nontrapping-fptoint,+reference-types,+simd128,+relaxed-simd,+tail-call,+extended-const");
        }
        if self.opts.threads {
            rustc.arg("-Ctarget-feature=+atomics,+bulk-memory,+mutable-globals");
        }
        rustc.arg(if self.opts.eh {"-Ctarget-feature=+exception-handling"} else {"-Ctarget-feature=-exception-handling"});
        rustc.arg(if self.opts.eh {"-Cpanic=unwind"} else {"-Cpanic=abort"});
        rustc.arg(if self.opts.debug || self.opts.mte {"-Cdebuginfo=2"} else {"-Cdebuginfo=0"});
        let ir = if !self.opts.mte {"plain"} else if self.opts.debug {"mte"} else {"mte-strip-debug"};
        rustc.arg(format!("-Cllvm-args=-wros-ir={ir}"));
        for (alias, krate) in &self.externs {
            rustc.arg("--extern").arg(format!("{alias}={}/lib{krate}.rmeta", self.metadata.display()));
        }
        rustc.args(flags).arg(format!("--emit=metadata={}/lib{name}.rmeta,llvm-bc={name}.bc", self.metadata.display()))
            .arg(source);
        run(&mut rustc, &format!("rustc ({name})"))?;
        self.crates.push(name.to_owned());
        Ok(())
    }
    fn expose(&mut self, alias: &str, name: &str) {
        self.externs.push((alias.into(), name.into()));
    }
}

fn build(opts: Options) -> io::Result<()> {
    let exe = env::current_exe()?;
    let sdk = exe.parent().and_then(Path::parent).ok_or_else(|| invalid("expected SDK/bin/wrrs"))?;
    let platform = selected_platform(sdk)?;
    if let Some(requested) = &opts.platform && requested != &platform {
        return Err(invalid(format!("requested platform {requested}; installed platform {platform}")));
    }
    let output_dir = opts.output.parent().ok_or_else(|| invalid("output needs a parent directory"))?;
    let work = Scratch::create(output_dir)?;
    let mut triple = format!("{}-wasip1", opts.target);
    if opts.threads { triple.push_str("-threads"); }
    // Relative --emit and --extern names also support output parent paths containing ',' or '='.
    let metadata = PathBuf::from("lib/rustlib").join(&triple).join("lib");
    fs::create_dir_all(work.0.join(&metadata))?;
    let mut cc = Compiler {opts: &opts, exe: exe.clone(), work: &work.0, triple,
                           metadata, crates: vec![], externs: vec![]};
    let rust = sdk.join("src/compilers/rust");
    let lib = rust.join("upstream/library");
    cc.compile("core", &lib.join("core/src/lib.rs"), "2024", &[])?;
    cc.compile("compiler_builtins", &lib.join("compiler-builtins/compiler-builtins/src/lib.rs"), "2024",
        &["--cfg", "feature=\"compiler-builtins\"", "--cfg", "feature=\"unmangled-names\"", "--cfg", "feature=\"mem\""])?;
    cc.compile("wros_runtime", &rust.join("runtime.rs"), "2024", &[])?;
    cc.expose("wros_runtime", "wros_runtime");
    let stable = ["-Zallow-features="];
    cc.compile("uwrosv2", &sdk.join("include/u2rosv2/universal/rust/uwrosv2/src/lib.rs"), "2021", &stable)?;
    cc.expose("uwrosv2", "uwrosv2");
    cc.expose("u2rosv2", "uwrosv2");
    if platform != "generic" {
        let name = if platform == "unitree" {"unitree_go2"} else {"wros_observation"};
        cc.compile(name, &sdk.join("include/u2rosv2/platform").join(&platform).join("rust/lib.rs"), "2021", &stable)?;
        cc.expose(name, name);
        if platform == "abb" { cc.expose("abb", name); }
    }
    for (name, path) in &opts.libraries {
        cc.compile(name, path, &opts.edition, &stable)?;
        cc.expose(name, name);
    }
    cc.compile("wros_guest", &opts.source, &opts.edition, &stable)?;
    let mut backend = Command::new("python3");
    backend.current_dir(&work.0).env("TMPDIR", &work.0)
        .args(["-I", "-B"]).arg(rust.join("lower.py"))
        .args(["--target", &opts.target, "--core", &opts.core, "-O", &opts.optimization])
        .arg(if opts.eh {"--eh"} else {"--no-eh"}).arg(if opts.mte {"--mte"} else {"--no-mte"})
        .arg(if opts.memory64 == Some(true) {"--memory64"} else {"--no-memory64"});
    if let Some(pages) = opts.pages { backend.arg("--shared-memory-pages").arg(pages.to_string()); }
    if opts.debug { backend.arg("-g"); }
    for name in &cc.crates { backend.arg(format!("{name}.bc")); }
    run(&mut backend, "Wasm code generation and link")?;
    fs::rename(work.0.join("guest.wasm"), &opts.output)
}

pub(super) fn main() -> ExitCode {
    if matches!(env::args_os().nth(1).as_deref().and_then(OsStr::to_str), Some("-h" | "--help")) {
        println!("{USAGE}");
        return ExitCode::SUCCESS;
    }
    if matches!(env::args_os().nth(1).as_deref().and_then(OsStr::to_str), Some("-V" | "--version")) {
        println!("wrrs (WROS SDK native Rust compiler)");
        return rustc_driver::main();
    }
    match parse().and_then(build) {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => { eprintln!("wrrs: {error}"); ExitCode::FAILURE }
    }
}
