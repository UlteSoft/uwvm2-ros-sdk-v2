import * as observation from "uwrosv2/platform/wasi/observation";

/* Constructed from the pinned upstream wire definition. */
const sample = new Uint8Array([
    0x04, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x42, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00
]);

function check(data) {
    if (observation.read_fs_filetype(data) !== 4) throw Error("fs_filetype");
    if (observation.read_fs_filetype(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated fs_filetype");
    if (observation.read_fs_flags(data) !== 1) throw Error("fs_flags");
    if (observation.read_fs_flags(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated fs_flags");
    if (observation.read_fs_rights_base(data) !== 66n) throw Error("fs_rights_base");
    if (observation.read_fs_rights_base(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated fs_rights_base");
    if (observation.read_fs_rights_inheriting(data) !== 4294967297n) throw Error("fs_rights_inheriting");
    if (observation.read_fs_rights_inheriting(data.subarray(0, data.length - 1)) !== undefined) throw Error("truncated fs_rights_inheriting");
}

check(sample);
