/** Read-only projections of Isaac Sim ROS2 Publish Clock / rosgraph_msgs/Clock. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["i32", 1, 0], // clock_sec
    ["u32", 1, 0], // clock_nanosec
];

/** Read clock_sec from the complete record. Invalid data or an invalid index returns undefined. */
export function read_clock_sec(data) {
    return project(data, 1, fields, 0, 0);
}

/** Read clock_nanosec from the complete record. Invalid data or an invalid index returns undefined. */
export function read_clock_nanosec(data) {
    return project(data, 1, fields, 1, 0);
}
