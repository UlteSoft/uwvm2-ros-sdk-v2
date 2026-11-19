"""Resolve one language and platform using just this revision's isolated hook."""
import argparse
import json


PROJECT_LANGUAGES = "c cpp csharp d fortran fsharp go java js kotlin lua nim objectc py rs ruby tinygo typescript vbnet".split()
BINDINGS = {"d": "d", "c": "c", "cpp": "c", "objectc": "c", "rs": "rs", "as": "as", "nim": "nim"}
DEVELOPMENT = ("go", "c", "cpp", "fortran", "js", "lua", "objectc", "rs", "tinygo", "nim", "d", "typescript", "py", "ruby")

# Command spellings are part of the per-commit SDK contract. A command name
# can be reserved before its language has an installable compiler package.
COMPILER_COMMANDS = {
    "as": "wras", "c": "wrc", "cpp": "wrcc", "csharp": "wrcs",
    "d": "wrd", "fortran": "wrf", "fsharp": "wrfs", "go": "wrgo",
    "haskell": "wrhs", "java": "wrjava", "js": "wrjs", "kotlin": "wrkt",
    "lua": "wrlua", "moonbit": "wrmbt", "nim": "wrnim", "objectc": "wrobjc",
    "odin": "wrodin", "php": "wrphp", "py": "wrpy", "r": "wrr", "rs": "wrrs",
    "ruby": "wrrb", "swift": "wrswift", "tinygo": "wrtg", "typescript": "wrts",
    "vbnet": "wrvb", "wat": "wrwat", "zig": "wrzig",
}

# BEGIN generated target inventory (tools/package_index.py)
LANGUAGES = "as c c_ffi_bridge cpp csharp d fortran fsharp go haskell java js kotlin lua moonbit nim objectc odin php py r rs ruby swift tinygo typescript vbnet wat zig".split()
PLATFORMS = "abb agibot agilex booster boston_dynamics clearpath deep_robotics dobot doosan elephant fanuc flexiv fourier franka hello_robot kinova kuka leju limx nvidia nvidia-groot nvidia-isaac-ros nvidia-isaac-sim pal realman robotis trossen ubtech ufactory unitree universal_robots yaskawa".split()
# END generated target inventory


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("platform")
    parser.add_argument("language")
    parser.add_argument("--revision-help", action="store_true")
    parser.add_argument("--component", choices=("development", "bindings", "protocol", "compiler-source", "synchronous-aot", "numeric-aot", "migration", "policy-review"),
                        default="development")
    parser.add_argument("--python-target", choices=("wasm32", "wasm64"), action="append",
                        help="fetch the CPython runtime archive for this pointer width (default wasm32)")
    args = parser.parse_args()
    if args.revision_help:
        help_text = parser.format_help()
        if args.language in COMPILER_COMMANDS:
            help_text += f"\nCompiler command name for {args.language}: {COMPILER_COMMANDS[args.language]}\n"
        print(json.dumps({"help": help_text}))
        return

    if args.platform not in PLATFORMS:
        parser.error("unknown platform: " + args.platform)
    if args.language not in LANGUAGES:
        parser.error("unknown language: " + args.language)
    if args.python_target and len(args.python_target) > 1:
        parser.error("select one --python-target per installation")
    if args.python_target is not None and (
        args.language != "py" or args.component not in ("development", "compiler-source", "migration")
    ):
        parser.error("--python-target requires Python development, compiler-source or migration")
    packages = ["platforms/" + args.platform, "metadata/" + args.language]
    if args.component == "policy-review":
        packages.append("migration/policy")
    elif args.component == "numeric-aot" or (args.component in ("development", "migration") and args.language in ("csharp", "vbnet", "fsharp")):
        if args.language not in ("csharp", "vbnet", "fsharp"):
            parser.error("the numeric-aot component requires csharp, fsharp or vbnet")
        packages.extend(("protocol", "frontend", args.language + "/numeric", "xmake/common", "xmake/platforms/" + args.platform))
        if args.component == "migration" and args.language == "fsharp":
            packages.extend(("migration/examples/fsharp/common", "migration/examples/fsharp/" + args.platform))
    elif args.component == "synchronous-aot" or (args.component in ("development", "migration") and args.language in ("java", "kotlin")):
        if args.language not in ("java", "kotlin"):
            parser.error("the synchronous-aot component requires java or kotlin")
        packages.extend(("protocol", "frontend", "jvm/synchronous", "jvm/" + args.language,
                         "xmake/common", "xmake/platforms/" + args.platform))
    elif args.component == "bindings":
        binding = BINDINGS.get(args.language)
        if binding is None:
            parser.error("no raw bindings are published for this language")
        packages.extend(("license", "bindings/" + binding))
    else:
        packages.append("protocol")
        if args.component in ("development", "compiler-source", "migration"):
            if args.language not in DEVELOPMENT:
                parser.error("a development package has not been published for this language")
            packages.extend(("frontend", "xmake/common", "xmake/platforms/" + args.platform, "languages/" + args.language))
            if args.language == "py":
                packages.append("python-runtime/" + (args.python_target or ["wasm32"])[0])
            if args.component == "migration" and args.language in ("c", "cpp"):
                packages.extend(("migration/resources", "migration/policy"))
                if args.language == "c":
                    packages.extend(("migration/examples/c/common", "migration/examples/c/" + args.platform))
                if args.language == "cpp":
                    packages.append("migration/tf2-buffer")
            if args.component == "compiler-source":
                packages.append("go-producer-source" if args.language == "go" else "compiler-source")
                if args.language == "nim":
                    packages.append("nim-producer-source")
    if args.component == "development" and args.language == "c":
        # The editable migration project prepares its immutable ROS message on the build host.
        packages.extend(("migration/resources", "migration/examples/c/common", "migration/examples/c/" + args.platform))
    if args.language in PROJECT_LANGUAGES and args.component in ("development", "migration", "synchronous-aot", "numeric-aot"):
        packages.append("examples/" + args.platform + "/" + args.language)
    if args.language in ("csharp", "fsharp", "vbnet") and args.component in ("development", "numeric-aot", "migration"):
        packages.append("examples/managed/" + args.platform + "/" + args.language)
    print(json.dumps({"variant": args.component, "packages": packages}))


if __name__ == "__main__":
    main()
