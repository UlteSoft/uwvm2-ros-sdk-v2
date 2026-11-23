//! Bind imports and exports to the installed ROSv2 catalogue and the selected shared-memory owner.
use super::Result;
use super::cli::Options;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use wasmparser::{FuncType, Import, TypeRef, ValType, types::Types};

pub(crate) fn check_interface(name: &str) -> Result<()> {
    // Match WIT package:interface/name with an optional version or path suffix.
    fn word(s: &str) -> bool {
        s.starts_with(|c: char| c.is_ascii_lowercase()) &&
            s.bytes().all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == b'-')
    }
    let wit_name = name.strip_prefix("[export]").unwrap_or(name);
    let wit = wit_name.split_once(':').is_some_and(|(namespace, rest)| {
        rest.split_once('/').is_some_and(|(package, rest)| {
            word(namespace) && word(package) && word(rest.split(['@', '#', '/']).next().unwrap_or(""))
        })
    });
    if wit || matches!(name, "wasip2" | "wasip3" | "wasi_snapshot_preview2" | "wasi_snapshot_preview3")
        || ["wasi:", "cm32p2", "cm32p3", "cabi_", "canonical_abi", "[resource-new]", "[resource-drop]",
            "[resource-rep]", "[async-lower]", "[async-lift]"].iter().any(|prefix| name.starts_with(prefix)) {
        return Err(format!("WASI P2/P3 and Component Model interfaces are prohibited: {name}").into());
    }
    Ok(())
}

pub(crate) struct ImportPolicy<'a> {
    options: &'a Options,
    module: &'a str,
    authorized: BTreeMap<&'a str, &'a Value>,
    seen: BTreeSet<String>,
    pub shared: bool,
    pub spawn: bool,
}

impl<'a> ImportPolicy<'a> {
    pub fn new(options: &'a Options, catalogue: &'a Value) -> Result<Self> {
        let module = catalogue["module"].as_str().ok_or("invalid ROSv2 module name")?;
        let mut authorized = BTreeMap::new();
        for row in catalogue["operations"].as_array().ok_or("invalid ROSv2 operation catalogue")? {
            let name = row["name"].as_str().ok_or("invalid ROSv2 operation name")?;
            if options.operations.contains(name) && authorized.insert(name, &row["wasm_signature"]).is_some() {
                return Err("duplicate ROSv2 catalogue operation".into());
            }
        }
        if options.operations.len() != authorized.len() {
            return Err("select distinct operations from the installed ROSv2 catalogue".into());
        }
        Ok(Self { options, module, authorized, seen: BTreeSet::new(), shared: false, spawn: false })
    }

    pub fn import(&mut self, import: Import<'_>, types: &Types) -> Result<()> {
        let Import { module, name, ty } = import;
        check_interface(module)?;
        check_interface(name)?;
        if let TypeRef::Memory(memory) = ty {
            if self.options.threads && !self.shared &&
                self.options.shared.as_ref().is_some_and(|pair| pair[0] == module && pair[1] == name) {
                if !memory.shared || memory.maximum.is_none() || memory.memory64 != self.options.memory64 || memory.page_size_log2.is_some() {
                    return Err("selected owner must be a bounded shared memory of the configured address width".into());
                }
                self.shared = true;
                return Ok(());
            }
        }
        if let TypeRef::Func(index) = ty {
            // validate_all succeeded, so this index denotes a core function type.
            let function = types[types.as_ref().core_type_at_in_module(index)].unwrap_func();
            if self.options.threads && !self.options.memory64 && !self.spawn && module == "wasi" && name == "thread-spawn" &&
                function.params() == [ValType::I32] && function.results() == [ValType::I32] {
                self.spawn = true;
                return Ok(());
            }
            if module == self.module && self.authorized.get(name).is_some_and(|s| signature_matches(function, s))
                && self.seen.insert(name.to_owned()) {
                return Ok(());
            }
        }
        Err(format!("unauthorized import or signature {module}.{name}").into())
    }

    pub fn finish(&self) -> Result<()> {
        if self.seen != self.options.operations { return Err("the module must import each selected ROSv2 operation exactly once".into()); }
        if self.options.shared.is_some() && !self.shared { return Err("expected exactly one declared shared memory import".into()); }
        if self.spawn && !self.shared { return Err("thread-spawn requires an explicitly selected shared memory owner".into()); }
        Ok(())
    }
}

fn signature_matches(function: &FuncType, signature: &Value) -> bool {
    fn list_matches(types: &[ValType], names: &Value) -> bool {
        names.as_array().is_some_and(|names| names.len() == types.len() &&
            names.iter().zip(types).all(|(name, ty)| name.as_str().is_some_and(|s| s == ty.to_string())))
    }
    list_matches(function.params(), &signature["parameters"]) && list_matches(function.results(), &signature["results"])
}
