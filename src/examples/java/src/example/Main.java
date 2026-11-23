package example;

import u2rosv2.Scene;

/** Entry point for a deployment that exposes the ABI version query. */
public final class Main {
    public static void main(String[] args) {
        if (Scene.abi() != 2) throw new AssertionError("scene ABI");
    }
}
