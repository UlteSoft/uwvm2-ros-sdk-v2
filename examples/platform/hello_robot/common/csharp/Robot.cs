/** @brief Check the ROSv2 ABI inside the guest and fail on mismatch. */
using Wros;

public static class Robot
{
    public static int Start() => Accept(Scene.Abi());
    public static int Accept(int major) => major == 2 ? 0 : 1;
}
