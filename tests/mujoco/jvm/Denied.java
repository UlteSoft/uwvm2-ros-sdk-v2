package simulation;
import wros.scene.Driver;

final class Denied {
    public static void main(String[] args) {
        Driver d = new Driver();
        if (d.open(new byte[]{110,111,110,101}, 8, 8) != 13) throw new AssertionError();
        if (d.open(new byte[]{114,101,97,100}, 8, 8) != 0) throw new AssertionError();
        if (d.connect() != 13 || d.close() != 0) throw new AssertionError();
    }
}
