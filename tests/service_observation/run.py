"""Compile the paired readiness client with a signed SDK and run against actual provisioned ROS 2 peers."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    with Path(path).open("rb") as body:
        return hashlib.file_digest(body, "sha256").hexdigest()

def header(suite, documents):
    constants = []
    clients = []
    for side, document in enumerate(documents):
        definitions = {row["identity"]: row for row in suite.selected(document, side)}
        service = "service-server" if side else "service-client"
        names = ["context", "node", service]
        fields = []
        for index, name in enumerate(names):
            row = definitions[name]
            payload = suite.profile(suite.definition.compile_definition(row)[1])
            if name == service:
                payload += suite.text(row["definition"]["name"]) + suite.text("std_srvs/srv/SetBool") + suite.text(row["definition"]["role"])
            variable = f"record_{side}_{index}"
            constants.append(f"static const unsigned char {variable}[] = {{" + ",".join(map(str, payload)) + "};")
            fields.extend([variable, f"sizeof({variable})"])
        aliases = [suite.alias(side, name) for name in names + ["set-bool-request", "set-bool-response"]]
        clients.append("{" + ", ".join([*fields, *map(json.dumps, aliases)]) + "}")
    shape = """static const struct {
        const unsigned char *context; size_t context_bytes;
        const unsigned char *node; size_t node_bytes;
        const unsigned char *service; size_t service_bytes;
        const char *context_alias, *node_alias, *service_alias, *request_alias, *response_alias;
    } profiles[2] = {"""
    return "\n".join([*constants, shape, ",\n".join(clients), "};", ""])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("sdk", "vm", "vm-source", "pair-receipt", "gateway", "toolchain", "sysroots", "output"):
        parser.add_argument("--" + key, type=lambda s: Path(s).resolve(), required=True)
    args = parser.parse_args()
    if not args.output.is_relative_to(ROOT / ".tmp"):
        parser.error("choose a fresh directory under this SDK checkout's .tmp")
    sys.path.insert(0, str(args.vm_source / "test/0084.ros-runtime"))
    import run_scene_communication as suite
    suite.verify_gate()
    if not os.sched_getaffinity(0).issubset({4, 5, 6, 7}):
        parser.error("run with the qualification CPU affinity")
    sys.path.insert(0, str(args.sdk / "install"))
    from guest_profile import Profile
    args.output.mkdir(parents=True)
    evidence = json.loads(args.pair_receipt.read_bytes())
    assert evidence["complete"]
    packs, documents = [], []
    inputs = {str(x): digest(x) for x in [args.vm, args.gateway, args.pair_receipt, args.sdk / "bin/wrc",
                                           args.sdk / "share/abi/ros.json", Path(__file__).with_name("client.c")]}
    for i in range(2):
        manifest = args.pair_receipt.parent / f"pack-{i}/manifest.json"
        assert evidence["pack_sha256"][str(manifest)] == digest(manifest)
        pack = json.loads(manifest.read_bytes())
        document_file = args.pair_receipt.parent / f"peer-{i}.json"
        document = json.loads(document_file.read_bytes())
        inputs[str(manifest)] = digest(manifest)
        inputs[str(document_file)] = digest(document_file)
        for image in [pack["launcher"], *pack["files"]]:
            assert digest(image["path"]) == image["sha256"]
        encoded, _ = suite.worker_definition.compile_definition(document)
        startup = next(x for x in pack["files"] if x["destination"] == "/worker/profile")
        assert encoded == Path(startup["path"]).read_bytes()
        packs.append(pack)
        documents.append(document)
    sdk_abi = json.loads((args.sdk / "share/abi/ros.json").read_bytes())
    assert sdk_abi == json.loads((ROOT / "share/abi/ros.json").read_bytes())
    report = {"complete": False, "inputs": inputs, "cases": []}
    result = args.output / "results.json"
    def save():
        result.write_text(json.dumps(report, indent=2) + "\n")
    def record(name, completed):
        for key in ("stdout", "stderr"):
            (args.output / (name + "." + key)).write_text(getattr(completed, key))
        report["cases"].append({"name": name, "argv": list(map(str, completed.args)), "exit": completed.returncode})
        save()
        completed.check_returncode()
    (args.output / "worker_profiles.h").write_text(header(suite, documents))
    source = args.output / "client.c"
    shutil.copyfile(Path(__file__).with_name("client.c"), source)
    wasm = args.output / "client.wasm"
    compile_args = [args.sdk / "bin/wrc", "--target", "wasm32", "--toolchain", args.toolchain, "--sysroots", args.sysroots,
                    "-O3", "-g", "--build-receipt", "--reactor", "--export", "_start", source, "-o", wasm]
    record("signed-sdk-compile", subprocess.run(compile_args, cwd=args.output, capture_output=True, text=True, timeout=180))
    report["wasm_sha256"] = digest(wasm)
    build = Path(str(wasm) + ".wros-build.json")
    report["guest_build_receipt_sha256"] = digest(build)
    record("verify-sdk-artifact", subprocess.run(
        [sys.executable, args.sdk / "install/qualification.py", "--artifact", wasm, "--receipt", build,
         "--vm", args.vm, "--approved-receipt-sha256", report["guest_build_receipt_sha256"]],
        cwd=args.output, capture_output=True, text=True, timeout=120))
    controls = Profile(32, exceptions="eh").uwvm_feature_flags()
    flags = suite.configured(packs, documents)
    for engine in ("int", "aot"):
        argv = [str(args.vm), "--wasm-set-main-module-name", "main", "--runtime-compile-threads", "0",
                "--runtime-llvm-jit-cache-path", "disable", "--log-color", "disable", "--runtime-" + engine,
                *controls, *flags, "--run", str(wasm)]
        record(engine, suite.deployment_fixture.execute(argv, packs, args.gateway))
    report["complete"] = True
    save()

if __name__ == "__main__":
    main()
