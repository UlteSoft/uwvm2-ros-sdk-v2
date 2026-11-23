package example;

import u2rosv2.Scene;

/** Entry point for the WROS guest. The only scene operation is the ABI version query. */
public final class Guest {
    private Guest() {}

    /** Checks the bound scene before replaying the same observation code used on the JVM. */
    public static void main(String[] args) {
        if (Scene.abi() != 2) throw new AssertionError("unexpected scene ABI");
        Replay.main(args);
    }
}
