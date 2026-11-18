"""Re-read the acquired ROS source manifests and retain evidence per package and variant."""
import argparse
import collections
import contextlib
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re

from package_manifest import MAX_MANIFEST, NonPackageDocument, describe


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_manifest(corpus, source_id, relative):
    if not re.fullmatch(r"[0-9a-f]{24}", source_id):
        raise ValueError("invalid source ID")
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts or path.name not in ("package.xml", "manifest.xml"):
        raise ValueError("invalid manifest path")
    for store in ("recovery", "supplemental", ""):
        root = corpus / store / "sources" / source_id
        candidate = root / path
        if candidate.is_file():
            if root.is_symlink() or not candidate.resolve().is_relative_to(root):
                raise ValueError("manifest outside source snapshot")
            return candidate
    raise FileNotFoundError(relative)


@contextlib.contextmanager
def json_lines(path):
    with path.open("wb") as target, gzip.GzipFile(filename="", mode="wb", fileobj=target, mtime=0) as data:
        with io.TextIOWrapper(data, encoding="utf-8", newline="\n") as text:
            yield text


def inspect_corpus(corpus, directory):
    corpus = corpus.resolve(strict=True)
    census = corpus / "reconciliation/packages.json"
    catalog = corpus / "reconciliation/package-effect-inventory.json"
    entries = json.loads(census.read_bytes())
    variants = json.loads(catalog.read_bytes())
    buckets = collections.defaultdict(lambda: dict(aliases=set(), sources=set(), kinds=set(), evidence=collections.Counter()))
    empty_labels = []
    for item in entries:
        name = item["name"].strip()
        if name:
            buckets[name]["aliases"].add(item["name"])
        else:
            empty_labels.append(item)
    observations = collections.Counter()
    directory.mkdir(parents=True, exist_ok=False)
    with json_lines(directory / "manifests.jsonl.gz") as records:
        for item in variants:
            rawname = item["package"]
            name = rawname.strip()
            if not name:
                raise ValueError("a source manifest was indexed with an empty identity")
            bucket = buckets[name]
            bucket["aliases"].add(rawname)
            source = item["source_id"]
            bucket["sources"].add(source)
            row = {key: item[key] for key in ("source_id", "source_url", "source_ref", "archive_sha256", "manifest")}
            row["package"] = name
            try:
                path = source_manifest(corpus, source, item["manifest"])
                with path.open("rb") as stream:
                    raw = stream.read(MAX_MANIFEST + 1)
                row["manifest_sha256"] = hashlib.sha256(raw).hexdigest() if len(raw) <= MAX_MANIFEST else None
                relative = PurePosixPath(item["manifest"])
                folder_name = relative.parent.name if len(relative.parts) > 2 else None
                manifest = describe(raw, path.name, folder_name)
                if manifest["name"] != name:
                    raise ValueError("source name differs from inventory: " + manifest["name"])
                row["manifest_info"] = manifest
                row["state"] = "manifest-read"
                bucket["kinds"].add(manifest["format"])
                if any(e["tag"] == "metapackage" for e in manifest["exports"]):
                    observations["metapackage_declarations"] += 1
                if any("condition" in e["attributes"] for e in manifest["dependencies"]):
                    observations["manifests_with_conditional_dependencies"] += 1
            except NonPackageDocument as err:
                row.update(state="non-package-document", reason=str(err))
            except (OSError, ValueError) as err:
                row.update(state="source-review-required", reason=str(err))
            bucket["evidence"][row["state"]] += 1
            observations[row["state"]] += 1
            records.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
    with (directory / "packages.tsv").open("w", newline="") as table:
        writer = csv.writer(table, delimiter="\t", lineterminator="\n")
        writer.writerow(("package", "source_snapshots", "manifests_read", "manifests_needing_review", "non_package_documents",
                         "manifest_formats", "manifest_status", "whole_package_runtime"))
        for name, item in sorted(buckets.items()):
            counts = item["evidence"]
            state = ("source-missing" if not item["sources"] else
                     "review-required" if counts["source-review-required"] else
                     "manifest-read" if counts["manifest-read"] else "only-non-package-documents")
            writer.writerow((name, len(item["sources"]), counts["manifest-read"], counts["source-review-required"],
                             counts["non-package-document"],
                             ",".join(sorted(item["kinds"])), state, "not-qualified-by-manifest"))
    aliases = {n: sorted(v["aliases"]) for n,v in sorted(buckets.items()) if v["aliases"] != {n}}
    (directory / "names.json").write_text(json.dumps(dict(aliases=aliases, empty_entries=empty_labels), indent=2))
    summary = dict(complete=True, raw_index_entries=len(entries), canonical_names=len(buckets),
                   names_with_source=sum(bool(v["sources"]) for v in buckets.values()),
                   names_with_read_manifest=sum(bool(v["evidence"]["manifest-read"]) for v in buckets.values()),
                   names_without_source=sum(not v["sources"] for v in buckets.values()),
                   source_manifest_instances=len(variants), observations=dict(observations), excluded_packages=[],
                   source_inventory_sha256=digest(catalog), name_inventory_sha256=digest(census),
                   evidence={p.name:digest(p) for p in directory.iterdir() if p.is_file()},
                   scope="ROS source manifest inspection. Dependencies retain their original conditions. "
                         "Package builds, guest execution and physical device qualification require separate evidence.")
    (directory / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--corpus", type=Path, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    print(json.dumps(inspect_corpus(args.corpus, args.output), indent=2))
