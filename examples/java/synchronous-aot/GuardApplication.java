package example;

import wros.scene.Guard;

public final class GuardApplication {
    public static void main(String[] args) {
        Guard guard = new Guard();
        byte[] alias = {'s', 'i', 'g', 'n', 'a', 'l'};
        if (guard.open(alias) != 0 || guard.create() != 0) throw new AssertionError();
        long[] count = {-1};
        if (guard.trigger() != 0 || guard.take(count) != 0 || count[0] != 1) throw new AssertionError();
        if (guard.close() != 0) throw new AssertionError();
    }
}
