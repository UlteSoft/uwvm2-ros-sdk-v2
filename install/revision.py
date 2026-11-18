"""Resolve one language and platform using just this revision's isolated hook."""
import argparse
import json


BINDINGS = {"c": "c", "cpp": "c", "rs": "rs", "as": "as", "nim": "nim"}
DEVELOPMENT = ("c", "cpp", "fortran", "lua", "rs", "tinygo", "nim")

# BEGIN generated target inventory (tools/package_index.py)
LANGUAGES = "as c c_ffi_bridge cpp csharp d fortran fsharp go haskell java js kotlin lua moonbit nim objectc odin php py r rs ruby swift tinygo typescript vbnet wat zig".split()
PLATFORMS = "abb agibot agilex booster boston_dynamics clearpath deep_robotics dobot doosan elephant fanuc flexiv fourier franka hello_robot kinova kuka leju limx nvidia nvidia-groot nvidia-isaac-ros nvidia-isaac-sim pal realman robotis trossen ubtech ufactory unitree universal_robots yaskawa".split()
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

    if args.platform not in PLATFORMS:
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
            packages.extend(("frontend", "xmake/common", "xmake/platforms/" + args.platform, "languages/" + args.language))
            if args.component == "compiler-source":
                packages.append("compiler-source")
                if args.language == "nim":
                    packages.append("nim-producer-source")
    print(json.dumps({"variant": args.component, "packages": packages}))


if __name__ == "__main__":
    main()
