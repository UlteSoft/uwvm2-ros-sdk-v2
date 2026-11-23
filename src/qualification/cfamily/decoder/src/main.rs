use std::collections::{BTreeMap, BTreeSet};
use std::error::Error;
use wasmparser::{
    ConstExpr, DataKind, ElementItems, ElementKind, KnownCustom, Name, Operator, OperatorsReader,
    Parser, Payload, TableInit, TypeRef, WasmFeatures,
};

type Result<T> = std::result::Result<T, Box<dyn Error>>;

fn classify<'a>(operator: &Operator<'a>) -> (&'static str, &'static str) {
    macro_rules! names {
        ($(@$proposal:ident $op:ident $({ $($field:ident: $ty:ty),* })? => $visit:ident ($($arity:tt)*))*) => {
            match operator {
                $(Operator::$op $({$($field: _,)*})? => (stringify!($proposal), stringify!($op)),)*
                _ => ("unknown", "unknown"),
            }
        }
    }
    wasmparser::for_each_operator!(names)
}

#[derive(Default)]
struct Counts {
    bodies: u64,
    operators: u64,
    shared_memories: u64,
    thread_spawn: u64,
    tags: u64,
    memtag: BTreeMap<&'static str, u64>,
    threads: BTreeMap<&'static str, u64>,
    eh: BTreeMap<&'static str, u64>,
    memtag_functions: BTreeSet<u32>,
    memtag_samples: BTreeMap<(&'static str, Option<u32>), (u64, String)>,
    names: BTreeMap<u32, String>,
    global_names: BTreeMap<u32, String>,
    global_accesses: BTreeMap<(u32, u32), u64>,
    shared_memory_types: BTreeSet<(String, u64, Option<u64>)>,
    thread_entries: BTreeSet<String>,
}

impl Counts {
    fn decode(&mut self, reader: OperatorsReader<'_>, function: Option<u32>) -> Result<()> {
        for item in reader.into_iter_with_offsets() {
            let (operator, offset) = item?;
            self.operators += 1;
            if let (Some(index), Operator::GlobalGet { global_index }) = (function, &operator) {
                *self.global_accesses.entry((index, *global_index)).or_default() += 1;
            }
            let (proposal, name) = classify(&operator);
            match proposal {
                "memtag_extension" => {
                    *self.memtag.entry(name).or_default() += 1;
                    self.memtag_functions.extend(function);
                    self.memtag_samples.entry((name, function))
                        .or_insert_with(|| (offset, format!("{operator:?}")));
                }
                "threads" | "shared_everything_threads" => {
                    *self.threads.entry(name).or_default() += 1;
                }
                "exceptions" | "legacy_exceptions" => {
                    *self.eh.entry(name).or_default() += 1;
                }
                "unknown" => return Err(format!("unclassified operator at 0x{offset:x}").into()),
                _ => {}
            }
        }
        Ok(())
    }

    fn decode_const(&mut self, expression: ConstExpr<'_>) -> Result<()> {
        self.decode(expression.get_operators_reader(), None)
    }

    fn add(&mut self, member: &Self) {
        self.bodies += member.bodies;
        self.operators += member.operators;
        self.shared_memories += member.shared_memories;
        self.thread_spawn += member.thread_spawn;
        self.tags += member.tags;
        for (total, counts) in [(&mut self.memtag, &member.memtag),
                                (&mut self.threads, &member.threads),
                                (&mut self.eh, &member.eh)] {
            for (family, count) in counts {
                *total.entry(family).or_default() += count;
            }
        }
    }

    fn show(&self, label: &str) {
        println!(
            "{label} bodies={} operators={} memtag_total={} threads_total={} shared_memories={} thread_spawn_imports={} eh_total={} tags={} memtag={:?} threads={:?} eh={:?}",
            self.bodies, self.operators, self.memtag.values().sum::<u64>(), self.threads.values().sum::<u64>(),
            self.shared_memories, self.thread_spawn, self.eh.values().sum::<u64>(), self.tags,
            self.memtag, self.threads, self.eh,
        );
    }

    fn samples(&self) {
        let mut shown = BTreeSet::new();
        for ((family, index), (offset, operator)) in &self.memtag_samples {
            let name = index.and_then(|index| self.names.get(&index)).map(String::as_str).unwrap_or("?");
            let user_code = name == "main" || name == "__original_main" || name.contains("update") || name.contains("run_worker");
            if shown.insert(family) || user_code {
                println!("  function={index:?} {name} offset=0x{offset:x} {operator}");
            }
        }
        for (module, initial, maximum) in &self.shared_memory_types {
            println!("  shared memory {module} initial={initial} maximum={maximum:?}");
        }
        for entry in &self.thread_entries {
            println!("  thread ABI {entry}");
        }
        for ((function, global), count) in &self.global_accesses {
            let Some(name) = self.names.get(function) else {continue};
            let Some(global_name) = self.global_names.get(global) else {continue};
            if name.contains("run_worker") || name.contains("wasi_thread_start") || name == "__original_main" {
                if global_name.contains("tls_base") || global_name.contains("stack_pointer") {
                    println!("  function={function} {name} reads {global_name} count={count}");
                }
            }
        }
    }
}

fn decode_module(bytes: &[u8]) -> Result<Counts> {
    let mut parser = Parser::new(0);
    parser.set_features(WasmFeatures::all());
    let mut counts = Counts::default();
    let mut imported_functions = 0;
    for entry in parser.parse_all(bytes) {
        match entry? {
            Payload::Version { num: 1, encoding: wasmparser::Encoding::Module, .. } => {}
            Payload::Version { .. } => return Err("expected a version-1 core wasm module".into()),
            Payload::ImportSection(imports) => {
                for import in imports.into_imports() {
                    let import = import?;
                    match import.ty {
                        TypeRef::Func(_) | TypeRef::FuncExact(_) => {
                            imported_functions += 1;
                            let name = import.name.to_ascii_lowercase().replace('_', "-");
                            if name.contains("thread-spawn") {
                                counts.thread_spawn += 1;
                                counts.thread_entries.insert(format!("import {}.{}", import.module, import.name));
                            }
                        }
                        TypeRef::Memory(memory) if memory.shared => {
                            counts.shared_memories += 1;
                            counts.shared_memory_types.insert(
                                (format!("import {}.{}", import.module, import.name), memory.initial, memory.maximum));
                        }
                        TypeRef::Tag(_) => counts.tags += 1,
                        _ => {}
                    }
                }
            }
            Payload::CodeSectionEntry(body) => {
                let index = Some(imported_functions + counts.bodies as u32);
                counts.decode(body.get_operators_reader()?, index)?;
                counts.bodies += 1;
            }
            Payload::MemorySection(memories) => {
                for memory in memories {
                    let memory = memory?;
                    if memory.shared {
                        counts.shared_memories += 1;
                        counts.shared_memory_types.insert(("defined".to_owned(), memory.initial, memory.maximum));
                    }
                }
            }
            Payload::ExportSection(exports) => {
                for export in exports {
                    let export = export?;
                    if export.name == "wasi_thread_start" {
                        counts.thread_entries.insert(format!("export {} index={}", export.name, export.index));
                    }
                }
            }
            Payload::TagSection(tags) => {
                for tag in tags {
                    tag?;
                    counts.tags += 1;
                }
            }
            Payload::GlobalSection(globals) => {
                for global in globals {
                    counts.decode_const(global?.init_expr)?;
                }
            }
            Payload::TableSection(tables) => {
                for table in tables {
                    if let TableInit::Expr(expression) = table?.init {
                        counts.decode_const(expression)?;
                    }
                }
            }
            Payload::ElementSection(elements) => {
                for element in elements {
                    let element = element?;
                    if let ElementKind::Active { offset_expr, .. } = element.kind {
                        counts.decode_const(offset_expr)?;
                    }
                    if let ElementItems::Expressions(_, expressions) = element.items {
                        for expression in expressions {
                            counts.decode_const(expression?)?;
                        }
                    }
                }
            }
            Payload::DataSection(data) => {
                for segment in data {
                    if let DataKind::Active { offset_expr, .. } = segment?.kind {
                        counts.decode_const(offset_expr)?;
                    }
                }
            }
            Payload::CustomSection(custom) => {
                if let KnownCustom::Name(names) = custom.as_known() {
                    for section in names {
                        let (map, target) = match section? {
                            Name::Function(functions) => (functions, &mut counts.names),
                            Name::Global(globals) => (globals, &mut counts.global_names),
                            _ => continue,
                        };
                        for mapping in map {
                            let mapping = mapping?;
                            target.insert(mapping.index, mapping.name.to_owned());
                        }
                    }
                }
            }
            _ => {}
        }
    }
    Ok(counts)
}

fn decode_archive(label: &str, bytes: &[u8]) -> Result<()> {
    let mut offset = 8;
    let mut long_names = &[][..];
    let mut count = 0;
    let mut total = Counts::default();
    while offset < bytes.len() {
        let header = bytes.get(offset..offset + 60).ok_or("short archive member header")?;
        if &header[58..] != b"`\n" {
            return Err(format!("{label}: invalid archive member header at {offset}").into());
        }
        let name = std::str::from_utf8(&header[..16])?.trim_end();
        let size: usize = std::str::from_utf8(&header[48..58])?.trim().parse()?;
        let start = offset + 60;
        let end = start.checked_add(size).ok_or("archive member size overflow")?;
        let mut payload = bytes.get(start..end).ok_or("short archive member")?;
        offset = end + (size % 2);
        let member = match name {
            "/" | "/SYM64/" => continue,
            "//" => {
                long_names = payload;
                continue;
            }
            _ if name.starts_with("#1/") => {
                let length: usize = name[3..].parse()?;
                let member = std::str::from_utf8(payload.get(..length).ok_or("short BSD member name")?)?
                    .trim_end_matches('\0');
                payload = &payload[length..];
                if member.starts_with("__.SYMDEF") {
                    continue;
                }
                member
            }
            _ if name.starts_with('/') => {
                let name_offset: usize = name[1..].parse()?;
                let tail = long_names.get(name_offset..).ok_or("GNU long name offset out of range")?;
                let length = tail.iter().position(|byte| *byte == b'\n' || *byte == 0)
                    .ok_or("unterminated GNU archive member name")?;
                std::str::from_utf8(&tail[..length])?.trim_end_matches('/')
            }
            _ => name.trim_end_matches('/'),
        };
        count += 1;
        let member_label = format!("{label}[{count}:{member}]");
        let counts = decode_module(payload).map_err(|error| format!("{member_label}: {error}"))?;
        counts.show(&format!("MEMBER {member_label}"));
        total.add(&counts);
    }
    if offset != bytes.len() {
        return Err(format!("{label}: missing archive alignment byte at end").into());
    }
    total.show(&format!("ARCHIVE {label} members={count}"));
    Ok(())
}

fn main() -> Result<()> {
    for input in std::env::args().skip(1) {
        let bytes = std::fs::read(&input)?;
        if bytes.starts_with(b"!<arch>\n") {
            decode_archive(&input, &bytes)?;
        } else {
            let counts = decode_module(&bytes).map_err(|error| format!("{input}: {error}"))?;
            counts.show(&format!("MODULE {input}"));
            if input.ends_with(".wasm") || input.starts_with("/work/thread-stack-output") {
                counts.samples();
            }
        }
    }
    Ok(())
}
