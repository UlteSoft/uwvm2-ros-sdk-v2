// Package u2rosv2 declares the host imports registered in the uwvm_ros_v2
// module. Link a normal Go package and call the functions it needs. The
// compiler and linker select the reachable imports.
//
// Memory operands use the exact integer widths of the VM registration.
// Preserve all address bits, including the WasmMTE tag, when converting a
// guest address to uint64. Keep storage alive at a stable address until the
// synchronous call returns. With standard Go, use globals or runtime.Pinner
// for memory referenced only through integer operands. Keep request, reply
// and returned-length storage disjoint where required by the operation.
//
// ABI returns the major number or a scene status. Other operations return
// scene status codes. Each declaration documents its grant, wire format,
// argument lifetimes and output rules.
package u2rosv2
