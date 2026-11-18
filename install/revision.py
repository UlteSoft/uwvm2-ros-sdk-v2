"""Resolve one language and platform using just this revision's isolated hook."""
import argparse
import json


BINDINGS = {"c": "c", "cpp": "c", "rs": "rs", "as": "as"}
DEVELOPMENT = ("c", "cpp", "fortran", "lua", "rs", "tinygo")

# BEGIN generated target inventory (tools/package_index.py)
LANGUAGES = "as c c_ffi_bridge cpp csharp d fortran fsharp go haskell java js kotlin lua moonbit nim objectc odin php py r rs ruby swift tinygo typescript vbnet wat zig".split()
PLATFORM_LANGUAGES = {
    platform: routes.split()
    for group, routes in (
        ("abb agibot doosan fanuc flexiv fourier franka hello_robot kinova leju pal robotis trossen ubtech universal_robots yaskawa",
         "as c c_ffi_bridge cpp csharp d fortran fsharp go haskell java js kotlin lua moonbit nim objectc odin php py r rs ruby swift tinygo vbnet zig"),
        ("agilex boston_dynamics clearpath",
         "as c cpp d fortran go haskell moonbit nim odin rs swift tinygo zig"),
        ("booster deep_robotics limx",
         "c c_ffi_bridge cpp fortran js lua objectc py"),
        ("dobot elephant realman ufactory",
         "as c c_ffi_bridge cpp fortran go java js kotlin lua objectc php py rs ruby tinygo"),
        ("kuka",
         "as c c_ffi_bridge cpp csharp d fortran fsharp go haskell java js kotlin lua moonbit nim objectc odin php py r rs ruby swift tinygo typescript vbnet zig"),
        ("nvidia nvidia-groot nvidia-isaac-ros nvidia-isaac-sim",
         "as c c_ffi_bridge cpp fortran go js rs tinygo typescript"),
        ("unitree",
         "as c c_ffi_bridge cpp d fortran go haskell java js kotlin lua moonbit nim objectc odin php py rs ruby swift tinygo typescript zig"),
    )
    for platform in group.split()
}
# END generated target inventory


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("platform")
    parser.add_argument("language")
    parser.add_argument("--revision-help", action="store_true")
    parser.add_argument("--component", choices=("development", "bindings", "protocol", "compiler-source"),
                        default="development")
    args = parser.parse_args()
    if args.revision_help:
        print(json.dumps({"help": parser.format_help()}))
        return

    if args.platform not in PLATFORM_LANGUAGES:
        parser.error("unknown platform: " + args.platform)
    if args.language not in LANGUAGES:
        parser.error("unknown language: " + args.language)
    packages = ["platforms/" + args.platform, "metadata/" + args.language]
    if args.component == "bindings":
        binding = BINDINGS.get(args.language)
        if binding is None:
            parser.error("no raw bindings are published for this language")
        packages.extend(("license", "bindings/" + binding))
    else:
        packages.append("protocol")
        if args.component in ("development", "compiler-source"):
            if args.language not in DEVELOPMENT:
                parser.error("a development package has not been published for this language")
            if args.language not in PLATFORM_LANGUAGES[args.platform]:
                parser.error("this platform has no development route for the requested language")
            packages.extend(("frontend", "xmake/common", "xmake/platforms/" + args.platform, "languages/" + args.language))
            if args.component == "compiler-source":
                packages.append("compiler-source")
    print(json.dumps({"variant": args.component, "packages": packages}))


if __name__ == "__main__":
    main()
