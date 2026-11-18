using System.Runtime.CompilerServices;
public static class Body
{
    [MethodImpl(MethodImplOptions.NoInlining)]
    public static void Swap(ref int a, ref int b)
    {
        int before = a;
        a = b + 5;
        b = before * 7;
    }

    public static int Control(int reading)
    {
        int left = reading;
        int right = reading ^ 0x125;
        Swap(ref left, ref right);
        return left ^ right;
    }

    public static int Rotate(int value) { return unchecked((value * 17 + 3) ^ (value >> 4)); }
    public static unsafe int TagNeighbors(int reading)
    {
        long left = reading;
        long right = reading + 1;
        nuint a = (nuint)(&left);
        nuint b = (nuint)(&right);
        return (int)((a >> 28) | ((b >> 28) << 4));
    }
    public static int ManagedArray(int n)
    {
        int[] values = new int[4];
        values[2] = n;
        return values[2] + values.Length;
    }
}
