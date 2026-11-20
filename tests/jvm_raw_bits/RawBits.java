/** @file RawBits.java
 * @brief Verify exact JVM bit reinterpretation through a guest collection.
 */
package example;

public final class RawBits {
    public static void main(String[] args) {
        int[] floatBits = {
            0x00000000, 0x80000000, 0x3f800000, 0xbf800000, 0x00000001, 0x807fffff,
            0x7f800000, 0xff800000, 0x7fc12345, 0xffc65432, 0x7fffffff,
        };
        long[] doubleBits = {
            0x0000000000000000L, 0x8000000000000000L, 0x3ff0000000000000L,
            0xbff0000000000000L, 0x0000000000000001L, 0x800fffffffffffffL,
            0x7ff0000000000000L, 0xfff0000000000000L, 0x7ff8123456789abcL,
            0xfff8fedcba987654L, 0x7fffffffffffffffL,
        };
        float[] floats = new float[floatBits.length];
        double[] doubles = new double[doubleBits.length];
        for (int i = 0; i < floatBits.length; ++i)
            floats[i] = Float.intBitsToFloat(floatBits[i]);
        for (int i = 0; i < doubleBits.length; ++i)
            doubles[i] = Double.longBitsToDouble(doubleBits[i]);
        System.gc();
        for (int i = 0; i < floatBits.length; ++i)
            if (Float.floatToRawIntBits(floats[i]) != floatBits[i])
                throw new AssertionError();
        for (int i = 0; i < doubleBits.length; ++i)
            if (Double.doubleToRawLongBits(doubles[i]) != doubleBits[i])
                throw new AssertionError();

        if (floats[2] != 1.0f || floats[3] != -1.0f || doubles[2] != 1.0 || doubles[3] != -1.0)
            throw new AssertionError();
        if (floats[8] == floats[8] || doubles[8] == doubles[8])
            throw new AssertionError();
        if (Float.floatToRawIntBits(-0.0f) != 0x80000000
                || Double.doubleToRawLongBits(-0.0) != 0x8000000000000000L)
            throw new AssertionError();
    }
}
