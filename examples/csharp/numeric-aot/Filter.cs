public static class Filter
{
    public static int Scale(int reading)
    {
        return unchecked(7 * reading - 3);
    }
}
