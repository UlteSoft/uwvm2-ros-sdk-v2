/** Read-only projections of isaac_ros_tensor_list_interfaces/TensorShape. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u8", 1, 0], // rank
    ["u32", 0, 0], // dims
];

/** Read rank from the complete record. Invalid data or an invalid index returns undefined. */
export function read_rank(data) {
    return project(data, 1, fields, 0, 0);
}

/** Read dims from the complete record. Invalid data or an invalid index returns undefined. */
export function read_dims(data, index) {
    return project(data, 1, fields, 1, index);
}
