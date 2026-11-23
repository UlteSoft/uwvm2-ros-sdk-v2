// Code generated from Unitree ROS 2 v0.3.0 .msg files by generate_go.py. DO NOT EDIT.

// Package unitreego maps the public unitree_go message definitions to Go.
package unitreego

// AudioData represents unitree_go/msg/AudioData.
type AudioData struct {
	TimeFrame uint64  `json:"time_frame"`
	Data      []uint8 `json:"data"`
}

// BmsCmd represents unitree_go/msg/BmsCmd.
type BmsCmd struct {
	Off     uint8    `json:"off"`
	Reserve [3]uint8 `json:"reserve"`
}

// BmsState represents unitree_go/msg/BmsState.
type BmsState struct {
	VersionHigh uint8      `json:"version_high"`
	VersionLow  uint8      `json:"version_low"`
	Status      uint8      `json:"status"`
	SOC         uint8      `json:"soc"`
	Current     int32      `json:"current"`
	Cycle       uint16     `json:"cycle"`
	BQNTC       [2]int8    `json:"bq_ntc"`
	MCUNTC      [2]int8    `json:"mcu_ntc"`
	CellVol     [15]uint16 `json:"cell_vol"`
}

// Error represents unitree_go/msg/Error.
type Error struct {
	Source uint32 `json:"source"`
	State  uint32 `json:"state"`
}

// Go2FrontVideoData represents unitree_go/msg/Go2FrontVideoData.
type Go2FrontVideoData struct {
	TimeFrame uint64  `json:"time_frame"`
	Video720p []uint8 `json:"video720p"`
	Video360p []uint8 `json:"video360p"`
	Video180p []uint8 `json:"video180p"`
}

// HeightMap represents unitree_go/msg/HeightMap.
type HeightMap struct {
	Stamp      float64    `json:"stamp"`
	FrameID    string     `json:"frame_id"`
	Resolution float32    `json:"resolution"`
	Width      uint32     `json:"width"`
	Height     uint32     `json:"height"`
	Origin     [2]float32 `json:"origin"`
	Data       []float32  `json:"data"`
}

// IMUState represents unitree_go/msg/IMUState.
type IMUState struct {
	Quaternion    [4]float32 `json:"quaternion"`
	Gyroscope     [3]float32 `json:"gyroscope"`
	Accelerometer [3]float32 `json:"accelerometer"`
	RPY           [3]float32 `json:"rpy"`
	Temperature   int8       `json:"temperature"`
}

// InterfaceConfig represents unitree_go/msg/InterfaceConfig.
type InterfaceConfig struct {
	Mode    uint8    `json:"mode"`
	Value   uint8    `json:"value"`
	Reserve [2]uint8 `json:"reserve"`
}

// LidarState represents unitree_go/msg/LidarState.
type LidarState struct {
	Stamp               float64    `json:"stamp"`
	FirmwareVersion     string     `json:"firmware_version"`
	SoftwareVersion     string     `json:"software_version"`
	SDKVersion          string     `json:"sdk_version"`
	SysRotationSpeed    float32    `json:"sys_rotation_speed"`
	ComRotationSpeed    float32    `json:"com_rotation_speed"`
	ErrorState          uint8      `json:"error_state"`
	CloudFrequency      float32    `json:"cloud_frequency"`
	CloudPacketLossRate float32    `json:"cloud_packet_loss_rate"`
	CloudSize           uint32     `json:"cloud_size"`
	CloudScanNum        uint32     `json:"cloud_scan_num"`
	IMUFrequency        float32    `json:"imu_frequency"`
	IMUPacketLossRate   float32    `json:"imu_packet_loss_rate"`
	IMURPY              [3]float32 `json:"imu_rpy"`
	SerialRecvStamp     float64    `json:"serial_recv_stamp"`
	SerialBufferSize    uint32     `json:"serial_buffer_size"`
	SerialBufferRead    uint32     `json:"serial_buffer_read"`
}

// LowCmd represents unitree_go/msg/LowCmd.
type LowCmd struct {
	Head           [2]uint8     `json:"head"`
	LevelFlag      uint8        `json:"level_flag"`
	FrameReserve   uint8        `json:"frame_reserve"`
	SN             [2]uint32    `json:"sn"`
	Version        [2]uint32    `json:"version"`
	Bandwidth      uint16       `json:"bandwidth"`
	MotorCmd       [20]MotorCmd `json:"motor_cmd"`
	BMSCmd         BmsCmd       `json:"bms_cmd"`
	WirelessRemote [40]uint8    `json:"wireless_remote"`
	Led            [12]uint8    `json:"led"`
	Fan            [2]uint8     `json:"fan"`
	Gpio           uint8        `json:"gpio"`
	Reserve        uint32       `json:"reserve"`
	CRC            uint32       `json:"crc"`
}

// LowState represents unitree_go/msg/LowState.
type LowState struct {
	Head            [2]uint8       `json:"head"`
	LevelFlag       uint8          `json:"level_flag"`
	FrameReserve    uint8          `json:"frame_reserve"`
	SN              [2]uint32      `json:"sn"`
	Version         [2]uint32      `json:"version"`
	Bandwidth       uint16         `json:"bandwidth"`
	IMUState        IMUState       `json:"imu_state"`
	MotorState      [20]MotorState `json:"motor_state"`
	BMSState        BmsState       `json:"bms_state"`
	FootForce       [4]int16       `json:"foot_force"`
	FootForceEst    [4]int16       `json:"foot_force_est"`
	Tick            uint32         `json:"tick"`
	WirelessRemote  [40]uint8      `json:"wireless_remote"`
	BitFlag         uint8          `json:"bit_flag"`
	ADCReel         float32        `json:"adc_reel"`
	TemperatureNtc1 int8           `json:"temperature_ntc1"`
	TemperatureNtc2 int8           `json:"temperature_ntc2"`
	PowerV          float32        `json:"power_v"`
	PowerA          float32        `json:"power_a"`
	FanFrequency    [4]uint16      `json:"fan_frequency"`
	Reserve         uint32         `json:"reserve"`
	CRC             uint32         `json:"crc"`
}

// MotorCmd represents unitree_go/msg/MotorCmd.
type MotorCmd struct {
	Mode    uint8     `json:"mode"`
	Q       float32   `json:"q"`
	DQ      float32   `json:"dq"`
	Tau     float32   `json:"tau"`
	Kp      float32   `json:"kp"`
	Kd      float32   `json:"kd"`
	Reserve [3]uint32 `json:"reserve"`
}

// MotorCmds represents unitree_go/msg/MotorCmds.
type MotorCmds struct {
	Cmds []MotorCmd `json:"cmds"`
}

// MotorState represents unitree_go/msg/MotorState.
type MotorState struct {
	Mode        uint8     `json:"mode"`
	Q           float32   `json:"q"`
	DQ          float32   `json:"dq"`
	DDQ         float32   `json:"ddq"`
	TauEst      float32   `json:"tau_est"`
	QRaw        float32   `json:"q_raw"`
	DQRaw       float32   `json:"dq_raw"`
	DDQRaw      float32   `json:"ddq_raw"`
	Temperature int8      `json:"temperature"`
	Lost        uint32    `json:"lost"`
	Reserve     [2]uint32 `json:"reserve"`
}

// MotorStates represents unitree_go/msg/MotorStates.
type MotorStates struct {
	States []MotorState `json:"states"`
}

// PathPoint represents unitree_go/msg/PathPoint.
type PathPoint struct {
	TFromStart float32 `json:"t_from_start"`
	X          float32 `json:"x"`
	Y          float32 `json:"y"`
	Yaw        float32 `json:"yaw"`
	Vx         float32 `json:"vx"`
	Vy         float32 `json:"vy"`
	Vyaw       float32 `json:"vyaw"`
}

// Req represents unitree_go/msg/Req.
type Req struct {
	UUID string `json:"uuid"`
	Body string `json:"body"`
}

// Res represents unitree_go/msg/Res.
type Res struct {
	UUID string  `json:"uuid"`
	Data []uint8 `json:"data"`
	Body string  `json:"body"`
}

// SportModeCmd represents unitree_go/msg/SportModeCmd.
type SportModeCmd struct {
	Mode            uint8         `json:"mode"`
	GaitType        uint8         `json:"gait_type"`
	SpeedLevel      uint8         `json:"speed_level"`
	FootRaiseHeight float32       `json:"foot_raise_height"`
	BodyHeight      float32       `json:"body_height"`
	Position        [2]float32    `json:"position"`
	Euler           [3]float32    `json:"euler"`
	Velocity        [2]float32    `json:"velocity"`
	YawSpeed        float32       `json:"yaw_speed"`
	BMSCmd          BmsCmd        `json:"bms_cmd"`
	PathPoint       [30]PathPoint `json:"path_point"`
}

// SportModeState represents unitree_go/msg/SportModeState.
type SportModeState struct {
	Stamp            TimeSpec    `json:"stamp"`
	ErrorCode        uint32      `json:"error_code"`
	IMUState         IMUState    `json:"imu_state"`
	Mode             uint8       `json:"mode"`
	Progress         float32     `json:"progress"`
	GaitType         uint8       `json:"gait_type"`
	FootRaiseHeight  float32     `json:"foot_raise_height"`
	Position         [3]float32  `json:"position"`
	BodyHeight       float32     `json:"body_height"`
	Velocity         [3]float32  `json:"velocity"`
	YawSpeed         float32     `json:"yaw_speed"`
	RangeObstacle    [4]float32  `json:"range_obstacle"`
	FootForce        [4]int16    `json:"foot_force"`
	FootPositionBody [12]float32 `json:"foot_position_body"`
	FootSpeedBody    [12]float32 `json:"foot_speed_body"`
}

// TimeSpec represents unitree_go/msg/TimeSpec.
type TimeSpec struct {
	Sec     int32  `json:"sec"`
	Nanosec uint32 `json:"nanosec"`
}

// UwbState represents unitree_go/msg/UwbState.
type UwbState struct {
	Version        [2]uint8   `json:"version"`
	Channel        uint8      `json:"channel"`
	JoyMode        uint8      `json:"joy_mode"`
	OrientationEst float32    `json:"orientation_est"`
	PitchEst       float32    `json:"pitch_est"`
	DistanceEst    float32    `json:"distance_est"`
	YawEst         float32    `json:"yaw_est"`
	TagRoll        float32    `json:"tag_roll"`
	TagPitch       float32    `json:"tag_pitch"`
	TagYaw         float32    `json:"tag_yaw"`
	BaseRoll       float32    `json:"base_roll"`
	BasePitch      float32    `json:"base_pitch"`
	BaseYaw        float32    `json:"base_yaw"`
	Joystick       [2]float32 `json:"joystick"`
	ErrorState     uint8      `json:"error_state"`
	Buttons        uint8      `json:"buttons"`
	EnabledFromApp uint8      `json:"enabled_from_app"`
}

// UwbSwitch represents unitree_go/msg/UwbSwitch.
type UwbSwitch struct {
	Enabled uint8 `json:"enabled"`
}

// WirelessController represents unitree_go/msg/WirelessController.
type WirelessController struct {
	Lx   float32 `json:"lx"`
	Ly   float32 `json:"ly"`
	Rx   float32 `json:"rx"`
	Ry   float32 `json:"ry"`
	Keys uint16  `json:"keys"`
}
