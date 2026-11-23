"""Plain XCDR1 messages for the pinned Unitree ROS 2 interfaces."""
from _struct import Struct
import sys

_FORMATS = dict(bool="B", int8="b", uint8="B", int16="h", uint16="H", int32="i",
                uint32="I", int64="q", uint64="Q", float32="f", float64="d")
_PRIMITIVES = {order: {kind: Struct(prefix + char) for kind, char in _FORMATS.items()}
               for order, prefix in (("little", "<"), ("big", ">"))}
_LIMIT = 4 * 1024 * 1024


class _Stream:
    def __init__(self, data, order, limit, reading):
        self.data = data
        self.formats = _PRIMITIVES[order]
        self.limit = limit
        self.reading = reading
        self.position = 4

    def extent(self, size, alignment):
        start = self.position + (-(self.position - 4) % alignment)
        end = start + size
        if end > self.limit:
            raise ValueError("CDR field exceeds the buffer limit")
        if not self.reading:
            self.data.extend(bytes(end - self.position))
        self.position = end
        return start

    def scalar(self, kind, value=None):
        fmt = self.formats[kind]
        at = self.extent(fmt.size, fmt.size)
        if self.reading:
            value = fmt.unpack_from(self.data, at)[0]
            if kind == "bool":
                if value > 1:
                    raise ValueError("invalid CDR boolean")
                return bool(value)
            return value
        if kind == "bool" and type(value) is not bool:
            raise TypeError("a bool field requires True or False")
        fmt.pack_into(self.data, at, value)

    def item(self, kind, types, value=None):
        if kind in self.formats:
            return self.scalar(kind, value)
        if kind == "string":
            if self.reading:
                size = self.scalar("uint32")
                at = self.extent(size, 1)
                if not size or self.data[at + size - 1] != 0:
                    raise ValueError("CDR string must include its NUL terminator")
                text = bytes(self.data[at:at + size - 1]).decode("utf-8")
                if "\x00" in text:
                    raise ValueError("embedded NUL in a ROS string")
                return text
            if not isinstance(value, str) or "\x00" in value:
                raise ValueError("expected UTF-8 text without embedded NUL")
            raw = value.encode("utf-8") + b"\0"
            self.scalar("uint32", len(raw))
            at = self.extent(len(raw), 1)
            self.data[at:at + len(raw)] = raw
            return
        cls = types[kind]
        if self.reading:
            value = cls.__new__(cls)
        elif not isinstance(value, cls):
            raise TypeError("expected a " + cls.__name__ + " field")
        self.fields(value)
        return value

    def fields(self, message):
        types = vars(sys.modules[type(message).__module__])
        for name, kind, count in message._fields:
            value = None if self.reading else getattr(message, name)
            if count is None:
                result = self.item(kind, types, value)
            elif self.reading:
                length = self.scalar("uint32") if count == -1 else count
                if length > self.limit - self.position:
                    raise ValueError("CDR sequence length exceeds available bytes")
                result = [self.item(kind, types) for _ in range(length)]
            else:
                length = len(value)
                if count == -1:
                    self.scalar("uint32", length)
                elif length != count:
                    raise ValueError(f"{name} requires exactly {count} elements")
                for item in value:
                    self.item(kind, types, item)
            if self.reading:
                setattr(message, name, result)


class Message:
    """A ROS message with named fields and plain CDR serialization in either byte order."""
    __slots__ = ()

    def __init__(self, **values):
        """Initialize named fields, allocating independent arrays and nested records."""
        types = vars(sys.modules[type(self).__module__])
        for name, kind, count in self._fields:
            if name in values:
                value = values.pop(name)
            else:
                ctor = (str if kind == "string" else bool if kind == "bool" else
                        float if kind.startswith("float") else int if kind in _FORMATS else types[kind])
                value = ctor() if count is None else [ctor() for _ in range(max(count, 0))]
            setattr(self, name, value)
        if values:
            raise TypeError("unknown ROS fields: " + ", ".join(values))

    def to_cdr(self, byteorder="little", *, limit=_LIMIT):
        """Serialize one full ROS message including its four-byte CDR encapsulation.

        Select little or big byte order. Fixed arrays require their declared extent.
        The limit covers the complete encoded sample, including alignment and header.
        """
        if byteorder not in _PRIMITIVES or limit < 4:
            raise ValueError("expected little or big byte order and space for a CDR header")
        data = bytearray((0, int(byteorder == "little"), 0, 0))
        _Stream(data, byteorder, limit, False).fields(self)
        return bytes(data)

    @classmethod
    def from_cdr(cls, data, *, limit=_LIMIT):
        """Decode one complete plain CDR_BE or CDR_LE sample into a new message.

        Truncation, unsupported encapsulation options and trailing bytes raise ValueError.
        No operation on guest or host resources is performed.
        """
        data = memoryview(data).cast("B")
        if (not 4 <= len(data) <= limit or data[0] or data[1] > 1 or data[2] or data[3]):
            raise ValueError("invalid plain CDR encapsulation or size")
        reader = _Stream(data, "little" if data[1] else "big", len(data), True)
        result = cls.__new__(cls)
        reader.fields(result)
        if reader.position != len(data):
            raise ValueError("trailing bytes in CDR message")
        return result
