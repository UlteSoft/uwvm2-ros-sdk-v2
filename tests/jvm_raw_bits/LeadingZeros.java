/** @file LeadingZeros.java
 * @brief Compare integer leading-zero counts with a bit scan and test upstream power rounding.
 */
package example;

import it.unimi.dsi.fastutil.HashCommon;

public final class LeadingZeros {
    private static void checkInt(int value) {
        int expected = 32;
        for (int bit = 31; bit >= 0; --bit) {
            if ((value & (1 << bit)) != 0) {
                expected = 31 - bit;
                break;
            }
        }
        if (Integer.numberOfLeadingZeros(value) != expected)
            throw new AssertionError();
    }

    private static void checkLong(long value) {
        int expected = 64;
        for (int bit = 63; bit >= 0; --bit) {
            if ((value & (1L << bit)) != 0L) {
                expected = 63 - bit;
                break;
            }
        }
        if (Long.numberOfLeadingZeros(value) != expected)
            throw new AssertionError();
    }

    public static void main(String[] args) {
        for (int value : new int[] {0, 1, -1, -7, Integer.MIN_VALUE, Integer.MAX_VALUE})
            checkInt(value);
        for (long value : new long[] {0L, 1L, -1L, -7L, Long.MIN_VALUE, Long.MAX_VALUE})
            checkLong(value);
        for (int bit = 0; bit < 32; ++bit)
            checkInt(1 << bit);
        for (int bit = 0; bit < 64; ++bit)
            checkLong(1L << bit);

        int i32 = 0x4c957f2d;
        long i64 = 0x3259ab16d0c934d3L;
        for (int i = 0; i < 8192; ++i) {
            i32 ^= i32 << 13;
            i32 ^= i32 >>> 17;
            i32 ^= i32 << 5;
            i64 ^= i64 << 13;
            i64 ^= i64 >>> 7;
            i64 ^= i64 << 17;
            checkInt(i32);
            checkLong(i64);
        }

        if (HashCommon.nextPowerOfTwo(0) != 1 || HashCommon.nextPowerOfTwo(0L) != 1L
                || HashCommon.nextPowerOfTwo(1) != 1 || HashCommon.nextPowerOfTwo(1L) != 1L)
            throw new AssertionError();
        for (int bit = 2; bit <= 30; ++bit) {
            int power = 1 << bit;
            if (HashCommon.nextPowerOfTwo(power) != power || HashCommon.nextPowerOfTwo(power - 1) != power)
                throw new AssertionError();
            if (bit < 30 && HashCommon.nextPowerOfTwo(power + 1) != power << 1)
                throw new AssertionError();
        }
        for (int bit = 2; bit <= 62; ++bit) {
            long power = 1L << bit;
            if (HashCommon.nextPowerOfTwo(power) != power || HashCommon.nextPowerOfTwo(power - 1L) != power)
                throw new AssertionError();
            if (bit < 62 && HashCommon.nextPowerOfTwo(power + 1L) != power << 1)
                throw new AssertionError();
        }
    }
}
