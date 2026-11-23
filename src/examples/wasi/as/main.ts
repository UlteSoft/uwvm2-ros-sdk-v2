import * as observation from "./uwrosv2/platform/wasi/observation";
import { writeByte, writeWord } from "./wros";

function check(size: u32): void {
    if (!observation.read_fs_filetype(size) || observation.fs_filetype != 4) unreachable();
    if (observation.read_fs_filetype(size - 1)) unreachable();
    if (!observation.read_fs_flags(size) || observation.fs_flags != 1) unreachable();
    if (observation.read_fs_flags(size - 1)) unreachable();
    if (!observation.read_fs_rights_base(size) || observation.fs_rights_base != 66) unreachable();
    if (observation.read_fs_rights_base(size - 1)) unreachable();
    if (!observation.read_fs_rights_inheriting(size) || observation.fs_rights_inheriting != 4294967297) unreachable();
    if (observation.read_fs_rights_inheriting(size - 1)) unreachable();
}

/** Stage complete wire examples for the pinned upstream field layout. */
export function _start(): void {
    writeWord(0, 0x0000000000010004);
    writeWord(8, 0x0000000000000042);
    writeWord(16, 0x0000000100000001);
    check(24);
}
