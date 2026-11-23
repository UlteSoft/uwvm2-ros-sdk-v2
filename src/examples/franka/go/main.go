package main

import (
	"bytes"

	"github.com/UlteSoft/uwvm2-ros-sdk-v2/franka/cdr"
	arm "github.com/UlteSoft/uwvm2-ros-sdk-v2/franka/cdr/frankamsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/franka/cdr/sensormsgs"
	"github.com/UlteSoft/uwvm2-ros-sdk-v2/u2rosv2"
)

// Read the independent Fast-CDR frames supplied with this external project.
func readElbow() arm.Elbow {
	var elbow arm.Elbow
	var out [84]byte
	for _, sample := range []struct {
		src, want []byte
		order     cdr.Endian
	}{{elbowLE[:], elbowBE[:], cdr.BigEndian}, {elbowBE[:], elbowLE[:], cdr.LittleEndian}} {
		if err := elbow.UnmarshalCDR(sample.src); err != nil {
			panic(err)
		}
		n, err := elbow.MarshalCDR(sample.order, out[:])
		if err != nil {
			panic(err)
		}
		if !bytes.Equal(out[:n], sample.want) || elbow.Position != [2]float64{1.125, -1} {
			panic("unexpected Elbow transcode")
		}
	}
	return elbow
}

// The semantic component publishes joint names, measured q and the base frame
// together. Build a local sample with those fields and reuse its transport
// buffer after decoding. The receiver keeps the original strings and slices.
func inspectState(elbow arm.Elbow) {
	state := arm.DefaultFrankaRobotState()
	state.Elbow = elbow
	state.RobotMode = arm.FrankaRobotStateRobotModeIdle
	state.MeasuredJointState = sensormsgs.JointState{
		Name:     []string{"fr3_joint1", "fr3_joint2", "fr3_joint3", "fr3_joint4", "fr3_joint5", "fr3_joint6", "fr3_joint7"},
		Position: []float64{0, -1, 0, -2, 0, 1.5, 0.5},
	}
	state.MeasuredJointState.Header.FrameID = "fr3_link0"
	frame, err := state.MarshalBinary()
	if err != nil {
		panic(err)
	}
	var received arm.FrankaRobotState
	if err := received.UnmarshalBinary(frame); err != nil {
		panic(err)
	}
	for i := range frame {
		frame[i] = 0
	}
	joints := received.MeasuredJointState
	if joints.Header.FrameID != "fr3_link0" || len(joints.Name) != 7 || joints.Name[6] != "fr3_joint7" ||
		len(joints.Position) != 7 || joints.Position[3] != -2 || received.Elbow != elbow ||
		received.RobotMode != arm.FrankaRobotStateRobotModeIdle || received.OTEE.Pose.Orientation.W != 1 {
		panic("invalid semantic-component state")
	}
}

func main() {
	if u2rosv2.ABI() != 2 {
		panic("unexpected scene ABI")
	}
	inspectState(readElbow())
}
