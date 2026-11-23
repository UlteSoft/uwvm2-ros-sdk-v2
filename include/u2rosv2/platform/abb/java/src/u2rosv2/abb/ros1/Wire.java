package u2rosv2.abb.ros1;

/** Bounds-checked cursor over a single ROS 1 body, shared by the domain decoders. */
final class Wire {
    private final byte[] data;
    private int offset;
    private int end;
    private boolean valid;

    Wire(byte[] data, int start, int length) {
        this.data = data;
        valid = data != null && start >= 0 && length >= 0 && start <= data.length - length;
        if (valid) {
            offset = start;
            end = start + length;
        }
    }

    boolean valid() {
        return valid;
    }

    boolean finished() {
        return valid && offset == end;
    }

    boolean require(int bytes) {
        if (bytes > end - offset) valid = false;
        return valid;
    }

    int uint8() {
        return require(1) ? data[offset++] & 0xff : 0;
    }

    boolean bool() {
        int value = uint8();
        if (value > 1) valid = false;
        return value == 1;
    }

    int uint16() {
        if (!require(2)) return 0;
        int word = (data[offset] & 0xff) | (data[offset + 1] & 0xff) << 8;
        offset += 2;
        return word;
    }

    private int word() {
        if (!require(4)) return 0;
        int word = (data[offset] & 0xff) | (data[offset + 1] & 0xff) << 8
                | (data[offset + 2] & 0xff) << 16 | data[offset + 3] << 24;
        offset += 4;
        return word;
    }

    long uint32() {
        return word() & 0xffff_ffffL;
    }

    float float32() {
        return Float.intBitsToFloat(word());
    }

    double float64() {
        long low = uint32();
        long high = uint32();
        return Double.longBitsToDouble(low | high << 32);
    }

    RosTime time() {
        return new RosTime(uint32(), uint32());
    }

    int count(int minimumElementBytes) {
        long count = uint32();
        if (count > (end - offset) / minimumElementBytes) valid = false;
        return valid ? (int) count : 0;
    }

    byte[] stringBytes() {
        int bytes = count(1);
        if (!valid) return null;
        byte[] result = new byte[bytes];
        for (int i = 0; i < bytes; ++i) result[i] = data[offset + i];
        offset += bytes;
        return result;
    }
}
