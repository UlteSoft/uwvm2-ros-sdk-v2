//! Allocation-free record I/O. Canonical text and blobs have a little-endian u64
//! byte length. Fixed artifact digests and tail payloads use raw bytes.

use crate::{Error, Result};
use crate::base::invalid;

pub struct Writer<'a> {
    storage: &'a mut [u8],
    used: usize,
}
impl<'a> Writer<'a> {
    pub fn new(storage: &'a mut [u8]) -> Self { Self { storage, used: 0 } }
    pub fn written(&self) -> &[u8] { &self.storage[..self.used] }
    pub fn word(&mut self, word: u64) -> Result<()> { self.raw(&word.to_le_bytes()) }
    pub fn raw(&mut self, bytes: &[u8]) -> Result<()> {
        let end = self.used.checked_add(bytes.len()).ok_or_else(invalid)?;
        let out = self.storage.get_mut(self.used..end)
            .ok_or(Error { status: 90, reported: end as u64 })?;
        out.copy_from_slice(bytes);
        self.used = end;
        Ok(())
    }
    pub fn blob(&mut self, bytes: &[u8]) -> Result<()> {
        let end = self.used.checked_add(8).and_then(|n| n.checked_add(bytes.len())).ok_or_else(invalid)?;
        if end > self.storage.len() { return Err(Error { status: 90, reported: end as u64 }); }
        self.word(bytes.len() as u64)?;
        self.raw(bytes)
    }
    pub fn text(&mut self, value: &str) -> Result<()> { self.blob(value.as_bytes()) }
}

pub struct Reader<'a> { remaining: &'a [u8] }
impl<'a> Reader<'a> {
    pub fn new(bytes: &'a [u8]) -> Self { Self { remaining: bytes } }
    pub fn word(&mut self) -> Result<u64> {
        let bytes = self.remaining.get(..8).ok_or_else(invalid)?;
        let word = u64::from_le_bytes(bytes.try_into().map_err(|_| invalid())?);
        self.remaining = &self.remaining[8..];
        Ok(word)
    }
    pub fn blob(&mut self) -> Result<&'a [u8]> {
        let n = usize::try_from(self.word()?).map_err(|_| invalid())?;
        let bytes = self.remaining.get(..n).ok_or_else(invalid)?;
        self.remaining = &self.remaining[n..];
        Ok(bytes)
    }
    pub fn text(&mut self) -> Result<&'a str> {
        core::str::from_utf8(self.blob()?).map_err(|_| invalid())
    }
    pub fn complete(&self) -> Result<()> {
        if self.remaining.is_empty() { Ok(()) } else { Err(invalid()) }
    }
}
