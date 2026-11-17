"""Resolve one language and platform at the selected SDK commit."""
import argparse
import json


BINDINGS = {"c": "c", "cpp": "c", "rs": "rs", "as": "as"}


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

    packages = ["platforms/" + args.platform, "metadata/" + args.language]
    if args.component == "bindings":
        binding = BINDINGS.get(args.language)
        if binding is None:
            parser.error("no raw bindings are published for this language")
        packages.extend(("license", "bindings/" + binding))
    else:
        packages.append("protocol")
        if args.component == "compiler-source":
            if args.language not in ("c", "cpp"):
                parser.error("no compiler source package for this language")
            packages.extend(("frontend", "languages/" + args.language, "compiler-source"))
        elif args.component == "development":
            if args.language in ("c", "cpp"):
                packages.append("frontend")
            elif args.language not in BINDINGS:
                parser.error("a development package has not been published for this language")
            packages.append("languages/" + args.language)
    print(json.dumps({"variant": args.component, "packages": packages}))


if __name__ == "__main__":
    main()
