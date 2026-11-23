// Package ros1 serializes complete ABB ROS 1 message, service request and
// successful service response bodies. Import a domain package for its generated
// record types, field documentation and connection-header identifiers.
package ros1

import (
	"encoding/binary"
	"errors"
	"math"
	"unsafe"
)

// Errors returned by the generated body codecs.
var (
	ErrNil         = errors.New("ros1: nil record")
	ErrLength      = errors.New("ros1: length exceeds uint32 or native int")
	ErrTruncated   = errors.New("ros1: truncated field")
	ErrTrailing    = errors.New("ros1: trailing bytes")
	ErrBoolean     = errors.New("ros1: boolean must be 0 or 1")
	ErrShortBuffer = errors.New("ros1: destination too short")
)

// Time stores the two unsigned words of a ROS 1 timestamp, in wire order.
// Both words are preserved exactly, including a non-normalized Nsec value.
type Time struct {
	Sec  uint32 `ros:"sec" json:"sec"`
	Nsec uint32 `ros:"nsec" json:"nsec"`
}

type mode uint8

const (
	measure mode = iota
	encode
	scan
	decode
)

const maxInt = int(^uint(0) >> 1)

// Stream visits the fields of one record in declaration order. Generated
// ROS1Fields methods use the same traversal for sizing, writing and reading.
// Applications normally call the methods on the enclosing record.
type Stream struct {
	mode mode
	data []byte
	pos  int
	err  error
}

func (s *Stream) take(n int) []byte {
	if s.err != nil {
		return nil
	}
	if n < 0 || n > maxInt-s.pos || uint64(s.pos)+uint64(n) > math.MaxUint32 {
		s.err = ErrLength
		return nil
	}
	start := s.pos
	if s.mode == measure {
		s.pos += n
		return nil
	}
	if n > len(s.data)-start {
		if s.mode == encode {
			s.err = ErrShortBuffer
		} else {
			s.err = ErrTruncated
		}
		return nil
	}
	s.pos += n
	return s.data[start:s.pos]
}

// Bool reads or writes a canonical one-byte ROS boolean.
func (s *Stream) Bool(v *bool) {
	b := s.take(1)
	if b == nil {
		return
	}
	if s.mode == encode {
		b[0] = 0
		if *v {
			b[0] = 1
		}
	} else if b[0] > 1 {
		s.err = ErrBoolean
	} else {
		*v = b[0] == 1
	}
}

// Uint8 reads or writes an unsigned byte.
func (s *Stream) Uint8(v *uint8) {
	if b := s.take(1); b != nil {
		if s.mode == encode {
			b[0] = *v
		} else {
			*v = b[0]
		}
	}
}

// Uint16 reads or writes two little-endian bytes.
func (s *Stream) Uint16(v *uint16) {
	if b := s.take(2); b != nil {
		if s.mode == encode {
			binary.LittleEndian.PutUint16(b, *v)
		} else {
			*v = binary.LittleEndian.Uint16(b)
		}
	}
}

// Uint32 reads or writes four little-endian bytes.
func (s *Stream) Uint32(v *uint32) {
	if b := s.take(4); b != nil {
		if s.mode == encode {
			binary.LittleEndian.PutUint32(b, *v)
		} else {
			*v = binary.LittleEndian.Uint32(b)
		}
	}
}

// Float32 preserves the IEEE-754 binary32 bit pattern.
func (s *Stream) Float32(v *float32) {
	if b := s.take(4); b != nil {
		if s.mode == encode {
			binary.LittleEndian.PutUint32(b, math.Float32bits(*v))
		} else {
			*v = math.Float32frombits(binary.LittleEndian.Uint32(b))
		}
	}
}

// Float64 preserves the IEEE-754 binary64 bit pattern.
func (s *Stream) Float64(v *float64) {
	if b := s.take(8); b != nil {
		if s.mode == encode {
			binary.LittleEndian.PutUint64(b, math.Float64bits(*v))
		} else {
			*v = math.Float64frombits(binary.LittleEndian.Uint64(b))
		}
	}
}

// Time reads or writes seconds followed by nanoseconds.
func (s *Stream) Time(v *Time) {
	s.Uint32(&v.Sec)
	s.Uint32(&v.Nsec)
}

func (s *Stream) putCount(n int) {
	if uint64(n) > math.MaxUint32 {
		s.err = ErrLength
		return
	}
	word := uint32(n)
	s.Uint32(&word)
}

func (s *Stream) count(minimum int) int {
	var word uint32
	s.Uint32(&word)
	if s.err != nil {
		return 0
	}
	if uint64(word) > uint64(maxInt) {
		s.err = ErrLength
		return 0
	}
	if uint64(word) > uint64((len(s.data)-s.pos)/minimum) {
		s.err = ErrTruncated
		return 0
	}
	return int(word)
}

// String preserves every byte, including embedded NULs. The decoded Go string
// owns its data independently of the serialized input.
func (s *Stream) String(v *string) {
	if s.mode == encode || s.mode == measure {
		s.putCount(len(*v))
		if b := s.take(len(*v)); b != nil {
			copy(b, *v)
		}
		return
	}
	n := s.count(1)
	b := s.take(n)
	if s.mode == decode && s.err == nil {
		*v = string(b)
	}
}

// Sequence visits a uint32-counted array. Every element type used by the ABB
// definitions has a positive minimum wire size. Generated code supplies that
// size and the element's own field traversal.
func Sequence[T any](s *Stream, values *[]T, minimum int, fields func(*T, *Stream)) {
	if s.err != nil {
		return
	}
	if s.mode == encode || s.mode == measure {
		s.putCount(len(*values))
		for i := 0; i < len(*values) && s.err == nil; i++ {
			fields(&(*values)[i], s)
		}
		return
	}
	if minimum <= 0 {
		s.err = ErrLength
		return
	}
	n := s.count(minimum)
	if n == 0 {
		return
	}
	var item T
	// sizeof includes Go string/slice headers and padding on this compiler.
	if width := uint64(unsafe.Sizeof(item)); width != 0 && uint64(n) > uint64(maxInt)/width {
		s.err = ErrLength
		return
	}
	if s.mode == scan {
		for i := 0; i < n && s.err == nil; i++ {
			fields(&item, s)
		}
		return
	}
	*values = make([]T, n)
	for i := range *values {
		fields(&(*values)[i], s)
	}
}

// Size computes the byte count of a complete generated record.
func Size[T any](v *T, fields func(*T, *Stream)) (int, error) {
	if v == nil {
		return 0, ErrNil
	}
	s := Stream{mode: measure}
	fields(v, &s)
	if s.err != nil {
		return 0, s.err
	}
	return s.pos, nil
}

// MarshalTo writes a complete body to dst and returns the number of bytes
// written. A short destination or an unrepresentable body leaves dst intact.
func MarshalTo[T any](v *T, dst []byte, fields func(*T, *Stream)) (int, error) {
	n, err := Size(v, fields)
	if err != nil {
		return 0, err
	}
	if len(dst) < n {
		return 0, ErrShortBuffer
	}
	s := Stream{mode: encode, data: dst[:n]}
	fields(v, &s)
	return s.pos, s.err
}

// Marshal allocates the exact number of bytes needed for a complete body.
func Marshal[T any](v *T, fields func(*T, *Stream)) ([]byte, error) {
	n, err := Size(v, fields)
	if err != nil {
		return nil, err
	}
	s := Stream{mode: encode, data: make([]byte, n)}
	fields(v, &s)
	return s.data, s.err
}

// Unmarshal verifies the complete body before allocating its strings and
// sequences. It assigns the receiver only after decoding all fields. Keep src
// stable until this call returns. The result then owns its dynamic fields.
func Unmarshal[T any](src []byte, v *T, fields func(*T, *Stream)) error {
	if v == nil {
		return ErrNil
	}
	if uint64(len(src)) > math.MaxUint32 {
		return ErrLength
	}
	var next T
	s := Stream{mode: scan, data: src}
	fields(&next, &s)
	if s.err != nil {
		return s.err
	}
	if s.pos != len(src) {
		return ErrTrailing
	}
	s.pos, s.mode = 0, decode
	fields(&next, &s)
	if s.err != nil {
		return s.err
	}
	*v = next
	return nil
}
