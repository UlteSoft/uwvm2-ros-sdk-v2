public static class SimulatedJoint
{
    public static int Direction(int step)
    {
        return ((step & 1) << 1) - 1;
    }
}
