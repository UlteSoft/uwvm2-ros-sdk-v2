package wros.scene;

import org.teavm.interop.Address;
import org.teavm.interop.Import;

/** Synchronous client of a single deployment-provisioned driver capability. */
public final class Driver {
    @Import(name="wr_capability_open") private static native int openRaw(int m,long name,long size,long token);
    @Import(name="wr_capability_close") private static native int closeRaw(long token);
    @Import(name="wr_driver_connect") private static native int connectRaw(long t,int m,long i,long n,long o,long c,long w);
    @Import(name="wr_driver_submit") private static native int submitRaw(long t,int m,long i,long n,long o,long c,long w);
    @Import(name="wr_driver_result") private static native int resultRaw(long t,int m,long i,long n,long o,long c,long w);
    @Import(name="wr_driver_describe") private static native int describeRaw(long t,int m,long i,long n,long o,long c,long w);
    @Import(name="wr_driver_disconnect") private static native int disconnectRaw(long t,int m,long i,long n,long o,long c,long w);
    @Import(name="wros_jvm_clear") private static native void clear(long address,int bytes);

    private static final int MAX_PAYLOAD = 65536;
    private long token;
    private byte[] request, reply;
    private final byte[] control = new byte[32], written = new byte[8];

    private static long address(byte[] bytes) {
        return ((long) Address.ofData(bytes).toInt()) & 0xffff_ffffL;
    }

    private static long word(byte[] bytes, int offset) {
        long result = 0;
        for (int i=0; i<8; i++) result |= ((long) bytes[offset+i] & 255L) << (8*i);
        return result;
    }

    private static void word(byte[] bytes, int offset, long value) {
        for (int i=0; i<8; i++) bytes[offset+i] = (byte) (value >>> (8*i));
    }

    /** Open the configured alias and preallocate staging bytes within the per-message limits. */
    public int open(byte[] alias, int requestLimit, int responseLimit) {
        if (token != 0) return 16;
        if (alias == null || alias.length == 0 || alias.length > MAX_PAYLOAD ||
            requestLimit < 0 || requestLimit > MAX_PAYLOAD || responseLimit < 0 || responseLimit > MAX_PAYLOAD) return 22;
        byte[] pendingRequest = new byte[24+requestLimit], pendingReply = new byte[16+responseLimit];
        int status = openRaw(0, address(alias), alias.length, address(control));
        if (status == 0) {
            token = word(control, 0);
            if (token == 0) status = 74;
            else { request = pendingRequest; reply = pendingReply; }
        }
        clear(address(control), 8);
        return status;
    }

    private int checkWord(int status, long expected) {
        if (status == 0 && (word(written,0) != 8 || word(control,0) != expected)) status = 74;
        clear(address(control), 8);
        clear(address(written), 8);
        return status;
    }

    public int connect() {
        if (token == 0) return 9;
        return checkWord(connectRaw(token,0,0,0,address(control),8,address(written)), 1);
    }

    /** Submit one canonical driver-schema payload with its sequence and monotonic deadline. */
    public int submit(long sequence, long deadline, byte[] payload) {
        if (token == 0) return 9;
        if (sequence == 0 || deadline == 0 || payload == null || payload.length > request.length-24) return 22;
        word(request,0,sequence);
        word(request,8,deadline);
        word(request,16,payload.length);
        for (int i=0; i<payload.length; i++) request[24+i] = payload[i];
        int size = 24+payload.length;
        int status = submitRaw(token,0,address(request),size,address(control),8,address(written));
        clear(address(request),size);
        return checkWord(status,sequence);
    }

    /** Receive a result. outcome[0] is the driver's status and outcome[1] is the payload byte count. */
    public int result(long sequence, byte[] payload, long[] outcome) {
        if (token == 0) return 9;
        if (sequence == 0 || payload == null || payload.length < reply.length-16 ||
            outcome == null || outcome.length != 2) return 22;
        word(control,0,sequence);
        int status = resultRaw(token,0,address(control),8,address(reply),reply.length,address(written));
        if (status == 0) {
            long size = word(written,0), body = word(reply,8);
            if (size < 16 || size > reply.length || body != size-16) status = 74;
            else {
                for (int i=0; i<(int)body; i++) payload[i] = reply[16+i];
                outcome[0] = word(reply,0);
                outcome[1] = body;
            }
        }
        clear(address(control),8);
        clear(address(written),8);
        clear(address(reply),reply.length);
        return status;
    }

    /** Copy phase, sequence, status and the unknown-effect bit on success. */
    public int describe(long[] state) {
        if (token == 0) return 9;
        if (state == null || state.length != 4) return 22;
        int status = describeRaw(token,0,0,0,address(control),32,address(written));
        if (status == 0) {
            long unknown=word(control,24);
            if (word(written,0) != 32 || (unknown != 0 && unknown != 1)) status = 74;
            else for (int i=0;i<4;i++) state[i] = word(control,8*i);
        }
        clear(address(control),32);
        clear(address(written),8);
        return status;
    }

    public int disconnect() {
        if (token == 0) return 9;
        return checkWord(disconnectRaw(token,0,0,0,address(control),8,address(written)), 1);
    }

    /** Release the local capability after disconnecting; the deployment owns the driver process. */
    public int close() {
        if (token == 0) return 9;
        int status = closeRaw(token);
        if (status == 0) { token = 0; request = null; reply = null; }
        return status;
    }
}
