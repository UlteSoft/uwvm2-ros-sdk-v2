"""Per-commit selection hook for the permanent bootstrap contract."""
import argparse
import json

def main():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument("platform")
    p.add_argument("language")
    p.add_argument("--revision-help",action="store_true")
    p.add_argument("--component",choices=["development","protocol","compiler-source"],default="development")
    a=p.parse_args()
    if a.revision_help:
        print(json.dumps({"help":p.format_help()}));return
    packages=["platforms/"+a.platform,"metadata/"+a.language,"protocol"]
    if a.component=="development":
        if a.language in ("c","cpp"):packages+=["frontend","languages/"+a.language]
        elif a.language in ("rs","as"):packages+=["languages/"+a.language]
        else:p.error("a development package has not been published for this language")
    elif a.component=="compiler-source":
        if a.language not in ("c","cpp"):p.error("no compiler source package for this language")
        packages+=["frontend","languages/"+a.language,"compiler-source"]
    print(json.dumps({"variant":a.component,"packages":packages}))

if __name__=="__main__":main()
