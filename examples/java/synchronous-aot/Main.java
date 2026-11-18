package example;
import wros.scene.Scene;
public final class Main {
    public static void main(String[] args) {
        if (args.length != 0 || Scene.abi() != 2) throw new AssertionError();
    }
}
