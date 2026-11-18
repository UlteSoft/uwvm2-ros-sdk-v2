# Local driver and model attachment boundary

An SDK application calls the registered ROSv2 driver or model imports. It does
not open a host socket, select a peer PID, read TLS secrets, switch namespaces,
load a vendor library or create a native driver. Compiling a language binding or
selecting a vendor platform does not grant any of those permissions.

The trusted deployment layer assigns one authenticated channel to each approved
VM/provider session. It delivers a connected local socket, immutable identity
material, exact peer credentials and clock-domain evidence to the VM host. The
Wasm application receives only an explicitly authorized capability. A transport
handshake does not grant an operation; both interface exposure and its specific
resource grant remain necessary. Shared providers must arbitrate across all
clients at the trusted external receiver.

The current VM registration uses TLS 1.3 with pinned Ed25519 raw public keys,
ephemeral X25519 and AES-128-GCM. The host identity descriptor contains the local
seed and exact peer public key, sealed against modification. Private keys never
belong in Wasm memory, application XML, command-line values or installation
manifests. The registry is not a request to expose raw crypto controls to guest
code; future transport profiles must be admitted by deployment policy.

For separate non-root users, the provisioner also supplies a read-only descriptor
of the peer's time namespace. The VM checks its kernel type and requires it to
match the VM's monotonic clock domain. The provisioner must pin each process's
namespace membership before execution. Cgroup resource limits alone do not
provide this property. The VM still authenticates the exact process incarnation,
per-packet credentials and TLS identity. Neither endpoint needs ptrace access to
the other user's process.

Deployment also reserves host identities before starting or recovering workloads.
Managers must share the [host ownership registry](https://github.com/UlteSoft/wasmros-deployer/blob/main/document/en/host-identities.md).
Reusing an identity is not a substitute for a driver capability. This host
coordination is separate from device exclusivity and ROSv2 grants.

The deployment layer now has [exact device ownership and kernel filtering](https://github.com/UlteSoft/wasmros-deployer/blob/main/document/en/device-isolation.md).
Its VM baseline denies physical device opens. Device aliases share the same
type/major/minor ownership key; another manager cannot take over after the
original exits. These controls do not grant SDK platform code a host device FD,
and cannot establish physical identity after hotplug or safe actuator state.
The full native-provider lifecycle still requires integration; an SDK platform
selection does not enable it.

The namespace descriptor is a host registration detail and does not change the
Wasm carrier ABI. Keep all computation that needs no host authority inside Wasm.
Use ROSv2 imports for permitted external effects; do not route driver access
through generic WASIp1 sockets or in-process native preloading.

The current Rust deployer executes reviewed VM workloads, but rejects native
driver declarations at execution. Its full driver provisioning and hardware
ownership lifecycle remain incomplete. Cross-identity attachment tests use a
test provisioner in a disposable Linux kernel. These tests do not establish
universal vendor compatibility or physical safety certification.

The deployer now provides [Rust provisioning primitives](https://github.com/UlteSoft/wasmros-deployer/blob/main/document/en/attachment-provisioning.md)
for fresh reciprocal keys, sealed identity descriptors, exact process/clock
pinning and a fixed external-adapter bootstrap. These objects are consumed by
the host and isolated adapter only. They add no Wasm import, WASIp1 socket grant
or native driver implementation to an SDK platform extension. An original
vendor binary or shared library still needs an admitted external adapter; it
does not automatically implement the WROS encrypted carrier. The current test
receiver is a harmless parameter-query fixture, not a supported vendor driver.
The VM repository also supplies the host-only `provider_bootstrap_receiver.h`
for bounded, authenticated receipt of that handoff. SDK Wasm applications never
receive those native descriptors or the provisioner's credentials.

See the VM's [driver attachment contract](https://github.com/UlteSoft/uwvm2-ros/blob/main/documents/runtime/ros-driver-attachment.md)
and [model attachment contract](https://github.com/UlteSoft/uwvm2-ros/blob/main/documents/runtime/ros-model-attachment.md).
