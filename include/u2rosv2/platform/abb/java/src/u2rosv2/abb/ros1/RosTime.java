package u2rosv2.abb.ros1;

/** The two unsigned 32-bit words of a ROS 1 time value in declaration order. */
public final class RosTime {
    /** Seconds since the clock's epoch, in the range 0 through 4,294,967,295. */
    public final long sec;

    /** Nanoseconds within the second. The decoder preserves the transmitted uint32 value. */
    public final long nsec;

    RosTime(long sec, long nsec) {
        this.sec = sec;
        this.nsec = nsec;
    }
}
