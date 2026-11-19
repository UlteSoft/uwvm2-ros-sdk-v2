using Wros;

public static class Robot
{
    public static int Start() => Accept(Scene.Abi());
    public static int Accept(int major) => major == 2 ? 0 : 1;
}
