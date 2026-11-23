package u2rosv2;

import org.teavm.interop.Address;
import org.teavm.interop.Import;

/** ABI discovery and capability lifetime for an enrolled WROS guest in memory zero. */
public final class Scene {
    private Scene() {}

    /** Returns ABI major 2 when the deployment exposes abi, or the scene status otherwise. */
    @Import(name = "wros_java_scene_abi")
    public static native int abi();

    @Import(name = "wros_java_cap_open")
    private static native int open(Address alias, int size, Address out);

    /** Opens an exact ASCII capability alias and writes its handle to slot[0] on success. */
    public static int open(byte[] alias, long[] slot) {
        if (alias == null || alias.length == 0 || alias.length > 255 || slot == null || slot.length == 0) return 22;
        return open(Address.ofData(alias), alias.length, Address.ofData(slot));
    }

    /** Retires the handle in this environment. Returns zero on success or a scene status. */
    @Import(name = "wros_java_cap_close")
    public static native int close(long handle);

    @Import(name = "wros_java_clock_read")
    private static native int clockRead(long capability, long clock, Address result);

    /**
     * Reads a deployed clock using an authorized clock.read capability.
     * On success result contains four little-endian 64-bit fields in order:
     * signed time, epoch, started flag and clock kind. The output requires 32 bytes.
     */
    public static int readClock(long capability, long clock, byte[] result) {
        if (result == null || result.length < 32) return 22;
        return clockRead(capability, clock, Address.ofData(result));
    }
}
