/** Read-only projections of __wasi_fdstat_t over bounded staging. */
import { begin, field, finish, bits } from "../../shared/reader";

function project(size: u32, wanted: u32, index: u32, fromReply: bool): bool {
    if (!begin(0, size, fromReply)) return false;
    if (!field(1, 1, 0, wanted == 0, index)) return false; // fs_filetype
    if (!field(1, 1, 0, wanted == 1, index)) return false; // pad1
    if (!field(2, 1, 0, wanted == 2, index)) return false; // fs_flags
    if (!field(1, 4, 0, wanted == 3, index)) return false; // pad2
    if (!field(8, 1, 0, wanted == 4, index)) return false; // fs_rights_base
    if (!field(8, 1, 0, wanted == 5, index)) return false; // fs_rights_inheriting
    return finish();
}

/** Last successfully decoded fs_filetype. */
export let fs_filetype: u8 = 0;

/** Validate the complete request or reply span, then publish fs_filetype. */
export function read_fs_filetype(size: u32, fromReply: bool = false): bool {
    if (!project(size, 0, 0, fromReply)) return false;
    fs_filetype = <u8>bits;
    return true;
}

/** Last successfully decoded fs_flags. */
export let fs_flags: u16 = 0;

/** Validate the complete request or reply span, then publish fs_flags. */
export function read_fs_flags(size: u32, fromReply: bool = false): bool {
    if (!project(size, 2, 0, fromReply)) return false;
    fs_flags = <u16>bits;
    return true;
}

/** Last successfully decoded fs_rights_base. */
export let fs_rights_base: u64 = 0;

/** Validate the complete request or reply span, then publish fs_rights_base. */
export function read_fs_rights_base(size: u32, fromReply: bool = false): bool {
    if (!project(size, 4, 0, fromReply)) return false;
    fs_rights_base = <u64>bits;
    return true;
}

/** Last successfully decoded fs_rights_inheriting. */
export let fs_rights_inheriting: u64 = 0;

/** Validate the complete request or reply span, then publish fs_rights_inheriting. */
export function read_fs_rights_inheriting(size: u32, fromReply: bool = false): bool {
    if (!project(size, 5, 0, fromReply)) return false;
    fs_rights_inheriting = <u64>bits;
    return true;
}
