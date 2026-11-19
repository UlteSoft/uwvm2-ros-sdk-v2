// Host reference assembly used by Roslyn. The final guest imports the named
// core-Wasm function directly and does not load this assembly or the CLR.
namespace Wros
{
    public static class Scene
    {
        [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.InternalCall)]
        public static extern int Abi();
    }
}
