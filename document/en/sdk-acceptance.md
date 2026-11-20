# SDK language and platform acceptance

[中文](../zh/sdk-acceptance.md)

Run the matrix from a source checkout with the selected commit available locally. Use the designated 64 GiB zero-swap test cgroup. Compilers and VM tests run serially. The receipt records the exact SDK commit, cgroup, fixture digests, Xmake and VM identity.

~~~sh
$GATE python3 -B tests/sdk_acceptance.py \
  --commit "$SDK_COMMIT" --language wat --language as \
  --platform unitree --platform universal_robots \
  --platform-case migration --vm "$VM" --xmake "$XMAKE" \
  --output .tmp/sdk-acceptance
~~~

Repeat the language and platform options to select a subset. Omitting either option selects every registered value for that dimension. The first selected platform is the common example location unless you set --contract-platform. The second tier executes the extension and migration projects for each selected pair by default. Repeat --platform-case to choose the desired categories. Use --plan to list the requested cases and known prerequisites without starting build or execution jobs.

The optional --inputs file uses the wros-sdk-acceptance-inputs-v1 schema. Site and artifact paths are relative to that file, or absolute. A platform-specific profile overrides the language default. For signed sites, provide the configuration that the SDK installer already verifies. For C#, F# and Visual Basic, provide managed_host from the matching host preparation command and managed_toolchain for the matching Wasm LLVM. Bundled AssemblyScript, standard Go and WAT can run without a site.

A producer that uses explicit local tools may select toolchain and sysroots instead of a site. Give the Wasm LLVM prefix and the matching sysroot manifest. The selected compiler still checks its own profile and admission rules.

~~~json
{
  "schema": "wros-sdk-acceptance-inputs-v1",
  "profiles": {
    "c": {"site": "wasm32-c-site.json"},
    "unitree/c": {"target": "wasm64", "site": "wasm64-c-site.json"}
  },
  "artifacts": {}
}
~~~

To exercise a supplied core Wasm module, add an entry under artifacts keyed by platform/language/case, such as unitree/wat/migration. Supply file and the exact lowercase SHA-256 as sha256. Optional profile fields are address_bits, wasm_version, threads, mte and exceptions. The defaults select wasm32, Core 3.0, a single thread, MTE and no EH. The optional queries array declares read-only test grants and is empty by default. The runner validates the digest and SDK import policy, then boots the exact bytes in both VM engines. This case provides execution evidence for those bytes. Compiler and vendor-driver qualification still require the corresponding source fixtures.

The versioned results.json distinguishes three outcomes.

- executable records both engine results and the Wasm digests.
- blocked records an unavailable prerequisite, failed fixture or rejected artifact.
- not_exercised records an absent example or a plan-only case.

A normal run returns zero only when every requested row is executable. Logs and child fixture receipts remain in the output directory. Temporary installations and objects are removed after each case. The platform extension fixture covers the SDK's authenticated local permission boundary. Official simulation and physical vendor drivers use dedicated acceptance fixtures.
