// Code generated from Unitree ROS 2 v0.3.0 .msg files by generate_go.py. DO NOT EDIT.

// Package unitreehg maps the public unitree_hg message definitions to Go.
package unitreehg

// BmsCmd represents unitree_hg/msg/BmsCmd.
type BmsCmd struct {
	Cmd     uint8     `json:"cmd"`
	Reserve [40]uint8 `json:"reserve"`
}

// BmsState represents unitree_hg/msg/BmsState.
type BmsState struct {
	VersionHigh      uint8      `json:"version_high"`
	VersionLow       uint8      `json:"version_low"`
	Fn               uint8      `json:"fn"`
	CellVol          [40]uint16 `json:"cell_vol"`
	Bmsvoltage       [3]uint32  `json:"bmsvoltage"`
	Current          int32      `json:"current"`
	SOC              uint8      `json:"soc"`
	SOH              uint8      `json:"soh"`
	Temperature      [12]int16  `json:"temperature"`
	Cycle            uint16     `json:"cycle"`
	ManufacturerDate uint16     `json:"manufacturer_date"`
	Bmsstate         [5]uint32  `json:"bmsstate"`
	Reserve          [3]uint32  `json:"reserve"`
}

// HandCmd represents unitree_hg/msg/HandCmd.
type HandCmd struct {
	MotorCmd []MotorCmd `json:"motor_cmd"`
	Reserve  [4]uint32  `json:"reserve"`
}

// HandState represents unitree_hg/msg/HandState.
type HandState struct {
	MotorState       []MotorState       `json:"motor_state"`
	PressSensorState []PressSensorState `json:"press_sensor_state"`
	IMUState         IMUState           `json:"imu_state"`
	PowerV           float32            `json:"power_v"`
	PowerA           float32            `json:"power_a"`
	SystemV          float32            `json:"system_v"`
	DeviceV          float32            `json:"device_v"`
	Error            [2]uint32          `json:"error"`
	Reserve          [2]uint32          `json:"reserve"`
}

// IMUState represents unitree_hg/msg/IMUState.
type IMUState struct {
	Quaternion    [4]float32 `json:"quaternion"`
	Gyroscope     [3]float32 `json:"gyroscope"`
	Accelerometer [3]float32 `json:"accelerometer"`
	RPY           [3]float32 `json:"rpy"`
	Temperature   int16      `json:"temperature"`
}

// LowCmd represents unitree_hg/msg/LowCmd.
type LowCmd struct {
	ModePr      uint8        `json:"mode_pr"`
	ModeMachine uint8        `json:"mode_machine"`
	MotorCmd    [35]MotorCmd `json:"motor_cmd"`
	Reserve     [4]uint32    `json:"reserve"`
	CRC         uint32       `json:"crc"`
}

// LowState represents unitree_hg/msg/LowState.
type LowState struct {
	Version        [2]uint32      `json:"version"`
	ModePr         uint8          `json:"mode_pr"`
	ModeMachine    uint8          `json:"mode_machine"`
	Tick           uint32         `json:"tick"`
	IMUState       IMUState       `json:"imu_state"`
	MotorState     [35]MotorState `json:"motor_state"`
	WirelessRemote [40]uint8      `json:"wireless_remote"`
	Reserve        [4]uint32      `json:"reserve"`
	CRC            uint32         `json:"crc"`
}

// MainBoardState represents unitree_hg/msg/MainBoardState.
type MainBoardState struct {
	FanState    [6]uint16  `json:"fan_state"`
	Temperature [6]int16   `json:"temperature"`
	Value       [6]float32 `json:"value"`
	State       [6]uint32  `json:"state"`
}

// MotorCmd represents unitree_hg/msg/MotorCmd.
type MotorCmd struct {
	Mode    uint8   `json:"mode"`
	Q       float32 `json:"q"`
	DQ      float32 `json:"dq"`
	Tau     float32 `json:"tau"`
	Kp      float32 `json:"kp"`
	Kd      float32 `json:"kd"`
	Reserve uint32  `json:"reserve"`
}

// MotorState represents unitree_hg/msg/MotorState.
type MotorState struct {
	Mode        uint8     `json:"mode"`
	Q           float32   `json:"q"`
	DQ          float32   `json:"dq"`
	DDQ         float32   `json:"ddq"`
	TauEst      float32   `json:"tau_est"`
	Temperature [2]int16  `json:"temperature"`
	Vol         float32   `json:"vol"`
	Sensor      [2]uint32 `json:"sensor"`
	Motorstate  uint32    `json:"motorstate"`
	Reserve     [4]uint32 `json:"reserve"`
}

// PressSensorState represents unitree_hg/msg/PressSensorState.
type PressSensorState struct {
	Pressure    [12]float32 `json:"pressure"`
	Temperature [12]float32 `json:"temperature"`
	Lost        uint32      `json:"lost"`
	Reserve     uint32      `json:"reserve"`
}
