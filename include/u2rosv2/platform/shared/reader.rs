//! Internal cursor shared by the selected no_std platform crate.
#[derive(Clone, Copy)]
pub struct Field(pub u8, pub i16, pub u8);

struct Cursor<'a> {
    data: &'a [u8],
    pos: usize,
    cdr: bool,
    big: bool,
}

fn word(data: &[u8], big: bool) -> u64 {
    let mut value = 0;
    for (i, &byte) in data.iter().enumerate() {
        let shift = if big { data.len() - 1 - i } else { i };
        value |= u64::from(byte) << (8 * shift);
    }
    value
}

impl<'a> Cursor<'a> {
    fn take(&mut self, count: usize, width: usize) -> Option<&'a [u8]> {
        let pad = if self.cdr { self.pos.wrapping_neg() & (width - 1) } else { 0 };
        let start = self.pos.checked_add(pad)?;
        let end = start.checked_add(count.checked_mul(width)?)?;
        let result = self.data.get(start..end)?;
        self.pos = end;
        Some(result)
    }

    fn count(&mut self) -> Option<usize> {
        let bytes = self.take(1, 4)?;
        Some(word(bytes, self.big) as usize)
    }

    fn strings(&mut self, count: usize) -> Option<()> {
        if count > (self.data.len() - self.pos) / 4 { return None; }
        for _ in 0..count {
            let size = self.count()?;
            let bytes = self.take(size, 1)?;
            if self.cdr && bytes.last() != Some(&0) { return None; }
        }
        Some(())
    }
}

/// Fixed widths, ROS counted sequences/strings, or the vendor's declared packed array.
pub fn project(data: &[u8], format: u8, fields: &[Field], wanted: usize, index: usize) -> Option<u64> {
    let cdr = format == 1 || (format == 3 && data.len() != 32);
    let (bytes, big, tail) = if cdr {
        let hdr = data.get(..4)?;
        if hdr[0] != 0 || hdr[1] > 1 || hdr[2] != 0 || hdr[3] > 3 { return None; }
        (&data[4..], hdr[1] == 0, usize::from(hdr[3]))
    } else if format == 2 {
        if data.get(..8)? != &0x4abec52f17edd11fu64.to_be_bytes()[..] { return None; }
        (&data[8..], true, 0)
    } else {
        (data, false, 0)
    };
    let mut r = Cursor { data: bytes, pos: 0, cdr, big };
    let mut saved = 0;
    let mut result = None;
    for (j, &Field(width, repeat, kind)) in fields.iter().enumerate() {
        let width = usize::from(width);
        let count = match repeat {
            1.. => repeat as usize,
            0 => r.count()?,
            -1 => saved,
            _ => {
                let remaining = r.data.len() - r.pos;
                if remaining % ((-1 - repeat) as usize * width) != 0 { return None; }
                remaining / width
            }
        };
        if width == 0 {
            r.strings(count)?;
        } else if count != 0 {
            let bytes = r.take(count, width)?;
            if kind == 2 {
                saved = word(bytes, big) as usize;
                if saved > i32::MAX as usize { return None; }
            } else if kind == 1 && bytes.iter().any(|&v| v > 1) {
                return None;
            }
            if j == wanted && index < count {
                let start = index * width;
                result = Some(word(&bytes[start..start + width], big));
            }
        }
    }
    let left = bytes.len() - r.pos;
    if (left != 0 && left != tail) || (tail != 0 && tail != (r.pos.wrapping_neg() & 3)) { return None; }
    result
}
