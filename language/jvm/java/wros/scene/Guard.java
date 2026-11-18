package wros.scene;

import org.teavm.interop.Address;
import org.teavm.interop.Import;

/** A scoped, synchronous ROS guard. Every operation returns the VM status unchanged. */
public final class Guard {
    @Import(name="wr_capability_open") private static native int openRaw(int memory, long name, long size, long token);
    @Import(name="wr_capability_close") private static native int closeRaw(long token);
    @Import(name="wr_guard_create") private static native int createRaw(long token, int memory, long request, long size,
                                                                        long response, long capacity, long written);
    @Import(name="wr_guard_trigger") private static native int triggerRaw(long token, int memory, long request, long size,
                                                                          long response, long capacity, long written);
    @Import(name="wr_guard_take") private static native int takeRaw(long token, int memory, long request, long size,
                                                                    long response, long capacity, long written);

    private long token;
    private long resource;

    private static long pointer(byte[] bytes) {
        return ((long)Address.ofData(bytes).toInt()) & 0xffff_ffffL;
    }
    private static long getWord(byte[] bytes) {
        long result = 0;
        for (int n=0; n<8; ++n) result |= ((long)bytes[n] & 255L) << (8*n);
        return result;
    }
    private static void putWord(long value, byte[] bytes) {
        for (int n=0; n<8; ++n) bytes[n] = (byte)(value >>> (8*n));
    }
    public int open(byte[] name) {
        if (token != 0) return 16;
        byte[] out = new byte[8];
        int status = openRaw(0, pointer(name), name.length, pointer(out));
        if (status == 0) token = getWord(out);
        putWord(0, out);
        return status;
    }
    public int create() {
        byte[] out = new byte[8], written = new byte[8];
        int status = createRaw(token, 0, 0, 0, pointer(out), 8, pointer(written));
        if (status == 0) {
            if (getWord(written) != 8 || getWord(out) == 0) status = 74;
            else resource = getWord(out);
        }
        putWord(0, out);
        return status;
    }
    public int trigger() {
        byte[] in = new byte[8], written = new byte[8];
        putWord(resource, in);
        int status = triggerRaw(token, 0, pointer(in), 8, 0, 0, pointer(written));
        putWord(0, in);
        return status;
    }
    public int take(long[] count) {
        if (count == null || count.length != 1) return 22;
        byte[] in = new byte[8], out = new byte[8], written = new byte[8];
        putWord(resource, in);
        int status = takeRaw(token, 0, pointer(in), 8, pointer(out), 8, pointer(written));
        if (status == 0) {
            if (getWord(written) != 8) status = 74;
            else count[0] = getWord(out);
        }
        putWord(0, in); putWord(0, out);
        return status;
    }
    public int close() {
        int status = closeRaw(token);
        if (status == 0) { token=0; resource=0; }
        return status;
    }
}
