// Code generated from Unitree ROS 2 v0.3.0 .msg files by generate_go.py. DO NOT EDIT.

package unitreehg

import (
	"encoding/binary"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/unitree/internal/xcdr1"
)

// LowStateCDRSize includes the four-byte plain CDR encapsulation header.
const LowStateCDRSize = 2092

// MarshalCDR writes one complete LowState in the selected byte order.
// It returns false for a nil receiver, short destination or unsupported byte order.
func (m *LowState) MarshalCDR(dst []byte, order binary.ByteOrder) bool {
	if m == nil || len(dst) < LowStateCDRSize || (order != binary.LittleEndian && order != binary.BigEndian) {
		return false
	}
	dst = dst[:LowStateCDRSize]
	clear(dst)
	if order == binary.LittleEndian {
		dst[1] = 1
	}
	m.cdr(&xcdr1.Stream{Body: dst[4:], Order: order})
	return true
}

// UnmarshalCDR decodes a complete CDR_BE or CDR_LE payload with zero
// encapsulation options. A rejected header or length leaves m untouched.
func (m *LowState) UnmarshalCDR(src []byte) bool {
	if m == nil || len(src) != LowStateCDRSize || src[0] != 0 || src[1] > 1 || src[2] != 0 || src[3] != 0 {
		return false
	}
	var order binary.ByteOrder = binary.BigEndian
	if src[1] == 1 {
		order = binary.LittleEndian
	}
	m.cdr(&xcdr1.Stream{Body: src[4:], Order: order, Read: true})
	return true
}

func (m *IMUState) cdr(s *xcdr1.Stream) {
	for i := range m.Quaternion {
		s.Float32(&m.Quaternion[i])
	}
	for i := range m.Gyroscope {
		s.Float32(&m.Gyroscope[i])
	}
	for i := range m.Accelerometer {
		s.Float32(&m.Accelerometer[i])
	}
	for i := range m.RPY {
		s.Float32(&m.RPY[i])
	}
	s.Int16(&m.Temperature)
}

func (m *LowState) cdr(s *xcdr1.Stream) {
	for i := range m.Version {
		s.Uint32(&m.Version[i])
	}
	s.Uint8(&m.ModePr)
	s.Uint8(&m.ModeMachine)
	s.Uint32(&m.Tick)
	m.IMUState.cdr(s)
	for i := range m.MotorState {
		m.MotorState[i].cdr(s)
	}
	for i := range m.WirelessRemote {
		s.Uint8(&m.WirelessRemote[i])
	}
	for i := range m.Reserve {
		s.Uint32(&m.Reserve[i])
	}
	s.Uint32(&m.CRC)
}

func (m *MotorState) cdr(s *xcdr1.Stream) {
	s.Uint8(&m.Mode)
	s.Float32(&m.Q)
	s.Float32(&m.DQ)
	s.Float32(&m.DDQ)
	s.Float32(&m.TauEst)
	for i := range m.Temperature {
		s.Int16(&m.Temperature[i])
	}
	s.Float32(&m.Vol)
	for i := range m.Sensor {
		s.Uint32(&m.Sensor[i])
	}
	s.Uint32(&m.Motorstate)
	for i := range m.Reserve {
		s.Uint32(&m.Reserve[i])
	}
}
