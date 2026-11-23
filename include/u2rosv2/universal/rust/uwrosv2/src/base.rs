/// An execution capability bound to the current module instance and its grant.
#[derive(Debug, PartialEq, Eq)]
pub struct Capability(u64);

impl Capability {
    /// Recover a previously issued identifier. The VM rechecks the actual caller on every use.
    pub const fn from_id(id: u64) -> Option<Self> {
        if id == 0 { None } else { Some(Self(id)) }
    }
    pub const fn id(&self) -> u64 { self.0 }
    pub(crate) fn clear(&mut self) { self.0 = 0; }
}

/// A provider-owned identity. Retire through its provider's close or release operation.
#[derive(Debug, PartialEq, Eq)]
pub struct Resource(u64);

impl Resource {
    pub const fn from_id(id: u64) -> Option<Self> {
        if id == 0 { None } else { Some(Self(id)) }
    }
    pub const fn id(&self) -> u64 { self.0 }
    pub(crate) fn clear(&mut self) { self.0 = 0; }
}

/// Carrier failure. A short output may report the required capacity. For permission
/// observation, unsupported may also deliver a supported=false page of this length.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Error {
    pub status: u32,
    pub reported: u64,
}
pub type Result<T> = core::result::Result<T, Error>;

pub(crate) const fn invalid() -> Error { Error { status: 22, reported: 0 } }
pub(crate) fn finish(status: u32, bytes: [u8; 8], capacity: usize) -> Result<usize> {
    let reported = u64::from_le_bytes(bytes);
    if status != 0 { return Err(Error { status, reported }); }
    if reported > capacity as u64 { return Err(Error { status: 22, reported }); }
    Ok(reported as usize)
}
pub(crate) fn address<T>(ptr: *const T) -> u64 { ptr as usize as u64 }
