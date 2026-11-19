"""Native GoogleTest oracle and Wasm predicate trace for the original Jazzy tf2 suite."""
from pathlib import Path
from xml.etree import ElementTree

from upstream_cpp import TEST, SUPPORT, build_gtest, case_run, sha

UNIT = "test/simple_tf2_core.cpp"
UNIT_DIGEST = "29e167036bbcc116a5ff166be0173b9610514280bd587adf43480e19195d5c92"
NO_ASSERTIONS = {"tf2_time.Display_Time_Point"}


def cases(fixture):
    if sha(fixture) != UNIT_DIGEST:
        raise ValueError("unrecognized Jazzy tf2 upstream suite")
    result = TEST.findall(fixture.read_text())
    if len(set(result)) != 17 or len(result) != 17:
        raise ValueError("expected seventeen original test bodies")
    return result


def native(options, index, fixture, flags, objects, check):
    options.native_cxx = Path("/usr/bin/g++")
    gtest = build_gtest(options, index)
    folder = options.output
    common = [options.native_cxx, "-std=c++20", "-O3", "-g", "-pthread", *flags]
    suite = cases(fixture)
    names = [s + "." + n for s, n in suite]
    check("original-tests-build", [*common, "-I", gtest / "include", fixture, *objects, gtest / "gtest.o",
                                   "-o", folder / "native-tests"])
    check("original-tests-run", [folder / "native-tests", "--gtest_output=xml:original-tests.xml"])
    rows = ElementTree.parse(folder / "original-tests.xml").findall(".//testcase")
    if (sorted(c.get("classname") + "." + c.get("name") for c in rows) != sorted(names)
            or any(c.get("status") != "run" or c.find("failure") is not None for c in rows)):
        raise ValueError("native GoogleTest did not pass every Jazzy body")
    trace = case_run(folder, str(fixture.relative_to(folder)), suite)
    check("trace-build", [*common, "-I", SUPPORT, trace, *objects, "-o", folder / "native-trace"])
    check("trace-run", [folder / "native-trace"])
    expected = {}
    for line in (folder / "trace-run.log").read_text().splitlines():
        name, count, checksum = line.split()
        expected[name] = [int(count), int(checksum)]
    if list(expected) != names or {n for n,(count,_) in expected.items() if count == 0} != NO_ASSERTIONS:
        raise ValueError("native assertion organization changed")
    return dict(googletestXmlSha256=sha(folder / "original-tests.xml"),
                googletestSourcesSha256=sha(gtest / "pins.json"), cases=expected)


def guest(folder, fixture, oracle, changed):
    suite = cases(fixture)
    expected = {name: pair.copy() for name, pair in oracle["upstreamTests"]["cases"].items()}
    if list(expected) != [s + "." + n for s, n in suite] or any(
        len(pair) != 2 or not all(type(x) is int and 0 <= x < 2 ** 64 for x in pair) for pair in expected.values()
    ):
        raise ValueError("bad native predicate trace")
    if changed:
        expected["tf2.setTransformValidWithCallback"][0] += 1
    generated = case_run(folder, str(fixture.relative_to(folder)), suite, expected)
    stub = "void _start(){wros_run_all();}"
    text = generated.read_text()
    if text.count(stub) != 1:
        raise ValueError("missing guest test entry point")
    # The original time tests call get_now(). Detect denied/zero clocks first.
    text = text.replace(stub, "void _start(){if(tf2::get_now().time_since_epoch() <= "
                        "std::chrono::hours(1)) __builtin_trap(); wros_run_all();}")
    path = folder / ("changed-tests.cpp" if changed else "original-tests.cpp")
    path.write_text(text)
    return path
