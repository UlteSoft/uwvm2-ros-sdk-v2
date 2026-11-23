//! Local XCDRv1 PLAIN_CDR codecs for the Universal Robots dashboard messages.
//! Decoded string slices borrow the immutable input frame. Writers use caller-provided storage.
use core::convert::{TryFrom, TryInto};

pub mod ur_dashboard_msgs;

/// Byte order carried by the four-byte CDR encapsulation.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Endian {
    Big,
    Little,
}

/// Failure while reading or writing a complete message.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Encapsulation,
    Truncated,
    InvalidPadding,
    TrailingBytes,
    InvalidString,
    LengthOverflow,
    OutputTooSmall,
}

/// Cursor used by generated field readers. Its alignment origin is the first payload byte.
#[doc(hidden)]
pub struct Reader<'a> {
    data: &'a [u8],
    pos: usize,
    order: Endian,
    tail: u8,
}

impl<'a> Reader<'a> {
    fn frame(data: &'a [u8]) -> Result<Self, Error> {
        let header = data.get(..4).ok_or(Error::Truncated)?;
        if header[0] != 0 || header[1] > 1 || header[2] != 0 || header[3] > 3 {
            return Err(Error::Encapsulation);
        }
        let order = if header[1] == 0 { Endian::Big } else { Endian::Little };
        Ok(Self { data: &data[4..], pos: 0, order, tail: header[3] })
    }

    fn finish(self) -> Result<(), Error> {
        let tail = usize::from(self.tail);
        if tail != 0 && tail != (self.pos.wrapping_neg() & 3) {
            return Err(Error::InvalidPadding);
        }
        let remaining = self.data.len() - self.pos;
        if remaining != 0 && remaining != tail { return Err(Error::TrailingBytes); }
        Ok(())
    }

    fn take(&mut self, count: usize) -> Result<&'a [u8], Error> {
        let end = self.pos.checked_add(count).ok_or(Error::LengthOverflow)?;
        let bytes = self.data.get(self.pos..end).ok_or(Error::Truncated)?;
        self.pos = end;
        Ok(bytes)
    }

    fn word<const N: usize>(&mut self) -> Result<[u8; N], Error> {
        self.take(self.pos.wrapping_neg() & (N - 1))?;
        self.take(N)?.try_into().map_err(|_| Error::Truncated)
    }

    fn string(&mut self) -> Result<&'a [u8], Error> {
        let count = usize::try_from(self.u32()?).map_err(|_| Error::LengthOverflow)?;
        self.take(count)?.strip_suffix(&[0]).ok_or(Error::InvalidString)
    }
}

/// Destination or measuring cursor used by generated field writers.
#[doc(hidden)]
pub struct Writer<'a> {
    data: Option<&'a mut [u8]>,
    pos: usize,
    order: Endian,
}

impl Writer<'_> {
    fn append(&mut self, bytes: &[u8]) -> Result<(), Error> {
        let end = self.pos.checked_add(bytes.len()).ok_or(Error::LengthOverflow)?;
        if let Some(data) = self.data.as_mut() {
            data.get_mut(self.pos..end).ok_or(Error::OutputTooSmall)?.copy_from_slice(bytes);
        }
        self.pos = end;
        Ok(())
    }

    fn word<const N: usize>(&mut self, bytes: &[u8; N]) -> Result<(), Error> {
        let padding = self.pos.wrapping_neg() & (N - 1);
        self.append(&[0; 7][..padding])?;
        self.append(bytes)
    }

    fn string(&mut self, bytes: &[u8]) -> Result<(), Error> {
        let count = u32::try_from(bytes.len()).ok().and_then(|n| n.checked_add(1)).ok_or(Error::LengthOverflow)?;
        self.u32(count)?;
        self.append(bytes)?;
        self.append(&[0])
    }
}

macro_rules! scalar {
    ($name:ident, $width:literal) => {
        impl Reader<'_> {
            fn $name(&mut self) -> Result<$name, Error> {
                let bytes = self.word::<$width>()?;
                Ok(match self.order {
                    Endian::Big => $name::from_be_bytes(bytes),
                    Endian::Little => $name::from_le_bytes(bytes),
                })
            }
        }
        impl Writer<'_> {
            fn $name(&mut self, value: $name) -> Result<(), Error> {
                let bytes = match self.order {
                    Endian::Big => value.to_be_bytes(),
                    Endian::Little => value.to_le_bytes(),
                };
                self.word(&bytes)
            }
        }
    };
}
scalar!(i8, 1);
scalar!(u8, 1);
scalar!(u32, 4);
scalar!(u64, 8);

/// Framing operations for one upstream message type on in-memory buffers.
pub trait Message<'a>: Sized {
    /// Fully qualified ROS 2 type name.
    const TYPE: &'static str;
    #[doc(hidden)]
    fn read(r: &mut Reader<'a>) -> Result<Self, Error>;
    #[doc(hidden)]
    fn write(&self, w: &mut Writer<'_>) -> Result<(), Error>;

    /// Decode all fields and retain borrowed string contents for the lifetime of the frame.
    fn decode(frame: &'a [u8]) -> Result<Self, Error> {
        let mut cursor = Reader::frame(frame)?;
        let value = Self::read(&mut cursor)?;
        cursor.finish()?;
        Ok(value)
    }

    /// Check the encapsulation, fields and end of the frame.
    fn validate(frame: &'a [u8]) -> Result<(), Error> {
        Self::decode(frame).map(|_| ())
    }

    /// Measure the full canonical frame in bytes, including its four-byte header.
    fn encoded_size(&self) -> Result<usize, Error> {
        let mut measure = Writer { data: None, pos: 0, order: Endian::Little };
        self.write(&mut measure)?;
        measure.pos.checked_add(4).ok_or(Error::LengthOverflow)
    }

    /// Encode into the supplied slice and return the exact number of bytes written.
    fn encode(&self, order: Endian, out: &mut [u8]) -> Result<usize, Error> {
        let size = self.encoded_size()?;
        let frame = out.get_mut(..size).ok_or(Error::OutputTooSmall)?;
        let (header, body) = frame.split_at_mut(4);
        let mut cursor = Writer { data: Some(body), pos: 0, order };
        self.write(&mut cursor)?;
        header.copy_from_slice(&[0, u8::from(order == Endian::Little), 0, 0]);
        Ok(size)
    }
}
