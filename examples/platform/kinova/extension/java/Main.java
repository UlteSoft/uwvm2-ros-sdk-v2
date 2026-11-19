package example;
import wros.scene.Calls;
/** @brief Verify that a refused platform connection leaves the caller's reply intact. */
public final class Main {
    public static void main(String[] args) {
        Calls arm = new Calls(8,8);
        byte[] reply = {42,0,0,0,0,0,0,0};
        long[] written = {0};
        if (arm.capabilityOpen(new byte[]{'a','r','m'}) != 0 ||
            arm.driverConnect(new byte[0], reply, written) != 13 || reply[0] != 42 ||
            arm.capabilityClose() != 0) throw new AssertionError();
    }
}
