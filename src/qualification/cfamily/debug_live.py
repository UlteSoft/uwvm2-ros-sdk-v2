"""Live language, full snapshot and production signed-update probes for debug_suite.py."""
import hashlib
import re
import socket
import struct
import subprocess
import time
from pathlib import Path


class Limitation(Exception):
    """A capability refusal positively identified on the requested live VM."""


class RestoreRefusal(Exception):
    """The VM declined a full archive and retained its original stopped world."""


def need(condition, message):
    if not condition:
        raise ValueError(message)


def parse_stop(reply):
    stop = re.search(r"^stop-id ([1-9][0-9]*)$", reply, re.M)
    thread = re.search(r"^thread ([1-9][0-9]*) module=(\d+) function=(\d+) byte-offset=(\d+) generation=(\d+)$",
                       reply, re.M)
    if stop and thread:
        return {"stop": int(stop[1]), "thread": int(thread[1]), "module": int(thread[2]),
                "function": int(thread[3]), "offset": int(thread[4]), "generation": int(thread[5])}
    return None


def stopped(vm, timeout, *, reason=None, newer=0):
    deadline = time.monotonic() + timeout
    while True:
        reply = vm.request("status")
        at = parse_stop(reply)
        if at is not None and at["stop"] > newer:
            need(reason is None or reason in reply, reply)
            return at
        need("guest exited:" not in reply and time.monotonic() < deadline, f"expected fresh stop: {reply}")
        time.sleep(.02)


def source_position(vm, at, source):
    bt = vm.request(f"bt {at['thread']}")
    need(f"stop-id {at['stop']}\n" in bt, f"backtrace belongs to another stop: {bt}")
    match = re.search(r"^  source (.+):(\d+):(\d+)$", bt, re.M)
    need(match is not None and Path(match[1]).resolve() == source and "source-position=exact" in bt,
         f"expected an exact statement in {source}: {bt}")
    return {**at, "file": match[1], "line": int(match[2]), "column": int(match[3])}


def variable(vm, at, symbol):
    reply = vm.request(f"print {at['thread']} {at['stop']} {symbol}")
    header = f"source-value stop={at['stop']} name={symbol}\n"
    need(reply.startswith(header) or reply.startswith(f"source-stop {at['stop']}\n"), reply)
    values = re.findall(r"(?:\bvalue=|\b[ui](?:8|16|32|64)=)(-?\d+)\b", reply)
    need("error:" not in reply and "unavailable" not in reply and len(values) == 1,
         f"expected one live scalar for {symbol}: {reply}")
    return int(values[0])


def normal_exit(vm, row, timeout):
    reply = vm.request("continue")
    deadline = time.monotonic() + timeout
    # A management continue can itself observe the terminal state. Otherwise
    # wait on the same admitted VM. A normal exit closes the control socket.
    while reply == "running\n" or reply == "wait timed out; no complete stop established; VM is running\nrunning\n":
        remaining = deadline - time.monotonic()
        need(remaining > 0, "guest did not reach its checked exit before the deadline")
        try:
            reply = vm.request("wait")
        except (BrokenPipeError, ConnectionResetError, AssertionError) as exc:
            # The pinned transport reports recv EOF as this exact assertion.
            # Like the VM's secure_server.finished_guest_reply, only the real
            # child wait can settle a terminal status after an acknowledged resume.
            if isinstance(exc, AssertionError) and str(exc) != "VM closed its management channel":
                raise
            row["process_exit"] = vm.process.wait(timeout=max(0, deadline - time.monotonic()))
            need(row["process_exit"] == 0, f"debugged VM exit {row['process_exit']} after its control channel closed")
            row["exit_observation"] = "child-wait-after-acknowledged-continue"
            return row["process_exit"]
    need(reply == "guest exited: 0\n", f"guest did not resume to its checked exit: {reply}")
    row["exit_observation"] = "debugger-terminal-reply"
    return 0


THREAD_REFUSAL = "error: operation unavailable on the private thread execution driver\n"


def private_thread_entry(reply, target, row):
    if not target.threads or not re.search(r"^threaded-profile ", reply, re.M):
        return None
    # Fresh launches hold the first instruction. A terminal reply also includes
    # the private profile and can be followed by an operation refusal.
    at = parse_stop(reply)
    need(reply.startswith("stopped: first Wasm instruction\n") and at is not None,
         f"expected a private thread at its first Wasm instruction: {reply}")
    row["thread_entry_stop"] = at
    return at


def debug_probe(vm, row, build, target, timeout):
    source = Path(build["source"])
    lines = source.read_text().splitlines()
    first, last = [next(i for i, text in enumerate(lines, 1) if marker in text)
                   for marker in ("SOURCE_BREAK", "SOURCE_STEP")]
    entry = private_thread_entry(vm.request("status"), target, row)
    module = build["module"]
    point = vm.request(f"breaksource {module} {source}:{first}")
    if entry is not None and point == THREAD_REFUSAL:
        raise Limitation("private-thread-source-debug-unavailable")
    bp = re.search(r"\bbreakpoint ([1-9][0-9]*)\b", point)
    need(bp, f"source breakpoint refused: {point}")
    vm.request("continue")
    at = source_position(vm, stopped(vm, timeout, reason="stopped: breakpoint"), source)
    need(at["line"] == first and at["module"] == module and at["function"] == build["source_function_index"],
         f"wrong source breakpoint: {at}")
    row["breakpoint"] = {**at, "expression": "local", "value": variable(vm, at, "local")}
    need(row["breakpoint"]["value"] == 40, f"wrong stopped scalar: {row['breakpoint']}")
    removed = vm.request(f"delete {bp[1]}")
    need(removed == "breakpoint deleted\n", removed)
    row["source_steps"] = []
    for _ in range(12):
        reply = vm.request(f"step source {at['thread']} over")
        need(not reply.startswith("error:"), reply)
        current = source_position(vm, stopped(vm, timeout, reason="selected participant step", newer=at["stop"]), source)
        need((current["module"], current["function"]) == (at["module"], at["function"]), current)
        row["source_steps"].append(current)
        at = current
        if at["line"] == last:
            break
    need(at["line"] == last, f"step never reached {source}:{last}")
    row["after_step_value"] = variable(vm, at, "local")
    need(row["after_step_value"] == 42, "source step did not execute the addition")
    row["guest_exit"] = normal_exit(vm, row, timeout)


def memory_word(vm, module):
    reply = vm.request(f"memory {module} 0 64 4")
    header = f"Wasm memory module={module} index=0 offset=64 bytes=4\n"
    match = re.match(re.escape(header) + r"0x0000000000000040: ((?:[0-9a-f]{2} ){4})", reply)
    need(match is not None, f"expected four bytes from guest memory 0 at offset 64: {reply}")
    return bytes.fromhex(match[1]).hex()


def write_word(vm, at, word, timeout):
    cmd = (f"set wasm memory {at['module']} 0 {at['thread']} 64 bytes {word} if-stop {at['stop']}")
    reply = vm.request(cmd)
    match = re.fullmatch(r"wasm-stop ([1-9][0-9]*)\nWasm mutation v=3 status=available applied=1 reason=none "
                         rf"runtime=[1-9][0-9]* module={at['module']} target=memory index=0 element=64 "
                         r"bytes=4 address-bytes=[48]\n", reply)
    need(match is not None and int(match[1]) > at["stop"], f"guest mutation not acknowledged: {reply}")
    current = stopped(vm, timeout, newer=at["stop"])
    need(current == {**at, "stop": int(match[1])}, f"write moved the paused guest: {current}")
    need(memory_word(vm, current["module"]) == word, "guest read-back differs from the acknowledged write")
    return current


def dump_probe(vm, row, build, target, timeout, folder, snapshot, *, restore_timeout):
    entry = private_thread_entry(vm.request("status"), target, row)
    policy = vm.request("dump policy")
    need(policy == "dump-policy max=full effective=full\n", policy)
    archive = folder / "full.uwsnap"
    module = build["module"]
    breakpoint = None
    if entry is not None:
        probe = folder / "thread-profile.uwsnap"
        reply = vm.request(f"dump wasm full {entry['stop']} {probe}")
        if reply == THREAD_REFUSAL and not probe.exists():
            raise Limitation("private-thread-full-dump-unavailable")
        need(reply.startswith("wasm-dump saved"), reply)
        at = stopped(vm, timeout)
    else:
        # The VM rechecks a pending breakpoint when a memory mutation issues
        # a new stop ID. A permanent point keeps both read-backs parked.
        point = vm.request(f"bw {module} {build['entry_index']} 0")
        breakpoint = re.fullmatch(r"breakpoint ([1-9][0-9]*) registered at executable Wasm expression byte offset\n", point)
        need(breakpoint, point)
        vm.request("continue")
        at = stopped(vm, timeout, reason="stopped: breakpoint")
    need((at["module"], at["function"], at["offset"]) == (module, build["entry_index"], 0), at)
    # These four bytes are below the linked fixture data and stack. Full memory
    # writes retire stop IDs. Each next operation uses the acknowledged ID.
    row["original_word"] = memory_word(vm, module)
    row["captured_word"] = "c84f613a"
    at = write_word(vm, at, row["captured_word"], timeout)
    row["captured_at"] = at.copy()
    need(vm.request(f"dump wasm full {at['stop']} {archive}").startswith("wasm-dump saved"), "full dump refused")
    raw = archive.read_bytes()
    image = snapshot.decode(raw)
    source_bytes = Path(build["generations"][0]["wasm"]).read_bytes()
    need(image.disclosure == "full" and any(r.kind == 3 and r.payload == source_bytes for r in image.records),
         "full archive lacks this exact installed-compiler image")
    states = [record for record in image.records if record.kind == 2]
    need(len(states) == 1, "full archive must describe the captured Wasm state")
    state = states[0]
    row["archive"] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                      "disclosure": image.disclosure, "platform": image.platform,
                      "wasm_state": {"capture": snapshot.CAPTURE[state.capture], "schema": state.schema,
                                     "bytes": len(state.payload)},
                      "record_kinds": [r.kind for r in image.records]}
    row["changed_word"] = "7193b6ee"
    changed = write_word(vm, at, row["changed_word"], timeout)
    row["changed_at"] = changed.copy()
    # Preparing the resumable LLVM image is synchronous and can take longer
    # than an ordinary debugger command. All pending replies share one deadline.
    started = time.monotonic()
    row["restore_timeout_seconds"] = restore_timeout
    deadline = started + restore_timeout
    command = f"dump restore current {changed['stop']} {archive}"
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("snapshot restore deadline exceeded")
            vm.channel.settimeout(remaining)
            reply = vm.request(command)
            if not reply.startswith("snapshot-restore pending "):
                break
            command = "dump restore continue"
    except TimeoutError as exc:
        raise TimeoutError(f"snapshot restore exceeded its {restore_timeout}s deadline") from exc
    finally:
        row["restore_elapsed_seconds"] = round(time.monotonic() - started, 3)
        vm.channel.settimeout(timeout)
    if reply.startswith("error: snapshot-restore rejected ") and "applied=0 retained=1" in reply:
        retained = stopped(vm, timeout)
        need(retained == changed and memory_word(vm, module) == row["changed_word"],
             "declined restore did not retain the changed original world")
        row["restore_refusal"] = reply.strip()
        raise RestoreRefusal("full-restore-declined-with-original-world-retained")
    restored = re.fullmatch(r"snapshot-restored stop=([1-9][0-9]*) epoch=([1-9][0-9]*) source=(ready|unavailable); "
                            r"guest paused; external effects are not rewound\n", reply)
    need(restored is not None, reply)
    need(row["archive"]["wasm_state"]["capture"] == "complete" and state.payload,
         "VM acknowledged restoration from an incomplete Wasm state")
    fresh = stopped(vm, timeout, newer=changed["stop"])
    need(fresh["stop"] == int(restored[1]) and fresh["generation"] == int(restored[2])
         and (fresh["module"], fresh["function"], fresh["offset"]) == (module, build["entry_index"], 0), fresh)
    row["restored_at"] = fresh
    row["restored_word"] = memory_word(vm, module)
    need(row["restored_word"] == row["captured_word"], "restored memory differs from the captured state")
    if breakpoint:
        removed = vm.request(f"delete {breakpoint[1]}")
        need(removed == "breakpoint deleted\n", removed)
    row["guest_exit"] = normal_exit(vm, row, timeout)


def update_probe(args, row, build, command, folder, protocol):
    """Run UUP1 on a dedicated stream to one VM. Keep the signing key in host memory."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    g1, g2 = build["generations"]
    target = Path(g2["wasm"]).read_bytes()
    installed, candidate = bytes.fromhex(g1["sha256"]), bytes.fromhex(g2["sha256"])
    sha = lambda data: hashlib.sha256(data).digest()
    declaration = struct.pack("<Q", build["value_local_index"])
    export = struct.pack("<III", build["value_index"], 0, 4)
    row.update(export="value", export_index=build["value_index"], scope_local_index=build["value_local_index"],
               protocol="UUP1", operations=[], test_key_fingerprint=sha(public).hex())
    if "start_section" in g1:
        row["launch_start_section"] = g1["start_section"]
    base = ["--debug-permissions", "none", "--update-public-key", public.hex(), "--update-contract",
            sha(b"SDK qualification: value() -> i32").hex(), "--update-scope",
            sha(b"SDK qualification: isolated host only").hex(), "--update-call-export", "value"]
    host, guest = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    with host, guest, (folder / "vm.log").open("wb") as log:
        host.settimeout(args.run_timeout)
        guest.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
        argv = [*args.runner, command[0], "--update-control-fd", str(guest.fileno()), *base, *command[1:]]
        proc = subprocess.Popen(argv, pass_fds=(guest.fileno(),), stdin=subprocess.DEVNULL,
                                stdout=log, stderr=subprocess.STDOUT)
        guest.close()
        row["pid"] = proc.pid
        row["argv"] = [arg if arg != public.hex() else "<ephemeral-public-key>" for arg in argv]

        def request(name, op, payload=b"", business=False):
            reply = protocol.call_export(host, payload) if business else protocol.request(host, op, payload)
            row["operations"].append({"operation": name, **reply})
            return reply

        try:
            facts = request("status", 0)
            need(row.get("launch_start_section") is None and "--wasm-preload-library" not in command,
                 "production update manager answered for a module with a start section or a preloaded module")
            need(facts["status"] == 0 and facts["state"] == 8 and not facts["active"] and facts["epoch"] == 0
                 and facts["installed"] == installed.hex(), facts)
            launch = protocol.permit(key, facts, 4, installed, sha(b"qualification launch"))
            base_facts = request("signed-launch", 9, launch)
            need(base_facts["status"] == 0 and base_facts["active"] and base_facts["epoch"] == 1, base_facts)
            before = request("call-before", 5, export, business=True)
            need(before["status"] == 0 and before["active"] and before["epoch"] == 1
                 and before["result"] == struct.pack("<i", 17).hex(), before)
            tx = sha(bytes.fromhex(facts["nonce"]) + candidate)
            prepare = protocol.permit(key, base_facts, 1, candidate, tx, declaration=declaration)
            pending = request("signed-prepare", 1, prepare + struct.pack("<I", 1) + declaration + target)
            need(pending["status"] == 0 and pending["state"] == 3, pending)
            ready = request("ready", 2)
            need(ready["status"] == 0 and ready["state"] == 4 and all(int(ready[k], 16)
                 for k in ("ready", "prepared")) and ready["transaction"] == tx.hex(), ready)
            commit = protocol.permit(key, base_facts, 2, candidate, tx, declaration=declaration,
                                     prepared=bytes.fromhex(ready["prepared"]), ready=bytes.fromhex(ready["ready"]))
            active = request("signed-commit", 3, commit)
            need(active["status"] == 0 and active["active"] and active["epoch"] == active["committed"] == 2
                 and active["installed"] == candidate.hex(), active)
            after = request("call-after", 5, export, business=True)
            need(after["status"] == 0 and after["active"] and after["epoch"] == 2
                 and after["result"] == struct.pack("<i", 29).hex() and after["nonce"] == before["nonce"], after)
            need(request("stop", 6)["status"] == 0, "managed stop refused")
            row["process_exit"] = proc.wait(timeout=args.run_timeout)
            need(row["process_exit"] == 0, "managed VM failed its checked entry or shutdown")
            row["business_values"] = [17, 29]
        finally:
            if proc.poll() is None:
                host.close()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)
            row["process_exit"] = proc.returncode
