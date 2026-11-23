//! Typed ABB ROS 1 message bodies. Decoded strings and sequences borrow the input.
//! All operations are allocation-free. Import [`Message`] to use the record methods.

use core::convert::TryInto;

/// Wire-format errors for a complete ABB ROS 1 payload.
#[derive(Debug, Clone, Copy, Eq, PartialEq)]
pub enum Error {
    /// A scalar, string or counted element extends past the available input.
    Truncated,
    /// Valid fields were followed by extra bytes.
    TrailingBytes,
    /// A boolean field contained a byte other than zero or one.
    InvalidBool,
    /// A string length, array count or total body size exceeds a ROS uint32.
    LengthOverflow,
    /// The output slice cannot hold the complete body.
    BufferTooSmall,
}

/// ROS 1 two-word timestamp.
#[derive(Debug, Clone, Copy, Default, Eq, PartialEq)]
pub struct Time {
    /// Seconds since the ROS time epoch.
    pub sec: u32,
    /// Nanoseconds within that second.
    pub nsec: u32,
}

/// Counts, encodes and decodes a complete message, request or response body.
pub trait Message<'a>: Sized {
    #[doc(hidden)]
    const MIN_WIRE_SIZE: usize;
    #[doc(hidden)]
    fn read(reader: &mut Reader<'a>) -> Result<Self, Error>;
    #[doc(hidden)]
    fn write(&self, writer: &mut Writer<'_>) -> Result<(), Error>;

    /// Decode the entire input. Nested strings and sequence elements can borrow this slice.
    ///
    /// Returns a wire error for trailing data, truncation, an invalid boolean or excessive length.
    fn decode(data: &'a [u8]) -> Result<Self, Error> {
        if data.len() > u32::MAX as usize {
            return Err(Error::LengthOverflow);
        }
        let mut reader = Reader { rest: data };
        let value = Self::read(&mut reader)?;
        if !reader.rest.is_empty() {
            return Err(Error::TrailingBytes);
        }
        Ok(value)
    }

    /// Check a complete body, including all counted elements, without retaining the result.
    fn validate(data: &'a [u8]) -> Result<(), Error> {
        Self::decode(data).map(|_| ())
    }

    /// Compute the exact body size. Returns [`Error::LengthOverflow`] for unrepresentable data.
    fn encoded_size(&self) -> Result<usize, Error> {
        let mut writer = Writer { data: None, pos: 0 };
        self.write(&mut writer)?;
        Ok(writer.pos)
    }

    /// Write a complete body and return its byte count. Capacity and wire lengths are checked
    /// before writing, so errors leave the supplied buffer untouched for generated ABB types.
    fn encode(&self, buffer: &mut [u8]) -> Result<usize, Error> {
        let size = self.encoded_size()?;
        if size > buffer.len() {
            return Err(Error::BufferTooSmall);
        }
        let mut writer = Writer { data: Some(buffer), pos: 0 };
        self.write(&mut writer)?;
        Ok(writer.pos)
    }
}

/// Association between a ROS service identity and the two payload types.
pub trait Service {
    /// ROS 1 connection-header datatype, e.g. `abb_robot_msgs/GetRAPIDNum`.
    const TYPE: &'static str;
    /// ROS 1 connection-header MD5 over the definitions of both service bodies.
    const MD5: &'static str;
    /// Request message body. Its decoded values can borrow the input for `'a`.
    type Request<'a>: Message<'a>;
    /// Successful transport reply payload, including the ABB result code and status message.
    type Response<'a>: Message<'a>;
}

#[doc(hidden)]
pub struct Reader<'a> {
    rest: &'a [u8],
}
impl<'a> Reader<'a> {
    fn bytes(&mut self, length: usize) -> Result<&'a [u8], Error> {
        if length > self.rest.len() {
            return Err(Error::Truncated);
        }
        let (value, rest) = self.rest.split_at(length);
        self.rest = rest;
        Ok(value)
    }
    fn fixed<const N: usize>(&mut self) -> Result<[u8; N], Error> {
        self.bytes(N)?.try_into().map_err(|_| Error::Truncated)
    }
    fn uint8(&mut self) -> Result<u8, Error> { Ok(self.fixed::<1>()?[0]) }
    fn uint16(&mut self) -> Result<u16, Error> { Ok(u16::from_le_bytes(self.fixed()?)) }
    fn uint32(&mut self) -> Result<u32, Error> { Ok(u32::from_le_bytes(self.fixed()?)) }
    fn float32(&mut self) -> Result<f32, Error> { Ok(f32::from_le_bytes(self.fixed()?)) }
    fn float64(&mut self) -> Result<f64, Error> { Ok(f64::from_le_bytes(self.fixed()?)) }
    fn boolean(&mut self) -> Result<bool, Error> {
        match self.uint8()? {
            0 => Ok(false),
            1 => Ok(true),
            _ => Err(Error::InvalidBool),
        }
    }
    fn time(&mut self) -> Result<Time, Error> {
        Ok(Time { sec: self.uint32()?, nsec: self.uint32()? })
    }
    fn string(&mut self) -> Result<&'a [u8], Error> {
        let length = self.uint32()? as usize;
        self.bytes(length)
    }
    fn sequence<T: Message<'a> + Copy>(&mut self) -> Result<Sequence<'a, T>, Error> {
        let count = self.uint32()? as usize;
        if T::MIN_WIRE_SIZE > 0 && count > self.rest.len() / T::MIN_WIRE_SIZE {
            return Err(Error::Truncated);
        }
        let start = self.rest;
        for _ in 0..count {
            T::read(self)?;
        }
        let bytes = &start[..start.len() - self.rest.len()];
        Ok(Sequence { storage: Storage::Wire(bytes, count) })
    }
}

#[doc(hidden)]
pub struct Writer<'a> {
    data: Option<&'a mut [u8]>,
    pos: usize,
}
impl Writer<'_> {
    fn bytes(&mut self, input: &[u8]) -> Result<(), Error> {
        let end = self.pos.checked_add(input.len()).ok_or(Error::LengthOverflow)?;
        if end > u32::MAX as usize {
            return Err(Error::LengthOverflow);
        }
        if let Some(ref mut data) = self.data {
            data.get_mut(self.pos..end).ok_or(Error::BufferTooSmall)?.copy_from_slice(input);
        }
        self.pos = end;
        Ok(())
    }
    fn uint8(&mut self, v: u8) -> Result<(), Error> { self.bytes(&[v]) }
    fn uint16(&mut self, v: u16) -> Result<(), Error> { self.bytes(&v.to_le_bytes()) }
    fn uint32(&mut self, v: u32) -> Result<(), Error> { self.bytes(&v.to_le_bytes()) }
    fn float32(&mut self, v: f32) -> Result<(), Error> { self.bytes(&v.to_le_bytes()) }
    fn float64(&mut self, v: f64) -> Result<(), Error> { self.bytes(&v.to_le_bytes()) }
    fn boolean(&mut self, v: bool) -> Result<(), Error> { self.uint8(u8::from(v)) }
    fn time(&mut self, v: Time) -> Result<(), Error> {
        self.uint32(v.sec)?;
        self.uint32(v.nsec)
    }
    fn count(&mut self, length: usize) -> Result<(), Error> {
        self.uint32(length.try_into().map_err(|_| Error::LengthOverflow)?)
    }
    fn string(&mut self, value: &[u8]) -> Result<(), Error> {
        self.count(value.len())?;
        self.bytes(value)
    }
    fn sequence<'a, T: Message<'a> + Copy>(&mut self, seq: &Sequence<'a, T>) -> Result<(), Error> {
        self.count(seq.len())?;
        match seq.storage {
            Storage::Values(values) => {
                for item in values {
                    item.write(self)?;
                }
                Ok(())
            }
            Storage::Wire(bytes, _) => self.bytes(bytes),
        }
    }
}

#[derive(Clone, Copy, Debug)]
enum Storage<'a, T> {
    Values(&'a [T]),
    Wire(&'a [u8], usize),
}

/// Either a borrowed typed slice for encoding or validated element bytes from a decoded record.
#[derive(Clone, Copy, Debug)]
pub struct Sequence<'a, T> {
    storage: Storage<'a, T>,
}
impl<'a, T: Message<'a> + Copy> Sequence<'a, T> {
    /// Borrow a typed slice for use as a ROS variable-length array field.
    pub fn from_values(values: &'a [T]) -> Self { Self { storage: Storage::Values(values) } }
    /// Return the number of typed elements, including for variable-width records.
    pub fn len(&self) -> usize {
        match self.storage {
            Storage::Values(values) => values.len(),
            Storage::Wire(_, count) => count,
        }
    }
    /// Returns true for a zero-element sequence.
    pub fn is_empty(&self) -> bool { self.len() == 0 }
    /// Iterate from the first element. Strings inside each item borrow the source storage.
    pub fn iter(&self) -> SequenceIter<'a, T> { SequenceIter { rest: self.storage } }
}
impl<T> Default for Sequence<'_, T> {
    fn default() -> Self { Self { storage: Storage::Values(&[]) } }
}

/// Forward iterator over validated wire elements or a caller-owned typed slice.
pub struct SequenceIter<'a, T> {
    rest: Storage<'a, T>,
}
impl<'a, T: Message<'a> + Copy> Iterator for SequenceIter<'a, T> {
    type Item = T;
    fn next(&mut self) -> Option<T> {
        match self.rest {
            Storage::Values(values) => {
                let (value, tail) = values.split_first()?;
                self.rest = Storage::Values(tail);
                Some(*value)
            }
            Storage::Wire(_, 0) => None,
            Storage::Wire(bytes, count) => {
                let mut reader = Reader { rest: bytes };
                let value = T::read(&mut reader).ok()?;
                self.rest = Storage::Wire(reader.rest, count - 1);
                Some(value)
            }
        }
    }
}

include!("records.rs");
