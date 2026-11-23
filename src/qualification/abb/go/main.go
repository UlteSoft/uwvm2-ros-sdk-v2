package main

import (
	"bytes"
	"encoding"
	"encoding/binary"
	"math"
	"reflect"
	"unsafe"

	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1/abbegmmsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1/abbrapidmsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1/abbrobotmsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1/stdmsgs"
)

type body interface {
	encoding.BinaryMarshaler
	encoding.BinaryUnmarshaler
	MarshalROS1([]byte) (int, error)
	UnmarshalROS1([]byte) error
	ROS1Size() (int, error)
	ROS1Type() string
	ROS1MD5() string
}

type badField struct {
	offset int
	boolean bool
}

var checkedTypes, checkedFields, vectors, empties, prefixes, badFields, tails int

func need(ok bool, label, behavior string) {
	if !ok {
		println("FAIL", label, behavior)
		panic(behavior)
	}
}

func checkType(sample body, wantType, wantMD5, constType, constMD5 string, min, size int, names, types []string) {
	need(sample.ROS1Type() == wantType && constType == wantType, wantType, "ROS1 type")
	need(sample.ROS1MD5() == wantMD5 && constMD5 == wantMD5, wantType, "ROS1 MD5")
	need(min == size, wantType, "minimum wire size")
	shape := reflect.TypeOf(sample).Elem()
	need(shape.NumField() == len(names), wantType, "public Go field count")
	for i, name := range names {
		field := shape.Field(i)
		need(field.Tag.Get("ros") == name && field.Tag.Get("json") == name, wantType, "struct tag "+name)
		t := field.Type
		actual := ""
		if t.Kind() == reflect.Slice {
			actual = "[]"
			t = t.Elem()
		}
		if path := t.PkgPath(); path != "" {
			end := len(path)-1
			for path[end] != '/' {
				end--
			}
			actual += path[end+1:] + "."
		}
		actual += t.Name()
		need(actual == types[i], wantType, "public Go field type "+name)
		checkedFields++
	}
	checkedTypes++
}

func equalFields(a, b reflect.Value) bool {
	switch a.Kind() {
	case reflect.Struct:
		for i := 0; i < a.NumField(); i++ {
			if !equalFields(a.Field(i), b.Field(i)) {
				return false
			}
		}
		return true
	case reflect.Slice:
		if a.IsNil() != b.IsNil() || a.Len() != b.Len() {
			return false
		}
		for i := 0; i < a.Len(); i++ {
			if !equalFields(a.Index(i), b.Index(i)) {
				return false
			}
		}
		return true
	case reflect.Bool:
		return a.Bool() == b.Bool()
	case reflect.Uint8, reflect.Uint16, reflect.Uint32:
		return a.Uint() == b.Uint()
	case reflect.Float32:
		return math.Float32bits(float32(a.Float())) == math.Float32bits(float32(b.Float()))
	case reflect.Float64:
		return math.Float64bits(a.Float()) == math.Float64bits(b.Float())
	case reflect.String:
		return a.String() == b.String()
	default:
		panic("unrecognized type in fixed schema")
	}
}

func same(actual, expected body) bool {
	return equalFields(reflect.ValueOf(actual).Elem(), reflect.ValueOf(expected).Elem())
}

func verifyVector(label string, received, want body, raw []byte, invalid []badField) {
	n, err := want.ROS1Size()
	need(err == nil && n == len(raw), label, "exact size")
	first, err := want.MarshalBinary()
	need(err == nil && bytes.Equal(first, raw), label, "MarshalBinary genpy bytes")
	second, err := want.MarshalBinary()
	need(err == nil && bytes.Equal(second, raw), label, "repeat MarshalBinary genpy bytes")
	if len(first) > 0 {
		first[0] ^= 0xff
	}
	need(bytes.Equal(second, raw), label, "allocated outputs do not alias")
	output := bytes.Repeat([]byte{0xac}, len(raw)+8)
	written, err := want.MarshalROS1(output)
	need(err == nil && written == len(raw) && bytes.Equal(output[:written], raw), label, "MarshalROS1 genpy bytes")
	need(bytes.Equal(output[written:], []byte{0xac, 0xac, 0xac, 0xac, 0xac, 0xac, 0xac, 0xac}),
		label, "MarshalROS1 preserves suffix")
	if n == 0 {
		empties++
		written, err = want.MarshalROS1(nil)
		need(written == 0 && err == nil && received.UnmarshalROS1(nil) == nil, label, "empty nil input and output")
	} else {
		short := bytes.Repeat([]byte{0xca}, n-1)
		written, err = want.MarshalROS1(short)
		need(err == ros1.ErrShortBuffer && written == 0 &&
			bytes.Equal(short, bytes.Repeat([]byte{0xca}, n-1)), label, "short destination unchanged")
	}
	need(received.UnmarshalBinary(output[:n]) == nil && same(received, want), label, "UnmarshalBinary typed values")
	for i := range output {
		output[i] = 0xfe
	}
	need(same(received, want), label, "UnmarshalBinary owns decoded fields")
	input := append([]byte(nil), raw...)
	need(received.UnmarshalROS1(input) == nil && same(received, want), label, "UnmarshalROS1 typed values")
	for i := range input {
		input[i] = 0xfe
	}
	need(same(received, want), label, "UnmarshalROS1 owns decoded fields")
	for i := range raw {
		need(received.UnmarshalROS1(raw[:i]) == ros1.ErrTruncated && same(received, want),
			label, "ROS1 truncated prefix preserves receiver")
		need(received.UnmarshalBinary(raw[:i]) == ros1.ErrTruncated && same(received, want),
			label, "Binary truncated prefix preserves receiver")
		prefixes++
	}
	tail := append(append([]byte(nil), raw...), 0xde, 0xad)
	need(received.UnmarshalROS1(tail) == ros1.ErrTrailing && same(received, want), label, "ROS1 trailing bytes preserve receiver")
	need(received.UnmarshalBinary(tail) == ros1.ErrTrailing && same(received, want), label, "Binary trailing bytes preserve receiver")
	tails++
	for _, spot := range invalid {
		copy(input, raw)
		expected := ros1.ErrTruncated
		if spot.boolean {
			input[spot.offset] = 2
			expected = ros1.ErrBoolean
		} else {
			binary.LittleEndian.PutUint32(input[spot.offset:], 0x44444444)
		}
		need(received.UnmarshalROS1(input) == expected && same(received, want), label, "bad bool or length preserves receiver")
		badFields++
	}
	vectors++
}

func extra() {
	const label = "supplemental wire edge"
	var actual stdmsgs.Header
	expected := stdmsgs.Header{
		Seq: 0xfeffaacc,
		Stamp: ros1.Time{Sec: 0xfedcba98, Nsec: 0xffffffff},
		FrameID: "\x00\xff\x80\x00\xc0",
	}
	raw := []byte{0xcc, 0xaa, 0xff, 0xfe, 0x98, 0xba, 0xdc, 0xfe, 0xff, 0xff, 0xff, 0xff, 5, 0, 0, 0, 0, 0xff, 0x80, 0, 0xc0}
	need(actual.UnmarshalROS1(raw) == nil && actual == expected, label, "binary string and unnormalized timestamp")
	out, err := expected.MarshalBinary()
	need(err == nil && bytes.Equal(out, raw), label, "binary string encoding and time raw words")
	binary.LittleEndian.PutUint32(raw[12:], 0xffffffff)
	wordSize := unsafe.Sizeof(int(0))
	var overflow = ros1.ErrTruncated
	if wordSize == 4 {
		overflow = ros1.ErrLength
	}
	need(actual.UnmarshalROS1(raw) == overflow && actual == expected, label, "uint32 count boundary")
	for i, tag := range []string{"sec", "nsec"} {
		field := reflect.TypeOf(ros1.Time{}).Field(i)
		need(field.Tag.Get("ros") == tag && field.Tag.Get("json") == tag && field.Type.Kind() == reflect.Uint32,
			label, "Time public tags")
	}
	var state, noChannels abbegmmsgs.EGMState
	state.EGMChannels = []abbegmmsgs.EGMChannelState{}
	withEmpty, err := state.MarshalBinary()
	need(err == nil, label, "explicit empty slice")
	withNil, err := noChannels.MarshalBinary()
	need(err == nil && bytes.Equal(withEmpty, withNil), label, "nil and explicit empty slice equivalence")
	state.EGMChannels = []abbegmmsgs.EGMChannelState{{Name: "prior"}}
	need(state.UnmarshalROS1(withNil) == nil && state.EGMChannels == nil, label, "empty sequence decodes to nil")
	var pos abbrapidmsgs.Pos
	floatRaw := []byte{1, 0, 0xc0, 0x7f, 0, 0, 0x80, 0x7f, 0, 0, 0x80, 0xff}
	need(pos.UnmarshalROS1(floatRaw) == nil, label, "IEEE nonfinite decode")
	need(math.Float32bits(pos.X) == 0x7fc00001 && math.Float32bits(pos.Y) == 0x7f800000 &&
		math.Float32bits(pos.Z) == 0xff800000, label, "IEEE nonfinite bits")
	out, err = pos.MarshalBinary()
	need(err == nil && bytes.Equal(out, floatRaw), label, "IEEE nonfinite encode")
	var empty *abbrobotmsgs.ServiceResponses
	_, err = empty.ROS1Size()
	need(err == ros1.ErrNil, label, "nil size")
	_, err = empty.MarshalBinary()
	need(err == ros1.ErrNil, label, "nil allocation")
	_, err = empty.MarshalROS1(nil)
	need(err == ros1.ErrNil && empty.UnmarshalROS1(nil) == ros1.ErrNil && empty.UnmarshalBinary(nil) == ros1.ErrNil,
		label, "nil receiver rejected")
	println("WIRE EDGE OK int-bytes", wordSize, "uintptr-bytes", unsafe.Sizeof(uintptr(0)))
}

func main() {
	runVectors()
	extra()
	println("ABB WIRE VERIFIED", "types", checkedTypes, "fields", checkedFields, "vectors", vectors,
		"empty", empties, "prefixes", prefixes, "invalid", badFields, "tails", tails)
}
