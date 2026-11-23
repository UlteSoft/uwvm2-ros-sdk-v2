//! Read-only projections of __wasi_fdstat_t.
#![no_std]
#[path = "../../shared/reader.rs"]
mod reader;
use reader::Field;

const LAYOUT: &[Field] = &[
    Field(1, 1, 0), // fs_filetype
    Field(1, 1, 0), // pad1
    Field(2, 1, 0), // fs_flags
    Field(1, 4, 0), // pad2
    Field(8, 1, 0), // fs_rights_base
    Field(8, 1, 0), // fs_rights_inheriting
];

/// Read fs_filetype.
pub fn read_fs_filetype(data: &[u8]) -> Option<u8> {
    let bits = reader::project(data, 0, LAYOUT, 0, 0)?;
    Some(bits as u8)
}

/// Read fs_flags.
pub fn read_fs_flags(data: &[u8]) -> Option<u16> {
    let bits = reader::project(data, 0, LAYOUT, 2, 0)?;
    Some(bits as u16)
}

/// Read fs_rights_base.
pub fn read_fs_rights_base(data: &[u8]) -> Option<u64> {
    let bits = reader::project(data, 0, LAYOUT, 4, 0)?;
    Some(bits)
}

/// Read fs_rights_inheriting.
pub fn read_fs_rights_inheriting(data: &[u8]) -> Option<u64> {
    let bits = reader::project(data, 0, LAYOUT, 5, 0)?;
    Some(bits)
}
