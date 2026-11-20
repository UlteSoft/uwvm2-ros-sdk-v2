/** @file ShiftMatrix.java
 * @brief Exercise the Java int and long shift operations on run-time operands.
 */
package example;

public final class ShiftMatrix {
    private static final int[] COUNTS = {
        Integer.MIN_VALUE, -129, -128, -65, -64, -63, -33, -32, -31, -1,
        0, 1, 7, 15, 31, 32, 33, 63, 64, 65, 127, 128, Integer.MAX_VALUE
    };
    private static final long[] VALUES = {
        0L, 1L, -1L, -7L, Integer.MIN_VALUE, Integer.MAX_VALUE,
        Long.MIN_VALUE, Long.MAX_VALUE, 0x8123456789abcdefL, 0x0102030405060708L
    };
    public static final int CASES = COUNTS.length * VALUES.length * 6;
    private static volatile int count;
    private static volatile long value;

    public static long result(int index) {
        int pair = index / 6;
        count = COUNTS[pair % COUNTS.length];
        value = VALUES[pair / COUNTS.length];
        switch (index % 6) {
            case 0: return (int) value << count;
            case 1: return (int) value >> count;
            case 2: return (int) value >>> count;
            case 3: return value << count;
            case 4: return value >> count;
            case 5: return value >>> count;
            default: throw new AssertionError();
        }
    }
}
