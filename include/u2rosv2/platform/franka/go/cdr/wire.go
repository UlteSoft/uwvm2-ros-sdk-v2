// Package cdr serializes complete ROS 2 XCDRv1 PLAIN_CDR samples. The domain
// packages provide concrete Franka and Jazzy records. Each sample has one
// encapsulation header and one alignment origin shared by all nested values.
package cdr

import (
	"errors"
	"math"
	"unsafe"
)

// Endian is the plain-CDR representation identifier in the second header octet.
type Endian uint8

const (
	BigEndian Endian = iota
	LittleEndian
)

// Unbounded is the largest count representable by a ROS sequence length word.
const Unbounded uint32 = math.MaxUint32

// Errors distinguish malformed wire data, schema bounds and caller buffer limits.
var (
	ErrNil           = errors.New("cdr: nil record")
	ErrEncapsulation = errors.New("cdr: invalid PLAIN_CDR identifier or options")
	ErrPadding       = errors.New("cdr: inconsistent transport padding count")
	ErrTrailing      = errors.New("cdr: trailing bytes")
	ErrTruncated     = errors.New("cdr: truncated sample")
	ErrBoolean       = errors.New("cdr: boolean must be 0 or 1")
	ErrString        = errors.New("cdr: string requires a counted terminal NUL")
	ErrBound         = errors.New("cdr: sequence exceeds its declared bound")
	ErrLength        = errors.New("cdr: length is not representable")
	ErrShortBuffer   = errors.New("cdr: destination too short")
)

type mode uint8

const (
	measure mode = iota
	encode
	scan
	decode
)

const maxInt = int(^uint(0) >> 1)

// Stream is the cursor used by generated CDRFields methods. Its position starts
// at the first byte following the encapsulation header. A nested record, fixed
// array or sequence continues at the parent's current position.
type Stream struct {
	mode  mode
	order Endian
	body  []byte
	pos   int
	err   error
}

func (s *Stream) reading() bool { return s.mode == scan || s.mode == decode }

func (s *Stream) take(n, align int) []byte {
	if s.err != nil {
		return nil
	}
	pad := -s.pos & (align - 1)
	// Reserve four bytes for the header even on a 32-bit TinyGo guest.
	room := maxInt - 4 - s.pos
	if n < 0 || pad > room || n > room-pad {
		s.err = ErrLength
		return nil
	}
	start := s.pos + pad
	end := start + n
	if s.mode == measure {
		s.pos = end
		return nil
	}
	if end > len(s.body) {
		if s.mode == encode {
			s.err = ErrShortBuffer
		} else {
			s.err = ErrTruncated
		}
		return nil
	}
	if s.mode == encode {
		for i := s.pos; i < start; i++ {
			s.body[i] = 0
		}
	}
	s.pos = end
	return s.body[start:end]
}

func (s *Stream) word(width int, value uint64) uint64 {
	b := s.take(width, width)
	if b == nil {
		return 0
	}
	if s.mode == encode {
		for i := range b {
			index := i
			if s.order == BigEndian {
				index = width - 1 - i
			}
			b[index] = byte(value)
			value >>= 8
		}
		return 0
	}
	var bits uint64
	for i := range b {
		index := i
		if s.order == LittleEndian {
			index = width - 1 - i
		}
		bits = (bits << 8) | uint64(b[index])
	}
	return bits
}

func integer[T ~uint8 | ~int8 | ~uint32 | ~int32 | ~int64](s *Stream, v *T, width int) {
	bits := s.word(width, uint64(*v))
	if s.reading() {
		*v = T(bits)
	}
}

// Bool encodes a single octet and rejects wire values greater than one.
func (s *Stream) Bool(v *bool) {
	var bits uint64
	if *v {
		bits = 1
	}
	bits = s.word(1, bits)
	if s.reading() && s.err == nil {
		if bits > 1 {
			s.err = ErrBoolean
			return
		}
		*v = bits != 0
	}
}

// Uint8 transfers one unsigned octet, including ROS char and empty-record placeholders.
func (s *Stream) Uint8(v *uint8) { integer(s, v, 1) }

// Int8 transfers one signed octet.
func (s *Stream) Int8(v *int8) { integer(s, v, 1) }

// Uint32 transfers an unsigned four-byte word aligned relative to the payload.
func (s *Stream) Uint32(v *uint32) { integer(s, v, 4) }

// Int32 transfers a signed four-byte word.
func (s *Stream) Int32(v *int32) { integer(s, v, 4) }

// Int64 transfers a signed eight-byte word.
func (s *Stream) Int64(v *int64) { integer(s, v, 8) }

// Float64 preserves the IEEE-754 binary64 bit pattern, including signed zeros and NaNs.
func (s *Stream) Float64(v *float64) {
	bits := s.word(8, math.Float64bits(*v))
	if s.reading() {
		*v = math.Float64frombits(bits)
	}
}

// String preserves every content octet in an owned Go string. The uint32
// byte count includes the final NUL. Embedded NULs are ordinary content bytes.
func (s *Stream) String(v *string) {
	if s.err != nil {
		return
	}
	if !s.reading() {
		if len(*v) == maxInt || uint64(len(*v)) >= math.MaxUint32 {
			s.err = ErrLength
			return
		}
		n := len(*v) + 1
		s.word(4, uint64(n))
		if b := s.take(n, 1); b != nil {
			copy(b, *v)
			b[n-1] = 0
		}
		return
	}
	n := s.word(4, 0)
	if s.err != nil {
		return
	}
	if n == 0 {
		s.err = ErrString
		return
	}
	if n > uint64(maxInt) {
		s.err = ErrLength
		return
	}
	b := s.take(int(n), 1)
	if s.err != nil {
		return
	}
	if b[len(b)-1] != 0 {
		s.err = ErrString
		return
	}
	if s.mode == decode {
		*v = string(b[:len(b)-1])
	}
}

// Sequence visits a uint32 count and the corresponding elements. Generated
// callers supply the schema bound and a positive lower bound on the wire size
// of an element. The scan pass checks all nested lengths and terminators before
// the decode pass allocates owned slices.
func Sequence[T any](s *Stream, items *[]T, bound uint32, minimum int, visit func(*T, *Stream)) {
	if s.err != nil {
		return
	}
	if !s.reading() {
		n := uint64(len(*items))
		if n > math.MaxUint32 {
			s.err = ErrLength
			return
		}
		if n > uint64(bound) {
			s.err = ErrBound
			return
		}
		s.word(4, n)
		for i := 0; i < len(*items) && s.err == nil; i++ {
			visit(&(*items)[i], s)
		}
		return
	}
	n := s.word(4, 0)
	if s.err != nil {
		return
	}
	if n > uint64(bound) {
		s.err = ErrBound
		return
	}
	if n > uint64(maxInt) || minimum <= 0 {
		s.err = ErrLength
		return
	}
	if n > uint64((len(s.body)-s.pos)/minimum) {
		s.err = ErrTruncated
		return
	}
	var element T
	if width := uint64(unsafe.Sizeof(element)); width != 0 && n > uint64(maxInt)/width {
		s.err = ErrLength
		return
	}
	if s.mode == scan {
		for i := 0; i < int(n) && s.err == nil; i++ {
			visit(&element, s)
		}
		return
	}
	if n == 0 {
		*items = nil
		return
	}
	*items = make([]T, int(n))
	for i := range *items {
		visit(&(*items)[i], s)
		if s.err != nil {
			return
		}
	}
}

// Size returns the exact size of an encapsulated sample, including its header.
func Size[T any](v *T, visit func(*T, *Stream)) (int, error) {
	if v == nil {
		return 0, ErrNil
	}
	s := Stream{mode: measure}
	visit(v, &s)
	if s.err != nil {
		return 0, s.err
	}
	return 4 + s.pos, nil
}

func writeFrame[T any](v *T, order Endian, dst []byte, visit func(*T, *Stream)) (int, error) {
	s := Stream{mode: encode, order: order, body: dst[4:]}
	visit(v, &s)
	if s.err != nil {
		return 0, s.err
	}
	dst[0], dst[1], dst[2], dst[3] = 0, byte(order), 0, 0
	return 4 + s.pos, nil
}

// MarshalTo checks the source and destination capacity before writing. Keep v
// stable and dst disjoint from the source fields throughout the call.
func MarshalTo[T any](v *T, order Endian, dst []byte, visit func(*T, *Stream)) (int, error) {
	if order > LittleEndian {
		return 0, ErrEncapsulation
	}
	n, err := Size(v, visit)
	if err != nil {
		return 0, err
	}
	if len(dst) < n {
		return 0, ErrShortBuffer
	}
	return writeFrame(v, order, dst[:n], visit)
}

// Marshal allocates exactly one destination frame in the requested byte order.
func Marshal[T any](v *T, order Endian, visit func(*T, *Stream)) ([]byte, error) {
	if order > LittleEndian {
		return nil, ErrEncapsulation
	}
	n, err := Size(v, visit)
	if err != nil {
		return nil, err
	}
	frame := make([]byte, n)
	if _, err := writeFrame(v, order, frame, visit); err != nil {
		return nil, err
	}
	return frame, nil
}

func readFrame[T any](src []byte, v *T, pass mode, visit func(*T, *Stream)) error {
	if len(src) < 4 {
		return ErrTruncated
	}
	if src[0] != 0 || src[1] > 1 || src[2] != 0 || src[3] > 3 {
		return ErrEncapsulation
	}
	s := Stream{mode: pass, order: Endian(src[1]), body: src[4:]}
	visit(v, &s)
	if s.err != nil {
		return s.err
	}
	tail := int(src[3])
	if tail != 0 && tail != (-s.pos&3) {
		return ErrPadding
	}
	remaining := len(s.body) - s.pos
	if remaining != 0 && remaining != tail {
		return ErrTrailing
	}
	return nil
}

// Validate checks all nested fields, bounds and transport padding without
// allocating strings or element slices from the incoming lengths.
func Validate[T any](src []byte, visit func(*T, *Stream)) error {
	var scratch T
	return readFrame(src, &scratch, scan, visit)
}

// Unmarshal checks the complete sample before materializing owned fields.
// Keep src stable until return. Success replaces v, and failure preserves v.
func Unmarshal[T any](src []byte, v *T, visit func(*T, *Stream)) error {
	if v == nil {
		return ErrNil
	}
	var next T
	if err := readFrame(src, &next, scan, visit); err != nil {
		return err
	}
	if err := readFrame(src, &next, decode, visit); err != nil {
		return err
	}
	*v = next
	return nil
}
