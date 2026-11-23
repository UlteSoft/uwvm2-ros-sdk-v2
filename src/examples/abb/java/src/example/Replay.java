package example;

import u2rosv2.abb.ros1.Egm;
import u2rosv2.abb.ros1.Rapid;
import u2rosv2.abb.ros1.Robot;
import u2rosv2.abb.ros1.StateMachine;

/** Reads serialized ABB ROS 1 bodies in memory. This class also runs on a host JVM. */
public final class Replay {
    private Replay() {}

    /** Counts channels marked active, returning -1 for an invalid EGMState body. */
    public static int activeChannels(byte[] report) {
        Egm.EGMState state = Egm.EGMState.decode(report);
        if (state == null) return -1;
        int active = 0;
        for (Egm.EGMChannelState channel : state.egmChannels) {
            if (channel.active) ++active;
        }
        return active;
    }

    private static int digit(char c) {
        if (c >= '0' && c <= '9') return c - '0';
        if (c >= 'a' && c <= 'f') return c - 'a' + 10;
        throw new IllegalArgumentException("invalid hex digit");
    }

    private static byte[] bytes(String hex) {
        if ((hex.length() & 1) != 0) throw new IllegalArgumentException("incomplete byte");
        byte[] result = new byte[hex.length() / 2];
        for (int i = 0; i < result.length; ++i) {
            result[i] = (byte)((digit(hex.charAt(2 * i)) << 4) | digit(hex.charAt(2 * i + 1)));
        }
        return result;
    }

    /** Replays independent genpy bodies, then exercises a truncated slice and a corrupt array count. */
    public static void main(String[] args) {
        byte[] report = bytes("620000807300bbaa3e68de3a0c00000061626200c3a9e99baa2d383402000000"
                + "0c00000061626200c3a9e99baa2d6530010093a4b50000000000000080"
                + "0c00000061626200c3a9e99baa2d653700019aabbc000000000000c03f");
        Egm.EGMState state = Egm.EGMState.decode(report);
        if (state == null || state.header.seq != 2147483746L || state.header.stamp.sec != 2864382067L
                || state.egmChannels.length != 2 || activeChannels(report) != 1
                || state.egmChannels[1].utilizationRate != 0.125
                || state.egmChannels[0].name[3] != 0) {
            throw new AssertionError("EGM state");
        }
        if (Egm.EGMState.decode(report, 0, report.length - 1) != null) {
            throw new AssertionError("truncated EGM state");
        }
        report[31] = (byte)0x80;
        if (activeChannels(report) != -1) throw new AssertionError("unsigned channel count");

        Rapid.Pose pose = Rapid.Pose.decode(bytes("0000003e00000080000030400000008000003040000048c10098fa44"));
        if (pose == null || pose.trans.x != 0.125f || pose.rot.q3 != -12.5f
                || Float.floatToRawIntBits(pose.trans.y) != Integer.MIN_VALUE) {
            throw new AssertionError("RAPID pose");
        }

        StateMachine.RuntimeState runtime = StateMachine.RuntimeState.decode(bytes(
                "050400801604bbaa9b64de3a0d00000061626200c3a9e99baa2d34323702000000"
                + "0d00000061626200c3a9e99baa2d34383394a50d00000061626200c3a9e99baa2d3438619bac"));
        if (runtime == null || runtime.stateMachines.length != 2 || runtime.stateMachines[1].egmAction != 172) {
            throw new AssertionError("StateMachine report");
        }

        Robot.SystemState controller = Robot.SystemState.decode(bytes(
                "d30c0080e40cbbaacd5bde3a0d00000061626200c3a9e99baa2d63663500010002000000"
                + "0d00000061626200c3a9e99baa2d65623601d8010d00000061626200c3a9e99baa2d65626400df00"
                + "020000000d00000061626200c3a9e99baa2d663264000d00000061626200c3a9e99baa2d66333401"));
        if (controller == null || !controller.autoMode || controller.rapidTasks.length != 2
                || !controller.rapidTasks[0].motionTask || controller.mechanicalUnits.length != 2
                || !controller.mechanicalUnits[1].activated) {
            throw new AssertionError("controller state");
        }

        Robot.GetRAPIDNumResponse response = Robot.GetRAPIDNumResponse.decode(
                bytes("000000801b810d00000061626200c3a9e99baa2d313263"));
        if (response == null || response.resultCode != 33051 || response.message.length != 13) {
            throw new AssertionError("RWS service status");
        }
    }
}
