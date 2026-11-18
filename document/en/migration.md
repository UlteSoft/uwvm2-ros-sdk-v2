# Migrating packaged ROS resources

A C or C++ guest can read a fixed selection of ROS package files with no WASI file, network or environment imports. Select the usual language and platform with `--component migration`. The resulting installation includes the compiler, Xmake adapter, host-side Python tools and `include/wros/package_resources.h`. Put its path in `UWVM_ROS_SDK_ROOT`.

For example, to keep an existing robot description and its lookup name, run these commands from your project. Set `ROBOT_DESCRIPTION` to the source directory containing the package manifest. The packer runs on a POSIX build host.

```sh
python3 "$UWVM_ROS_SDK_ROOT/tools/migration/package_manifest.py" "$ROBOT_DESCRIPTION/package.xml"
python3 "$UWVM_ROS_SDK_ROOT/tools/migration/package_resources.py" lock \
  --package-root "$ROBOT_DESCRIPTION" --uri package://my_robot/urdf/body.urdf --output resources.lock
python3 "$UWVM_ROS_SDK_ROOT/tools/migration/package_resources.py" pack \
  --package-root "$ROBOT_DESCRIPTION" --lock resources.lock --output resources.bin
```

Review the selected URIs and hashes in the lock. Multiple packages and URIs can be selected explicitly. A changed resource or manifest requires a new lock. Symbolic links and duplicate package names are refused. Each lookup uses its exact, case-sensitive URI. Use canonical percent encoding for spaces and non-ASCII characters. The pack is limited to 64 MiB and 65,535 entries. Every guest receiving it can read every entry. Keep secrets and writable deployment state outside these packs.

Place the pack beside the following C23 source and add the installation's include directory. From C++ or another producer, supply the same immutable byte span to the reader. Keep that span alive until all views have been consumed.

```c
#include <wros/package_resources.h>
static const unsigned char resources[] = {
#embed "resources.bin"
};

int read_description(wros_package_view *result) {
    const char uri[] = "package://my_robot/urdf/body.urdf";
    wros_package_index package;
    return wros_package_open(resources, sizeof resources, &package) &&
           wros_package_find(&package, uri, sizeof uri - 1, result);
}
```

Open an index once and reuse it for many lookups. A present empty file returns success with a zero length. The packer copies files as bytes. Applications which process Xacro or a mesh format separately select and validate any dependent assets. File writes and live device operations require their corresponding VM capabilities.

The manifest inspector retains dependency kinds, version constraints and unevaluated conditions. Its output identifies the source version to port. A complete migration also needs the package's build, imported interfaces, upstream tests, and deployment behavior to be checked for each supported target.

### Checking a source collection

From the SDK source tree, run `tools/migration/audit_ros_packages.py --corpus CORPUS --output OUT` against the acquired ROS distribution snapshots. The output distinguishes ROS manifest identities, other recognized XML documents, unavailable sources and invalid declarations. Conditions on dependencies remain attached to their distribution variant. For names missing from that table, `tools/migration/recover_release_manifests.py --corpus CORPUS --table OUT/packages.tsv --output RELEASES` looks up exact Bloom release tags and verifies the package name in the manifest at the resolved commit. This optional host tool needs Git and PyYAML. Recovered manifests establish identity only.

The SDK test `tests/migration/package_resource_corpus.py` checks each selected original file in a native executable and in both VM engines for wasm32 and wasm64. It preserves source variants and records the files selected from each package. A resource check alone cannot qualify a package's executable, middleware, drivers or transitive dependencies.

Use `tests/migration/resource_urdf_mujoco.py` with the resulting `variants.jsonl.gz` to replay supported URDF models with an installed MuJoCo SDK. Models can include STL meshes from the same package. The runner resolves every mesh URI relative to that snapshot, pins its digest and gives distinct geometry a distinct filename inside the simulator's virtual filesystem. Joint limits, inertias, link poses and geometry bytes are preserved. The report records simulator rejections and dependencies requiring a different fixture. Fixed-link models have zero dynamic degrees of freedom.

Review existing ROSv1 observer/source authority before issuing ROSv2 permission recommendations. The reviewer ships in this migration installation. [Review legacy observer permissions](legacy-permissions.md)
