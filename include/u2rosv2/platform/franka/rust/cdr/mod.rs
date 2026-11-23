//! Encapsulated XCDRv1 PLAIN_CDR for the frozen ROS 2 Franka interfaces.
//! Decoding borrows immutable input. Encoding writes into caller-owned storage.
//! Creating or decoding a request does not grant authority to contact a service or robot.
#![allow(non_camel_case_types)]

use core::convert::{TryFrom, TryInto};

pub mod action_msgs;
pub mod builtin_interfaces;
pub mod franka_msgs;
pub mod franka_spine_msgs;
pub mod geometry_msgs;
pub mod sensor_msgs;
pub mod service_msgs;
pub mod std_msgs;
pub mod unique_identifier_msgs;

/// Representation identifier in the encapsulation header.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Endian {
    Big,
    Little,
}

/// Structural or capacity error detected while processing a frame.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Error {
    Encapsulation,
    Truncated,
    TrailingBytes,
    InvalidPadding,
    InvalidBoolean,
    InvalidString,
    SequenceBound,
    LengthOverflow,
    OutputTooSmall,
}

/// Bounded cursor. Nested records and sequence iterators preserve its payload-relative alignment.
#[derive(Clone, Copy)]
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

    fn take(&mut self, n: usize) -> Result<&'a [u8], Error> {
        let end = self.pos.checked_add(n).ok_or(Error::LengthOverflow)?;
        let bytes = self.data.get(self.pos..end).ok_or(Error::Truncated)?;
        self.pos = end;
        Ok(bytes)
    }

    fn word<const N: usize>(&mut self) -> Result<[u8; N], Error> {
        self.take(self.pos.wrapping_neg() & (N - 1))?;
        self.take(N)?.try_into().map_err(|_| Error::Truncated)
    }
}

/// Framing and measurement share the same writing path. A measuring writer owns no buffer.
pub struct Writer<'a> {
    data: Option<&'a mut [u8]>,
    pos: usize,
    order: Endian,
}

impl Writer<'_> {
    fn raw(&mut self, value: &[u8]) -> Result<(), Error> {
        let end = self.pos.checked_add(value.len()).ok_or(Error::LengthOverflow)?;
        if let Some(data) = self.data.as_mut() {
            data.get_mut(self.pos..end).ok_or(Error::OutputTooSmall)?.copy_from_slice(value);
        }
        self.pos = end;
        Ok(())
    }

    fn word<const N: usize>(&mut self, bytes: &[u8; N]) -> Result<(), Error> {
        let pad = self.pos.wrapping_neg() & (N - 1);
        self.raw(&[0; 7][..pad])?;
        self.raw(bytes)
    }
}

/// Operations on a single field at the current alignment origin.
pub trait CdrValue<'a>: Copy {
    /// Lower bound for one serialized value, excluding alignment padding.
    const MIN_SIZE: usize;
    fn read(r: &mut Reader<'a>) -> Result<Self, Error>;
    fn write(&self, w: &mut Writer<'_>) -> Result<(), Error>;
}

macro_rules! scalar {
    ($t:ty, $width:literal) => {
        impl<'a> CdrValue<'a> for $t {
            const MIN_SIZE: usize = $width;
            fn read(r: &mut Reader<'a>) -> Result<Self, Error> {
                let bytes = r.word::<$width>()?;
                Ok(match r.order {
                    Endian::Big => Self::from_be_bytes(bytes),
                    Endian::Little => Self::from_le_bytes(bytes),
                })
            }
            fn write(&self, w: &mut Writer<'_>) -> Result<(), Error> {
                let bytes = match w.order {
                    Endian::Big => self.to_be_bytes(),
                    Endian::Little => self.to_le_bytes(),
                };
                w.word(&bytes)
            }
        }
    };
}
scalar!(u8, 1);
scalar!(i8, 1);
scalar!(u32, 4);
scalar!(i32, 4);
scalar!(i64, 8);
scalar!(f64, 8);

impl<'a> CdrValue<'a> for bool {
    const MIN_SIZE: usize = 1;
    fn read(r: &mut Reader<'a>) -> Result<Self, Error> {
        match u8::read(r)? {
            0 => Ok(false),
            1 => Ok(true),
            _ => Err(Error::InvalidBoolean),
        }
    }
    fn write(&self, w: &mut Writer<'_>) -> Result<(), Error> { u8::from(*self).write(w) }
}

impl<'a> CdrValue<'a> for &'a [u8] {
    const MIN_SIZE: usize = 5;
    fn read(r: &mut Reader<'a>) -> Result<Self, Error> {
        let count = u32::read(r)? as usize;
        let value = r.take(count)?;
        value.strip_suffix(&[0]).ok_or(Error::InvalidString)
    }
    fn write(&self, w: &mut Writer<'_>) -> Result<(), Error> {
        let count = u32::try_from(self.len()).ok().and_then(|n| n.checked_add(1)).ok_or(Error::LengthOverflow)?;
        count.write(w)?;
        w.raw(self)?;
        w.raw(&[0])
    }
}

impl<'a, T: CdrValue<'a> + Default, const N: usize> CdrValue<'a> for [T; N] {
    const MIN_SIZE: usize = N * T::MIN_SIZE;
    fn read(r: &mut Reader<'a>) -> Result<Self, Error> {
        let mut items = [T::default(); N];
        for item in &mut items { *item = T::read(r)?; }
        Ok(items)
    }
    fn write(&self, w: &mut Writer<'_>) -> Result<(), Error> {
        for item in self { item.write(w)?; }
        Ok(())
    }
}

#[derive(Clone, Copy)]
enum Storage<'a, T> {
    Values(&'a [T]),
    Wire(Reader<'a>),
}

/// A sequence borrowed from a typed slice or a fully validated immutable frame.
#[derive(Clone, Copy)]
pub struct Sequence<'a, T> {
    storage: Storage<'a, T>,
    count: usize,
}

impl<'a, T> Sequence<'a, T> {
    pub fn from_values(values: &'a [T]) -> Self {
        Self { storage: Storage::Values(values), count: values.len() }
    }
    pub fn len(&self) -> usize { self.count }
    pub fn is_empty(&self) -> bool { self.count == 0 }
}

impl<T> Default for Sequence<'_, T> {
    fn default() -> Self { Self::from_values(&[]) }
}

/// Iteration keeps the original CDR alignment origin and endian selection.
pub struct Iter<'a, T>(Sequence<'a, T>);

impl<'a, T: CdrValue<'a>> Iterator for Iter<'a, T> {
    type Item = T;
    fn next(&mut self) -> Option<T> {
        if self.0.count == 0 { return None; }
        let value = match &mut self.0.storage {
            Storage::Values(values) => {
                let (first, rest) = values.split_first()?;
                *values = rest;
                *first
            }
            Storage::Wire(r) => T::read(r).ok()?,
        };
        self.0.count -= 1;
        Some(value)
    }
    fn size_hint(&self) -> (usize, Option<usize>) { (self.0.count, Some(self.0.count)) }
}

impl<'a, T: CdrValue<'a>> Sequence<'a, T> {
    pub fn iter(&self) -> Iter<'a, T> { Iter(*self) }

    fn read_bounded(r: &mut Reader<'a>, bound: u32) -> Result<Self, Error> {
        let count = u32::read(r)?;
        if count > bound { return Err(Error::SequenceBound); }
        let count = count as usize;
        if count != 0 && (T::MIN_SIZE == 0 || count > (r.data.len() - r.pos) / T::MIN_SIZE) {
            return Err(Error::Truncated);
        }
        let mut start = *r;
        for _ in 0..count { T::read(r)?; }
        start.data = &start.data[..r.pos];
        Ok(Self { storage: Storage::Wire(start), count })
    }

    fn write_bounded(&self, w: &mut Writer<'_>, bound: u32) -> Result<(), Error> {
        let count = u32::try_from(self.count).map_err(|_| Error::LengthOverflow)?;
        if count > bound { return Err(Error::SequenceBound); }
        count.write(w)?;
        let mut iter = self.iter();
        for _ in 0..count {
            iter.next().ok_or(Error::Truncated)?.write(w)?;
        }
        Ok(())
    }
}

impl<'a, T: CdrValue<'a>> CdrValue<'a> for Sequence<'a, T> {
    const MIN_SIZE: usize = 4;
    fn read(r: &mut Reader<'a>) -> Result<Self, Error> { Self::read_bounded(r, u32::MAX) }
    fn write(&self, w: &mut Writer<'_>) -> Result<(), Error> { self.write_bounded(w, u32::MAX) }
}

/// Top-level operations on a complete encapsulated message. All variable-length fields borrow their input.
pub trait Message<'a>: CdrValue<'a> {
    const TYPE: &'static str;

    fn decode(frame: &'a [u8]) -> Result<Self, Error> {
        let mut r = Reader::frame(frame)?;
        let value = Self::read(&mut r)?;
        r.finish()?;
        Ok(value)
    }
    fn validate(frame: &'a [u8]) -> Result<(), Error> { Self::decode(frame).map(|_| ()) }

    fn encoded_size(&self) -> Result<usize, Error> {
        let mut measure = Writer { data: None, pos: 0, order: Endian::Little };
        self.write(&mut measure)?;
        measure.pos.checked_add(4).ok_or(Error::LengthOverflow)
    }
    fn encode(&self, order: Endian, out: &mut [u8]) -> Result<usize, Error> {
        let size = self.encoded_size()?;
        let frame = out.get_mut(..size).ok_or(Error::OutputTooSmall)?;
        let (header, body) = frame.split_at_mut(4);
        let mut w = Writer { data: Some(body), pos: 0, order };
        self.write(&mut w)?;
        header.copy_from_slice(&[0, u8::from(order == Endian::Little), 0, 0]);
        Ok(size)
    }
}

/// Rosidl service and its request, response and introspection samples.
pub trait Service {
    const TYPE: &'static str;
    type Request<'a>: Message<'a>;
    type Response<'a>: Message<'a>;
    type Event<'a>: Message<'a>;
}

/// Rosidl action and its goal, result, feedback and communication envelopes.
pub trait Action {
    const TYPE: &'static str;
    type Goal<'a>: Message<'a>;
    type Result<'a>: Message<'a>;
    type Feedback<'a>: Message<'a>;
    type FeedbackMessage<'a>: Message<'a>;
    type SendGoal: Service;
    type GetResult: Service;
}
