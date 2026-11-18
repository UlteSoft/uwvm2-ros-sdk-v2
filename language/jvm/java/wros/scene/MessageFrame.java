package wros.scene;

import org.teavm.interop.Address;
import org.teavm.interop.Import;

/** Private scratch for one synchronous invocation, owned exclusively by its Wasm guest. */
final class MessageFrame {
    @Import(name="wros_jvm_clear") private static native void wipe(long address,int bytes);

    final byte[] input;
    final byte[] output;
    final byte[] count = new byte[8];
    long token;

    MessageFrame(int inputCapacity, int outputCapacity) {
        if (inputCapacity < 0 || outputCapacity < 0 || (long)inputCapacity + outputCapacity > 16777216L)
            throw new IllegalArgumentException();
        input = new byte[inputCapacity];
        output = new byte[outputCapacity];
    }

    static long address(byte[] bytes) {
        return ((long) Address.ofData(bytes).toInt()) & 0xffff_ffffL;
    }

    long prepare(byte[] request) {
        if (request.length == 0) return 0;
        for (int i=0; i<request.length; i++) input[i] = request[i];
        return address(input);
    }

    int abandon(int status, int bytes) {
        if (bytes != 0) wipe(address(input),bytes);
        return status;
    }

    private long count() {
        long n=0;
        for (int i=0; i<8; i++) n |= ((long)count[i] & 255L) << (i*8);
        return n;
    }

    int finishOpen(int status, int aliasBytes) {
        wipe(address(input), aliasBytes);
        if (status == 0) {
            token=count();
            if (token == 0) status=74;
        }
        wipe(address(count), 8);
        return status;
    }

    long lengthSlot() {
        // Distinguish an untouched length (denial/unknown function) from a published empty page.
        for (int i=0;i<8;i++) count[i]=(byte)255;
        return address(count);
    }

    int finish(int status, int requestSize, byte[] destination, long[] written, boolean permissionReport) {
        if (requestSize != 0) wipe(address(input),requestSize);
        long size=count();
        boolean publishesPage = status==0 || (permissionReport && status==95 && size!=-1);
        if (publishesPage) {
            if (size < 0 || size > destination.length) status=74;
            else {
                for (int i=0;i<(int)size;i++) destination[i]=output[i];
                written[0]=size;
            }
        } else if (status==90 && size>=0) {
            written[0]=size;
        }
        if (destination.length != 0) wipe(address(output),destination.length);
        wipe(address(count),8);
        return status;
    }
}
