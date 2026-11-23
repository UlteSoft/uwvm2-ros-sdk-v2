// Package xcdr1 implements fixed-layout XCDR1 primitives for Unitree messages.
package xcdr1

import (
	"encoding/binary"
	"math"
)

// Stream operates on the body after the four-byte DDS encapsulation.
// Generated entry points check its exact size before accessing fields.
type Stream struct {
	Body  []byte
	Order binary.ByteOrder
	Read  bool
	pos   int
}

func (s *Stream) field(width int) []byte {
	start := (s.pos + width - 1) &^ (width - 1)
	s.pos = start + width
	return s.Body[start:s.pos]
}

func (s *Stream) Uint8(p *uint8) {
	b := s.field(1)
	if s.Read {
		*p = b[0]
	} else {
		b[0] = *p
	}
}

func (s *Stream) Uint16(p *uint16) {
	b := s.field(2)
	if s.Read {
		*p = s.Order.Uint16(b)
	} else {
		s.Order.PutUint16(b, *p)
	}
}

func (s *Stream) Uint32(p *uint32) {
	b := s.field(4)
	if s.Read {
		*p = s.Order.Uint32(b)
	} else {
		s.Order.PutUint32(b, *p)
	}
}

func (s *Stream) Int8(p *int8) {
	v := uint8(*p)
	s.Uint8(&v)
	if s.Read {
		*p = int8(v)
	}
}

func (s *Stream) Int16(p *int16) {
	v := uint16(*p)
	s.Uint16(&v)
	if s.Read {
		*p = int16(v)
	}
}

func (s *Stream) Int32(p *int32) {
	v := uint32(*p)
	s.Uint32(&v)
	if s.Read {
		*p = int32(v)
	}
}

func (s *Stream) Float32(p *float32) {
	v := math.Float32bits(*p)
	s.Uint32(&v)
	if s.Read {
		*p = math.Float32frombits(v)
	}
}
