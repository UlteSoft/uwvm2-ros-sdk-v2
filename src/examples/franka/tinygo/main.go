package main

import (
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/franka/cdr"
	arm "github.com/UlteSoft/uwvm2-ros-sdk-v2/franka/cdr/frankamsgs"
	spine "github.com/UlteSoft/uwvm2-ros-sdk-v2/franka/cdr/frankaspinemsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/franka/cdr/servicemsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/u2rosv2"
)

// Match the gripper feedback envelope to its local goal by the sixteen UUID octets.
func inspectGrasp() {
	goal := arm.DefaultGraspSendGoalRequest()
	goal.GoalID.UUID[15] = 7
	if goal.Goal.Epsilon.Inner != 0.005 || goal.Goal.Epsilon.Outer != 0.005 {
		panic("invalid default grasp tolerance")
	}
	report := arm.GraspFeedbackMessage{GoalID: goal.GoalID, Feedback: arm.GraspFeedback{CurrentWidth: 0.04}}
	var wire [32]byte
	n, err := report.MarshalCDR(cdr.BigEndian, wire[:])
	if err != nil {
		panic(err)
	}
	var feedback arm.GraspFeedbackMessage
	if err := feedback.UnmarshalCDR(wire[:n]); err != nil {
		panic(err)
	}
	if feedback.GoalID != goal.GoalID || feedback.Feedback.CurrentWidth != 0.04 {
		panic("unexpected gripper feedback")
	}
}

// The upstream GetPosition controller example reports 0.42 metres. Capture its
// reply in a Jazzy service event and match the sequence number and response.
func inspectSpine() {
	var wire [128]byte
	var query spine.GetPositionRequest
	n, err := query.MarshalCDR(cdr.BigEndian, wire[:])
	if err != nil {
		panic(err)
	}
	if n != 5 || wire[4] != 0 {
		panic("invalid empty service request")
	}
	event := spine.GetPositionEvent{
		Info:     servicemsgs.ServiceEventInfo{EventType: servicemsgs.ServiceEventInfoResponseSent, SequenceNumber: 41},
		Response: []spine.GetPositionResponse{{Position: 0.42, Success: true}},
	}
	n, err = event.MarshalCDR(cdr.LittleEndian, wire[:])
	if err != nil {
		panic(err)
	}
	var received spine.GetPositionEvent
	if err := received.UnmarshalCDR(wire[:n]); err != nil {
		panic(err)
	}
	if received.Info != event.Info || len(received.Request) != 0 || len(received.Response) != 1 ||
		received.Response[0] != event.Response[0] {
		panic("unexpected service event")
	}
}

func main() {
	if u2rosv2.ABI() != 2 {
		panic("unexpected scene ABI")
	}
	inspectGrasp()
	inspectSpine()
}
