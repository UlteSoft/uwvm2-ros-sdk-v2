package example;
import wros.scene.Guard;
public final class GuardApplication {
    public static void main(String[] args) {
        Guard g = new Guard();
        int policy = 2;
        int code = g.open(new byte[]{115,105,103,110,97,108});
        if (policy == 0) { if (code != 13) throw new AssertionError(); return; }
        if (code != 0 || g.create() != 0) throw new AssertionError();
        System.gc();
        int result = g.trigger();
        if (policy == 1) { if (result != 13 || g.close() != 0) throw new AssertionError(); return; }
        long[] count = {-1};
        if (result != 0 || g.take(count)!=0 || count[0]!=1 || g.close()!=0) throw new AssertionError();
    }
}
