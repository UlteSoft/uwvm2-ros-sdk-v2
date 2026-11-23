/** Read-only projections of __wasi_fdstat_t. */
/** Read fs_filetype from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_fs_filetype(data: Uint8Array): number | undefined;

/** Read fs_flags from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_fs_flags(data: Uint8Array): number | undefined;

/** Read fs_rights_base from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_fs_rights_base(data: Uint8Array): bigint | undefined;

/** Read fs_rights_inheriting from the complete record. Invalid data or an invalid index returns undefined. */
export declare function read_fs_rights_inheriting(data: Uint8Array): bigint | undefined;
