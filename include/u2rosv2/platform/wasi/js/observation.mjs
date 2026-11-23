/** Read-only projections of __wasi_fdstat_t. */
import { project } from "../../shared/reader.mjs";

const fields = [
    ["u8", 1, 0], // fs_filetype
    ["u8", 1, 0], // pad1
    ["u16", 1, 0], // fs_flags
    ["u8", 4, 0], // pad2
    ["u64", 1, 0], // fs_rights_base
    ["u64", 1, 0], // fs_rights_inheriting
];

/** Read fs_filetype from the complete record. Invalid data or an invalid index returns undefined. */
export function read_fs_filetype(data) {
    return project(data, 0, fields, 0, 0);
}

/** Read fs_flags from the complete record. Invalid data or an invalid index returns undefined. */
export function read_fs_flags(data) {
    return project(data, 0, fields, 2, 0);
}

/** Read fs_rights_base from the complete record. Invalid data or an invalid index returns undefined. */
export function read_fs_rights_base(data) {
    return project(data, 0, fields, 4, 0);
}

/** Read fs_rights_inheriting from the complete record. Invalid data or an invalid index returns undefined. */
export function read_fs_rights_inheriting(data) {
    return project(data, 0, fields, 5, 0);
}
