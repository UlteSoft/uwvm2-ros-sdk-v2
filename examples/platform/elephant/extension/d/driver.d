/** @brief Verify the read-only result of a denied platform driver connection. */
module application;
import wros_scene : wros_capability_close, wros_capability_open, wros_driver_connect;
extern(C) uint wros_main() nothrow @nogc {
    immutable aliasName = "arm";
    ulong handle, reply = 0x4321, written = 0x1234;
    if (wros_capability_open(0, cast(ulong)aliasName.ptr, aliasName.length, cast(ulong)&handle) != 0) return 1;
    const status = wros_driver_connect(handle, 0, 0, 0, cast(ulong)&reply, 8, cast(ulong)&written);
    return status == 13 && reply == 0x4321 && written == 0x1234 && wros_capability_close(handle) == 0 ? 0 : 1;
}
