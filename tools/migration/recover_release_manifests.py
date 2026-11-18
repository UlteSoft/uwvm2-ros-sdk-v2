"""Resolve missing ROS identities against the exact package tags in a rosdistro snapshot.

Only public GitHub release repositories are supported. The output contains original manifest
bytes and distribution/version/commit provenance. It does not install or execute upstream code.
"""
import argparse
import collections
import concurrent.futures
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen
from urllib.error import URLError

import yaml

from package_manifest import MAX_MANIFEST, describe


def release_targets(corpus, missing):
    found = collections.defaultdict(list)
    for file in sorted((corpus / "metadata").glob("*-0.yaml")):
        distro = file.name.split("-")[0]
        repositories = yaml.load(file.read_bytes(), Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))["repositories"]
        for repo, item in repositories.items():
            release = item.get("release", {})
            version = release.get("version")
            pattern = release.get("tags", {}).get("release")
            if not version or not pattern:
                continue
            for name in release.get("packages", [repo]):
                if name in missing:
                    upstream = re.sub(r"-[0-9]+$", "", version)
                    pattern_for_version = pattern.replace("{upstream_version}", upstream)
                    tag = pattern_for_version.replace("{package}", name).replace("{version}", version).replace("{rosdistro}", distro)
                    found[release["url"]].append(dict(package=name, distro=distro, version=version, tag=tag))
    return found


def fetch_repo(url, items):
    match = re.fullmatch(r"https://github\.com/([\w.-]+/[\w.-]+?)(?:\.git)?", url, flags=re.ASCII)
    rows = [dict(item, repository=url, state="unresolved") for item in items]
    if not match:
        for row in rows:
            row["reason"] = "unhandled release repository URL"
        return rows, {}
    refs = set()
    for row in rows:
        ref = "refs/tags/" + row["tag"]
        if re.fullmatch(r"refs/tags/[A-Za-z0-9+_./-]+", ref):
            refs.add(ref)
        else:
            row["reason"] = "unrecognized release tag pattern"
    if not refs:
        return rows, {}
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    cmd = ["git", "-c", "credential.helper=", "ls-remote", "--tags", url,
           *sorted(refs | {ref + "^{}" for ref in refs})]
    objects = {}
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=40, env=env, check=True)
        tags = dict(reversed(line.decode("ascii").split("\t")) for line in result.stdout.splitlines())
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        for row in rows:
            row["reason"] = type(exc).__name__ + ": unable to resolve release refs"
        return rows, objects
    cache = {}
    for row in rows:
        if "reason" in row:
            continue
        ref = "refs/tags/" + row["tag"]
        commit = tags.get(ref + "^{}", tags.get(ref, ""))
        if not re.fullmatch("[0-9a-f]{40}", commit):
            row["reason"] = "missing immutable release ref"
            continue
        raw_url = "https://raw.githubusercontent.com/" + match[1] + "/" + commit + "/package.xml"
        row.update(commit=commit, url=raw_url)
        try:
            if commit not in cache:
                with urlopen(Request(raw_url, headers={"User-Agent": "wros-source-audit"}), timeout=12) as stream:
                    data = stream.read(MAX_MANIFEST + 1)
                cache[commit] = data
            raw = cache[commit]
            info = describe(raw, "package.xml")
            if info["name"] != row["package"]:
                raise ValueError("manifest identifies a different package: " + info["name"])
            row.update(state="release-manifest-read", sha256=info["sha256"], manifest_version=info["version"])
            objects[info["sha256"]] = raw
        except (OSError, ValueError, URLError) as exc:
            row["reason"] = str(exc)
    return rows, objects


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("corpus", "table", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    objects = args.output / "objects"
    objects.mkdir()
    with args.table.open() as file:
        missing = {row["package"] for row in csv.DictReader(file, delimiter="\t") if row["manifest_status"] == "source-missing"}
    targets = release_targets(args.corpus, missing)
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = [pool.submit(fetch_repo, url, items) for url, items in sorted(targets.items())]
        for result in concurrent.futures.as_completed(results):
            batch, content = result.result()
            rows.extend(batch)
            for sha, data in content.items():
                (objects / (sha + ".xml")).write_bytes(data)
    names = {r["package"] for r in rows if r["state"] == "release-manifest-read"}
    result = dict(distribution_revision=json.loads((args.corpus / "reconciliation/summary.json").read_bytes())["rosdistro_revision"],
                  initial_missing=len(missing), release_candidates=len({r["package"] for r in rows}),
                  manifest_names_recovered=len(names), unresolved_names=sorted(missing - names),
                  scope="Package identity recovered from the immutable Bloom release manifest only.",
                  releases=sorted(rows, key=lambda r: (r["package"], r["distro"], r["tag"])))
    (args.output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print("missing:", len(missing), "recovered:", len(names), "release records:", len(rows))


if __name__ == "__main__":
    main()
