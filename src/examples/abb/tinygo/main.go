package main

import (
	"bytes"

	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1/abbegmmsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1/abbrobotmsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1/stdmsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/u2rosv2"
)

// readSymbol handles one serialized request in guest memory. The sample value
// is local. A deployment can exchange these same bodies through its ROS service.
func readSymbol(query, reply []byte) (int, error) {
	var request abbrobotmsgs.GetRAPIDNumRequest
	if err := request.UnmarshalROS1(query); err != nil {
		return 0, err
	}
	path := abbrobotmsgs.RAPIDSymbolPath{Task: "T_ROB1", Module: "Survey", Symbol: "sample"}
	result := abbrobotmsgs.GetRAPIDNumResponse{ResultCode: abbrobotmsgs.ServiceResponsesRCFailed, Message: "Unknown symbol"}
	if request.Path == path {
		result = abbrobotmsgs.GetRAPIDNumResponse{Value: 12.5, ResultCode: abbrobotmsgs.ServiceResponsesRCSuccess}
	}
	return result.MarshalROS1(reply)
}

func serviceExchange() {
	request := abbrobotmsgs.GetRAPIDNumRequest{
		Path: abbrobotmsgs.RAPIDSymbolPath{Task: "T_ROB1", Module: "Survey", Symbol: "sample"},
	}
	query, err := request.MarshalBinary()
	if err != nil {
		panic(err)
	}
	var reply [64]byte
	n, err := readSymbol(query, reply[:])
	if err != nil {
		panic(err)
	}
	want := []byte{0, 0, 0x48, 0x41, 1, 0, 0, 0, 0, 0}
	var answer abbrobotmsgs.GetRAPIDNumResponse
	if !bytes.Equal(reply[:n], want) || answer.UnmarshalROS1(reply[:n]) != nil ||
		answer.ResultCode != abbrobotmsgs.ServiceResponsesRCSuccess || answer.Value != 12.5 {
		panic("unexpected ABB service response")
	}
	if answer.UnmarshalROS1(reply[:n-1]) != ros1.ErrTruncated || answer.Value != 12.5 {
		panic("truncated response replaced the previous result")
	}
}

func channelReport(seq uint32) {
	state := abbegmmsgs.EGMState{
		Header: stdmsgs.Header{Seq: seq, Stamp: ros1.Time{Sec: 42, Nsec: 17}, FrameID: "base"},
		EGMChannels: []abbegmmsgs.EGMChannelState{
			{Name: "channel-1", Active: true, EGMClientState: abbegmmsgs.EGMChannelStateEGMRunning, UtilizationRate: 73.25},
		},
	}
	frame, err := state.MarshalBinary()
	if err != nil {
		panic(err)
	}
	var received abbegmmsgs.EGMState
	if err := received.UnmarshalBinary(frame); err != nil {
		panic(err)
	}
	if received.Header != state.Header || len(received.EGMChannels) != 1 || received.EGMChannels[0] != state.EGMChannels[0] {
		panic("unexpected EGM channel report")
	}
}

func main() {
	major := u2rosv2.ABI()
	if major != 2 {
		panic("unexpected scene ABI")
	}
	channelReport(major)
	serviceExchange()
}
