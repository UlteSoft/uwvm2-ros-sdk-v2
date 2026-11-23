package main

import (
	"encoding/binary"

	"github.com/UlteSoft/uwvm2-ros-sdk-v2/u2rosv2"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/unitree/unitreego"
)

// A real program can pass the serialized body received from a ROS 2
// subscription here. This copy belongs to the guest.
func decode(frame []byte) unitreego.LowState {
	var state unitreego.LowState
	if !state.UnmarshalCDR(frame) {
		panic("invalid unitree_go/msg/LowState CDR")
	}
	return state
}

func main() {
	major := u2rosv2.ABI()
	if major != 2 {
		panic("uwvm_ros_v2 ABI query failed")
	}
	// Exercise the full published schema using local values. Only the ABI
	// number above comes from the host.
	var state unitreego.LowState
	state.Tick = major
	state.IMUState.Quaternion = [4]float32{1, 0, 0, 0}
	state.MotorState[19].Q = float32(major) / 16
	state.MotorState[19].Reserve[1] = 0x11223344
	state.BMSState.CellVol[14] = 3777
	state.FootForce[3] = -17
	state.WirelessRemote[39] = 0xa5
	state.TemperatureNtc1 = -9
	state.CRC = 0x10203040
	var frame [unitreego.LowStateCDRSize]byte
	for _, order := range []binary.ByteOrder{binary.LittleEndian, binary.BigEndian} {
		if !state.MarshalCDR(frame[:], order) || decode(frame[:]) != state {
			panic("full LowState did not round trip")
		}
	}
}
