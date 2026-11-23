package main
import (
"bytes"
"encoding/binary"
"reflect"
"unsafe"
"github.com/UlteSoft/uwvm2-ros-sdk-v2/u2rosv2"
"github.com/UlteSoft/uwvm2-ros-sdk-v2/unitree/unitreeapi"
"github.com/UlteSoft/uwvm2-ros-sdk-v2/unitree/unitreego"
"github.com/UlteSoft/uwvm2-ros-sdk-v2/unitree/unitreehg"
)
type field struct { name, kind string }
func need(ok bool, message string) {
    if !ok { panic(message) }
}
func checkType(actual reflect.Type, expected []field) {
    need(actual.Kind() == reflect.Struct && actual.NumField() == len(expected), actual.String())
    for i, field := range expected {
        item := actual.Field(i)
        need(item.Tag.Get("json") == field.name && item.Type.String() == field.kind,
             actual.String() + ". field at " + field.name)
    }
}
func checkShapes() {
  checkType(reflect.TypeOf(unitreeapi.Request{}), []field{
    {"header", "unitreeapi.RequestHeader"},
    {"parameter", "string"},
    {"binary", "[]uint8"},
  })
  checkType(reflect.TypeOf(unitreeapi.RequestHeader{}), []field{
    {"identity", "unitreeapi.RequestIdentity"},
    {"lease", "unitreeapi.RequestLease"},
    {"policy", "unitreeapi.RequestPolicy"},
  })
  checkType(reflect.TypeOf(unitreeapi.RequestIdentity{}), []field{
    {"id", "int64"},
    {"api_id", "int64"},
  })
  checkType(reflect.TypeOf(unitreeapi.RequestLease{}), []field{
    {"id", "int64"},
  })
  checkType(reflect.TypeOf(unitreeapi.RequestPolicy{}), []field{
    {"priority", "int32"},
    {"noreply", "bool"},
  })
  checkType(reflect.TypeOf(unitreeapi.Response{}), []field{
    {"header", "unitreeapi.ResponseHeader"},
    {"data", "string"},
    {"binary", "[]int8"},
  })
  checkType(reflect.TypeOf(unitreeapi.ResponseHeader{}), []field{
    {"identity", "unitreeapi.RequestIdentity"},
    {"status", "unitreeapi.ResponseStatus"},
  })
  checkType(reflect.TypeOf(unitreeapi.ResponseStatus{}), []field{
    {"code", "int32"},
  })
  checkType(reflect.TypeOf(unitreego.AudioData{}), []field{
    {"time_frame", "uint64"},
    {"data", "[]uint8"},
  })
  checkType(reflect.TypeOf(unitreego.BmsCmd{}), []field{
    {"off", "uint8"},
    {"reserve", "[3]uint8"},
  })
  checkType(reflect.TypeOf(unitreego.BmsState{}), []field{
    {"version_high", "uint8"},
    {"version_low", "uint8"},
    {"status", "uint8"},
    {"soc", "uint8"},
    {"current", "int32"},
    {"cycle", "uint16"},
    {"bq_ntc", "[2]int8"},
    {"mcu_ntc", "[2]int8"},
    {"cell_vol", "[15]uint16"},
  })
  checkType(reflect.TypeOf(unitreego.Error{}), []field{
    {"source", "uint32"},
    {"state", "uint32"},
  })
  checkType(reflect.TypeOf(unitreego.Go2FrontVideoData{}), []field{
    {"time_frame", "uint64"},
    {"video720p", "[]uint8"},
    {"video360p", "[]uint8"},
    {"video180p", "[]uint8"},
  })
  checkType(reflect.TypeOf(unitreego.HeightMap{}), []field{
    {"stamp", "float64"},
    {"frame_id", "string"},
    {"resolution", "float32"},
    {"width", "uint32"},
    {"height", "uint32"},
    {"origin", "[2]float32"},
    {"data", "[]float32"},
  })
  checkType(reflect.TypeOf(unitreego.IMUState{}), []field{
    {"quaternion", "[4]float32"},
    {"gyroscope", "[3]float32"},
    {"accelerometer", "[3]float32"},
    {"rpy", "[3]float32"},
    {"temperature", "int8"},
  })
  checkType(reflect.TypeOf(unitreego.InterfaceConfig{}), []field{
    {"mode", "uint8"},
    {"value", "uint8"},
    {"reserve", "[2]uint8"},
  })
  checkType(reflect.TypeOf(unitreego.LidarState{}), []field{
    {"stamp", "float64"},
    {"firmware_version", "string"},
    {"software_version", "string"},
    {"sdk_version", "string"},
    {"sys_rotation_speed", "float32"},
    {"com_rotation_speed", "float32"},
    {"error_state", "uint8"},
    {"cloud_frequency", "float32"},
    {"cloud_packet_loss_rate", "float32"},
    {"cloud_size", "uint32"},
    {"cloud_scan_num", "uint32"},
    {"imu_frequency", "float32"},
    {"imu_packet_loss_rate", "float32"},
    {"imu_rpy", "[3]float32"},
    {"serial_recv_stamp", "float64"},
    {"serial_buffer_size", "uint32"},
    {"serial_buffer_read", "uint32"},
  })
  checkType(reflect.TypeOf(unitreego.LowCmd{}), []field{
    {"head", "[2]uint8"},
    {"level_flag", "uint8"},
    {"frame_reserve", "uint8"},
    {"sn", "[2]uint32"},
    {"version", "[2]uint32"},
    {"bandwidth", "uint16"},
    {"motor_cmd", "[20]unitreego.MotorCmd"},
    {"bms_cmd", "unitreego.BmsCmd"},
    {"wireless_remote", "[40]uint8"},
    {"led", "[12]uint8"},
    {"fan", "[2]uint8"},
    {"gpio", "uint8"},
    {"reserve", "uint32"},
    {"crc", "uint32"},
  })
  checkType(reflect.TypeOf(unitreego.LowState{}), []field{
    {"head", "[2]uint8"},
    {"level_flag", "uint8"},
    {"frame_reserve", "uint8"},
    {"sn", "[2]uint32"},
    {"version", "[2]uint32"},
    {"bandwidth", "uint16"},
    {"imu_state", "unitreego.IMUState"},
    {"motor_state", "[20]unitreego.MotorState"},
    {"bms_state", "unitreego.BmsState"},
    {"foot_force", "[4]int16"},
    {"foot_force_est", "[4]int16"},
    {"tick", "uint32"},
    {"wireless_remote", "[40]uint8"},
    {"bit_flag", "uint8"},
    {"adc_reel", "float32"},
    {"temperature_ntc1", "int8"},
    {"temperature_ntc2", "int8"},
    {"power_v", "float32"},
    {"power_a", "float32"},
    {"fan_frequency", "[4]uint16"},
    {"reserve", "uint32"},
    {"crc", "uint32"},
  })
  checkType(reflect.TypeOf(unitreego.MotorCmd{}), []field{
    {"mode", "uint8"},
    {"q", "float32"},
    {"dq", "float32"},
    {"tau", "float32"},
    {"kp", "float32"},
    {"kd", "float32"},
    {"reserve", "[3]uint32"},
  })
  checkType(reflect.TypeOf(unitreego.MotorCmds{}), []field{
    {"cmds", "[]unitreego.MotorCmd"},
  })
  checkType(reflect.TypeOf(unitreego.MotorState{}), []field{
    {"mode", "uint8"},
    {"q", "float32"},
    {"dq", "float32"},
    {"ddq", "float32"},
    {"tau_est", "float32"},
    {"q_raw", "float32"},
    {"dq_raw", "float32"},
    {"ddq_raw", "float32"},
    {"temperature", "int8"},
    {"lost", "uint32"},
    {"reserve", "[2]uint32"},
  })
  checkType(reflect.TypeOf(unitreego.MotorStates{}), []field{
    {"states", "[]unitreego.MotorState"},
  })
  checkType(reflect.TypeOf(unitreego.PathPoint{}), []field{
    {"t_from_start", "float32"},
    {"x", "float32"},
    {"y", "float32"},
    {"yaw", "float32"},
    {"vx", "float32"},
    {"vy", "float32"},
    {"vyaw", "float32"},
  })
  checkType(reflect.TypeOf(unitreego.Req{}), []field{
    {"uuid", "string"},
    {"body", "string"},
  })
  checkType(reflect.TypeOf(unitreego.Res{}), []field{
    {"uuid", "string"},
    {"data", "[]uint8"},
    {"body", "string"},
  })
  checkType(reflect.TypeOf(unitreego.SportModeCmd{}), []field{
    {"mode", "uint8"},
    {"gait_type", "uint8"},
    {"speed_level", "uint8"},
    {"foot_raise_height", "float32"},
    {"body_height", "float32"},
    {"position", "[2]float32"},
    {"euler", "[3]float32"},
    {"velocity", "[2]float32"},
    {"yaw_speed", "float32"},
    {"bms_cmd", "unitreego.BmsCmd"},
    {"path_point", "[30]unitreego.PathPoint"},
  })
  checkType(reflect.TypeOf(unitreego.SportModeState{}), []field{
    {"stamp", "unitreego.TimeSpec"},
    {"error_code", "uint32"},
    {"imu_state", "unitreego.IMUState"},
    {"mode", "uint8"},
    {"progress", "float32"},
    {"gait_type", "uint8"},
    {"foot_raise_height", "float32"},
    {"position", "[3]float32"},
    {"body_height", "float32"},
    {"velocity", "[3]float32"},
    {"yaw_speed", "float32"},
    {"range_obstacle", "[4]float32"},
    {"foot_force", "[4]int16"},
    {"foot_position_body", "[12]float32"},
    {"foot_speed_body", "[12]float32"},
  })
  checkType(reflect.TypeOf(unitreego.TimeSpec{}), []field{
    {"sec", "int32"},
    {"nanosec", "uint32"},
  })
  checkType(reflect.TypeOf(unitreego.UwbState{}), []field{
    {"version", "[2]uint8"},
    {"channel", "uint8"},
    {"joy_mode", "uint8"},
    {"orientation_est", "float32"},
    {"pitch_est", "float32"},
    {"distance_est", "float32"},
    {"yaw_est", "float32"},
    {"tag_roll", "float32"},
    {"tag_pitch", "float32"},
    {"tag_yaw", "float32"},
    {"base_roll", "float32"},
    {"base_pitch", "float32"},
    {"base_yaw", "float32"},
    {"joystick", "[2]float32"},
    {"error_state", "uint8"},
    {"buttons", "uint8"},
    {"enabled_from_app", "uint8"},
  })
  checkType(reflect.TypeOf(unitreego.UwbSwitch{}), []field{
    {"enabled", "uint8"},
  })
  checkType(reflect.TypeOf(unitreego.WirelessController{}), []field{
    {"lx", "float32"},
    {"ly", "float32"},
    {"rx", "float32"},
    {"ry", "float32"},
    {"keys", "uint16"},
  })
  checkType(reflect.TypeOf(unitreehg.BmsCmd{}), []field{
    {"cmd", "uint8"},
    {"reserve", "[40]uint8"},
  })
  checkType(reflect.TypeOf(unitreehg.BmsState{}), []field{
    {"version_high", "uint8"},
    {"version_low", "uint8"},
    {"fn", "uint8"},
    {"cell_vol", "[40]uint16"},
    {"bmsvoltage", "[3]uint32"},
    {"current", "int32"},
    {"soc", "uint8"},
    {"soh", "uint8"},
    {"temperature", "[12]int16"},
    {"cycle", "uint16"},
    {"manufacturer_date", "uint16"},
    {"bmsstate", "[5]uint32"},
    {"reserve", "[3]uint32"},
  })
  checkType(reflect.TypeOf(unitreehg.HandCmd{}), []field{
    {"motor_cmd", "[]unitreehg.MotorCmd"},
    {"reserve", "[4]uint32"},
  })
  checkType(reflect.TypeOf(unitreehg.HandState{}), []field{
    {"motor_state", "[]unitreehg.MotorState"},
    {"press_sensor_state", "[]unitreehg.PressSensorState"},
    {"imu_state", "unitreehg.IMUState"},
    {"power_v", "float32"},
    {"power_a", "float32"},
    {"system_v", "float32"},
    {"device_v", "float32"},
    {"error", "[2]uint32"},
    {"reserve", "[2]uint32"},
  })
  checkType(reflect.TypeOf(unitreehg.IMUState{}), []field{
    {"quaternion", "[4]float32"},
    {"gyroscope", "[3]float32"},
    {"accelerometer", "[3]float32"},
    {"rpy", "[3]float32"},
    {"temperature", "int16"},
  })
  checkType(reflect.TypeOf(unitreehg.LowCmd{}), []field{
    {"mode_pr", "uint8"},
    {"mode_machine", "uint8"},
    {"motor_cmd", "[35]unitreehg.MotorCmd"},
    {"reserve", "[4]uint32"},
    {"crc", "uint32"},
  })
  checkType(reflect.TypeOf(unitreehg.LowState{}), []field{
    {"version", "[2]uint32"},
    {"mode_pr", "uint8"},
    {"mode_machine", "uint8"},
    {"tick", "uint32"},
    {"imu_state", "unitreehg.IMUState"},
    {"motor_state", "[35]unitreehg.MotorState"},
    {"wireless_remote", "[40]uint8"},
    {"reserve", "[4]uint32"},
    {"crc", "uint32"},
  })
  checkType(reflect.TypeOf(unitreehg.MainBoardState{}), []field{
    {"fan_state", "[6]uint16"},
    {"temperature", "[6]int16"},
    {"value", "[6]float32"},
    {"state", "[6]uint32"},
  })
  checkType(reflect.TypeOf(unitreehg.MotorCmd{}), []field{
    {"mode", "uint8"},
    {"q", "float32"},
    {"dq", "float32"},
    {"tau", "float32"},
    {"kp", "float32"},
    {"kd", "float32"},
    {"reserve", "uint32"},
  })
  checkType(reflect.TypeOf(unitreehg.MotorState{}), []field{
    {"mode", "uint8"},
    {"q", "float32"},
    {"dq", "float32"},
    {"ddq", "float32"},
    {"tau_est", "float32"},
    {"temperature", "[2]int16"},
    {"vol", "float32"},
    {"sensor", "[2]uint32"},
    {"motorstate", "uint32"},
    {"reserve", "[4]uint32"},
  })
  checkType(reflect.TypeOf(unitreehg.PressSensorState{}), []field{
    {"pressure", "[12]float32"},
    {"temperature", "[12]float32"},
    {"lost", "uint32"},
    {"reserve", "uint32"},
  })
}
func check_go2(little, big []byte) {
  var expected unitreego.LowState
  expected.Head[0] = 24
  expected.Head[1] = 47
  expected.LevelFlag = 70
  expected.FrameReserve = 93
  expected.SN[0] = 2442195239
  expected.SN[1] = 2442207586
  expected.Version[0] = 2442219933
  expected.Version[1] = 2442232280
  expected.Bandwidth = 44041
  expected.IMUState.Quaternion[0] = 1.25
  expected.IMUState.Quaternion[1] = -1.375
  expected.IMUState.Quaternion[2] = 1.5
  expected.IMUState.Quaternion[3] = -1.625
  expected.IMUState.Gyroscope[0] = 1.75
  expected.IMUState.Gyroscope[1] = -1.875
  expected.IMUState.Gyroscope[2] = 2.0
  expected.IMUState.Accelerometer[0] = -2.125
  expected.IMUState.Accelerometer[1] = 2.25
  expected.IMUState.Accelerometer[2] = -2.375
  expected.IMUState.RPY[0] = 2.5
  expected.IMUState.RPY[1] = -2.625
  expected.IMUState.RPY[2] = 2.75
  expected.IMUState.Temperature = -24
  expected.MotorState[0].Mode = 43
  expected.MotorState[0].Q = -3.125
  expected.MotorState[0].DQ = 3.25
  expected.MotorState[0].DDQ = -3.375
  expected.MotorState[0].TauEst = 3.5
  expected.MotorState[0].QRaw = -3.625
  expected.MotorState[0].DQRaw = 3.75
  expected.MotorState[0].DDQRaw = -3.875
  expected.MotorState[0].Temperature = -33
  expected.MotorState[0].Lost = 2442540955
  expected.MotorState[0].Reserve[0] = 2442553302
  expected.MotorState[0].Reserve[1] = 2442565649
  expected.MotorState[1].Mode = 64
  expected.MotorState[1].Q = -4.625
  expected.MotorState[1].DQ = 4.75
  expected.MotorState[1].DDQ = -4.875
  expected.MotorState[1].TauEst = 5.0
  expected.MotorState[1].QRaw = -5.125
  expected.MotorState[1].DQRaw = 5.25
  expected.MotorState[1].DDQRaw = -5.375
  expected.MotorState[1].Temperature = -45
  expected.MotorState[1].Lost = 2442689119
  expected.MotorState[1].Reserve[0] = 2442701466
  expected.MotorState[1].Reserve[1] = 2442713813
  expected.MotorState[2].Mode = 85
  expected.MotorState[2].Q = -6.125
  expected.MotorState[2].DQ = 6.25
  expected.MotorState[2].DDQ = -6.375
  expected.MotorState[2].TauEst = 6.5
  expected.MotorState[2].QRaw = -6.625
  expected.MotorState[2].DQRaw = 6.75
  expected.MotorState[2].DDQRaw = -6.875
  expected.MotorState[2].Temperature = -57
  expected.MotorState[2].Lost = 2442837283
  expected.MotorState[2].Reserve[0] = 2442849630
  expected.MotorState[2].Reserve[1] = 2442861977
  expected.MotorState[3].Mode = 106
  expected.MotorState[3].Q = -7.625
  expected.MotorState[3].DQ = 7.75
  expected.MotorState[3].DDQ = -7.875
  expected.MotorState[3].TauEst = 8.0
  expected.MotorState[3].QRaw = -8.125
  expected.MotorState[3].DQRaw = 8.25
  expected.MotorState[3].DDQRaw = -8.375
  expected.MotorState[3].Temperature = -69
  expected.MotorState[3].Lost = 2442985447
  expected.MotorState[3].Reserve[0] = 2442997794
  expected.MotorState[3].Reserve[1] = 2443010141
  expected.MotorState[4].Mode = 127
  expected.MotorState[4].Q = -9.125
  expected.MotorState[4].DQ = 9.25
  expected.MotorState[4].DDQ = -9.375
  expected.MotorState[4].TauEst = 9.5
  expected.MotorState[4].QRaw = -9.625
  expected.MotorState[4].DQRaw = 9.75
  expected.MotorState[4].DDQRaw = -9.875
  expected.MotorState[4].Temperature = -81
  expected.MotorState[4].Lost = 2443133611
  expected.MotorState[4].Reserve[0] = 2443145958
  expected.MotorState[4].Reserve[1] = 2443158305
  expected.MotorState[5].Mode = 148
  expected.MotorState[5].Q = -10.625
  expected.MotorState[5].DQ = 10.75
  expected.MotorState[5].DDQ = -10.875
  expected.MotorState[5].TauEst = 11.0
  expected.MotorState[5].QRaw = -11.125
  expected.MotorState[5].DQRaw = 11.25
  expected.MotorState[5].DDQRaw = -11.375
  expected.MotorState[5].Temperature = -93
  expected.MotorState[5].Lost = 2443281775
  expected.MotorState[5].Reserve[0] = 2443294122
  expected.MotorState[5].Reserve[1] = 2443306469
  expected.MotorState[6].Mode = 169
  expected.MotorState[6].Q = -12.125
  expected.MotorState[6].DQ = 12.25
  expected.MotorState[6].DDQ = -12.375
  expected.MotorState[6].TauEst = 12.5
  expected.MotorState[6].QRaw = -12.625
  expected.MotorState[6].DQRaw = 12.75
  expected.MotorState[6].DDQRaw = -12.875
  expected.MotorState[6].Temperature = -105
  expected.MotorState[6].Lost = 2443429939
  expected.MotorState[6].Reserve[0] = 2443442286
  expected.MotorState[6].Reserve[1] = 2443454633
  expected.MotorState[7].Mode = 190
  expected.MotorState[7].Q = -13.625
  expected.MotorState[7].DQ = 13.75
  expected.MotorState[7].DDQ = -13.875
  expected.MotorState[7].TauEst = 14.0
  expected.MotorState[7].QRaw = -14.125
  expected.MotorState[7].DQRaw = 14.25
  expected.MotorState[7].DDQRaw = -14.375
  expected.MotorState[7].Temperature = -117
  expected.MotorState[7].Lost = 2443578103
  expected.MotorState[7].Reserve[0] = 2443590450
  expected.MotorState[7].Reserve[1] = 2443602797
  expected.MotorState[8].Mode = 211
  expected.MotorState[8].Q = -15.125
  expected.MotorState[8].DQ = 15.25
  expected.MotorState[8].DDQ = -15.375
  expected.MotorState[8].TauEst = 15.5
  expected.MotorState[8].QRaw = -15.625
  expected.MotorState[8].DQRaw = 15.75
  expected.MotorState[8].DDQRaw = -15.875
  expected.MotorState[8].Temperature = -2
  expected.MotorState[8].Lost = 2443726267
  expected.MotorState[8].Reserve[0] = 2443738614
  expected.MotorState[8].Reserve[1] = 2443750961
  expected.MotorState[9].Mode = 232
  expected.MotorState[9].Q = -16.625
  expected.MotorState[9].DQ = 16.75
  expected.MotorState[9].DDQ = -16.875
  expected.MotorState[9].TauEst = 17.0
  expected.MotorState[9].QRaw = -17.125
  expected.MotorState[9].DQRaw = 17.25
  expected.MotorState[9].DDQRaw = -17.375
  expected.MotorState[9].Temperature = -14
  expected.MotorState[9].Lost = 2443874431
  expected.MotorState[9].Reserve[0] = 2443886778
  expected.MotorState[9].Reserve[1] = 2443899125
  expected.MotorState[10].Mode = 253
  expected.MotorState[10].Q = -18.125
  expected.MotorState[10].DQ = 18.25
  expected.MotorState[10].DDQ = -18.375
  expected.MotorState[10].TauEst = 18.5
  expected.MotorState[10].QRaw = -18.625
  expected.MotorState[10].DQRaw = 18.75
  expected.MotorState[10].DDQRaw = -18.875
  expected.MotorState[10].Temperature = -26
  expected.MotorState[10].Lost = 2444022595
  expected.MotorState[10].Reserve[0] = 2444034942
  expected.MotorState[10].Reserve[1] = 2444047289
  expected.MotorState[11].Mode = 19
  expected.MotorState[11].Q = -19.625
  expected.MotorState[11].DQ = 19.75
  expected.MotorState[11].DDQ = -19.875
  expected.MotorState[11].TauEst = 20.0
  expected.MotorState[11].QRaw = -20.125
  expected.MotorState[11].DQRaw = 20.25
  expected.MotorState[11].DDQRaw = -20.375
  expected.MotorState[11].Temperature = -38
  expected.MotorState[11].Lost = 2444170759
  expected.MotorState[11].Reserve[0] = 2444183106
  expected.MotorState[11].Reserve[1] = 2444195453
  expected.MotorState[12].Mode = 40
  expected.MotorState[12].Q = -21.125
  expected.MotorState[12].DQ = 21.25
  expected.MotorState[12].DDQ = -21.375
  expected.MotorState[12].TauEst = 21.5
  expected.MotorState[12].QRaw = -21.625
  expected.MotorState[12].DQRaw = 21.75
  expected.MotorState[12].DDQRaw = -21.875
  expected.MotorState[12].Temperature = -50
  expected.MotorState[12].Lost = 2444318923
  expected.MotorState[12].Reserve[0] = 2444331270
  expected.MotorState[12].Reserve[1] = 2444343617
  expected.MotorState[13].Mode = 61
  expected.MotorState[13].Q = -22.625
  expected.MotorState[13].DQ = 22.75
  expected.MotorState[13].DDQ = -22.875
  expected.MotorState[13].TauEst = 23.0
  expected.MotorState[13].QRaw = -23.125
  expected.MotorState[13].DQRaw = 23.25
  expected.MotorState[13].DDQRaw = -23.375
  expected.MotorState[13].Temperature = -62
  expected.MotorState[13].Lost = 2444467087
  expected.MotorState[13].Reserve[0] = 2444479434
  expected.MotorState[13].Reserve[1] = 2444491781
  expected.MotorState[14].Mode = 82
  expected.MotorState[14].Q = -24.125
  expected.MotorState[14].DQ = 24.25
  expected.MotorState[14].DDQ = -24.375
  expected.MotorState[14].TauEst = 24.5
  expected.MotorState[14].QRaw = -24.625
  expected.MotorState[14].DQRaw = 24.75
  expected.MotorState[14].DDQRaw = -24.875
  expected.MotorState[14].Temperature = -74
  expected.MotorState[14].Lost = 2444615251
  expected.MotorState[14].Reserve[0] = 2444627598
  expected.MotorState[14].Reserve[1] = 2444639945
  expected.MotorState[15].Mode = 103
  expected.MotorState[15].Q = -25.625
  expected.MotorState[15].DQ = 25.75
  expected.MotorState[15].DDQ = -25.875
  expected.MotorState[15].TauEst = 26.0
  expected.MotorState[15].QRaw = -26.125
  expected.MotorState[15].DQRaw = 26.25
  expected.MotorState[15].DDQRaw = -26.375
  expected.MotorState[15].Temperature = -86
  expected.MotorState[15].Lost = 2444763415
  expected.MotorState[15].Reserve[0] = 2444775762
  expected.MotorState[15].Reserve[1] = 2444788109
  expected.MotorState[16].Mode = 124
  expected.MotorState[16].Q = -27.125
  expected.MotorState[16].DQ = 27.25
  expected.MotorState[16].DDQ = -27.375
  expected.MotorState[16].TauEst = 27.5
  expected.MotorState[16].QRaw = -27.625
  expected.MotorState[16].DQRaw = 27.75
  expected.MotorState[16].DDQRaw = -27.875
  expected.MotorState[16].Temperature = -98
  expected.MotorState[16].Lost = 2444911579
  expected.MotorState[16].Reserve[0] = 2444923926
  expected.MotorState[16].Reserve[1] = 2444936273
  expected.MotorState[17].Mode = 145
  expected.MotorState[17].Q = -28.625
  expected.MotorState[17].DQ = 28.75
  expected.MotorState[17].DDQ = -28.875
  expected.MotorState[17].TauEst = 29.0
  expected.MotorState[17].QRaw = -29.125
  expected.MotorState[17].DQRaw = 29.25
  expected.MotorState[17].DDQRaw = -29.375
  expected.MotorState[17].Temperature = -110
  expected.MotorState[17].Lost = 2445059743
  expected.MotorState[17].Reserve[0] = 2445072090
  expected.MotorState[17].Reserve[1] = 2445084437
  expected.MotorState[18].Mode = 166
  expected.MotorState[18].Q = -30.125
  expected.MotorState[18].DQ = 30.25
  expected.MotorState[18].DDQ = -30.375
  expected.MotorState[18].TauEst = 30.5
  expected.MotorState[18].QRaw = -30.625
  expected.MotorState[18].DQRaw = 30.75
  expected.MotorState[18].DDQRaw = -30.875
  expected.MotorState[18].Temperature = -122
  expected.MotorState[18].Lost = 2445207907
  expected.MotorState[18].Reserve[0] = 2445220254
  expected.MotorState[18].Reserve[1] = 2445232601
  expected.MotorState[19].Mode = 187
  expected.MotorState[19].Q = -31.625
  expected.MotorState[19].DQ = 31.75
  expected.MotorState[19].DDQ = -31.875
  expected.MotorState[19].TauEst = 32.0
  expected.MotorState[19].QRaw = -32.125
  expected.MotorState[19].DQRaw = 32.25
  expected.MotorState[19].DDQRaw = -32.375
  expected.MotorState[19].Temperature = -7
  expected.MotorState[19].Lost = 2445356071
  expected.MotorState[19].Reserve[0] = 2445368418
  expected.MotorState[19].Reserve[1] = 2445380765
  expected.BMSState.VersionHigh = 208
  expected.BMSState.VersionLow = 231
  expected.BMSState.Status = 254
  expected.BMSState.SOC = 22
  expected.BMSState.Current = -193759
  expected.BMSState.Cycle = 44301
  expected.BMSState.BQNTC[0] = -17
  expected.BMSState.BQNTC[1] = -18
  expected.BMSState.MCUNTC[0] = -19
  expected.BMSState.MCUNTC[1] = -20
  expected.BMSState.CellVol[0] = 44306
  expected.BMSState.CellVol[1] = 44307
  expected.BMSState.CellVol[2] = 44308
  expected.BMSState.CellVol[3] = 44309
  expected.BMSState.CellVol[4] = 44310
  expected.BMSState.CellVol[5] = 44311
  expected.BMSState.CellVol[6] = 44312
  expected.BMSState.CellVol[7] = 44313
  expected.BMSState.CellVol[8] = 44314
  expected.BMSState.CellVol[9] = 44315
  expected.BMSState.CellVol[10] = 44316
  expected.BMSState.CellVol[11] = 44317
  expected.BMSState.CellVol[12] = 44318
  expected.BMSState.CellVol[13] = 44319
  expected.BMSState.CellVol[14] = 44320
  expected.FootForce[0] = -19133
  expected.FootForce[1] = -19130
  expected.FootForce[2] = -19127
  expected.FootForce[3] = -19124
  expected.FootForceEst[0] = -19121
  expected.FootForceEst[1] = -19118
  expected.FootForceEst[2] = -19115
  expected.FootForceEst[3] = -19112
  expected.Tick = 2445800563
  expected.WirelessRemote[0] = 225
  expected.WirelessRemote[1] = 248
  expected.WirelessRemote[2] = 16
  expected.WirelessRemote[3] = 39
  expected.WirelessRemote[4] = 62
  expected.WirelessRemote[5] = 85
  expected.WirelessRemote[6] = 108
  expected.WirelessRemote[7] = 131
  expected.WirelessRemote[8] = 154
  expected.WirelessRemote[9] = 177
  expected.WirelessRemote[10] = 200
  expected.WirelessRemote[11] = 223
  expected.WirelessRemote[12] = 246
  expected.WirelessRemote[13] = 14
  expected.WirelessRemote[14] = 37
  expected.WirelessRemote[15] = 60
  expected.WirelessRemote[16] = 83
  expected.WirelessRemote[17] = 106
  expected.WirelessRemote[18] = 129
  expected.WirelessRemote[19] = 152
  expected.WirelessRemote[20] = 175
  expected.WirelessRemote[21] = 198
  expected.WirelessRemote[22] = 221
  expected.WirelessRemote[23] = 244
  expected.WirelessRemote[24] = 12
  expected.WirelessRemote[25] = 35
  expected.WirelessRemote[26] = 58
  expected.WirelessRemote[27] = 81
  expected.WirelessRemote[28] = 104
  expected.WirelessRemote[29] = 127
  expected.WirelessRemote[30] = 150
  expected.WirelessRemote[31] = 173
  expected.WirelessRemote[32] = 196
  expected.WirelessRemote[33] = 219
  expected.WirelessRemote[34] = 242
  expected.WirelessRemote[35] = 10
  expected.WirelessRemote[36] = 33
  expected.WirelessRemote[37] = 56
  expected.WirelessRemote[38] = 79
  expected.WirelessRemote[39] = 102
  expected.BitFlag = 125
  expected.ADCReel = -42.375
  expected.TemperatureNtc1 = -87
  expected.TemperatureNtc2 = -88
  expected.PowerV = 42.75
  expected.PowerA = -42.875
  expected.FanFrequency[0] = 44376
  expected.FanFrequency[1] = 44377
  expected.FanFrequency[2] = 44378
  expected.FanFrequency[3] = 44379
  expected.Reserve = 2446430260
  expected.CRC = 2446442607
  need(unitreego.LowStateCDRSize == 1180, "go2 frame size")
  for index, frame := range [][]byte{little, big} {
    var order binary.ByteOrder = binary.LittleEndian
    if index == 1 { order = binary.BigEndian }
    need(len(frame) == 1180, "go2 oracle length")
    var decoded unitreego.LowState
    need(decoded.UnmarshalCDR(frame), "go2 decode")
    need(decoded == expected, "go2 all scalar fields")
    dest := make([]byte, len(frame) + 5)
    for i := range dest { dest[i] = 0xac }
    need(decoded.MarshalCDR(dest, order), "go2 encode")
    need(bytes.Equal(dest[:1180], frame), "go2 Fast-CDR bytes")
    need(bytes.Equal(dest[1180:], []byte{0xac, 0xac, 0xac, 0xac, 0xac}), "go2 trailing output")
    for i := range frame {
        need(!decoded.UnmarshalCDR(frame[:i]), "go2 truncated input accepted")
    }
    need(!decoded.UnmarshalCDR(dest), "go2 long input accepted")
    for i, v := range []byte{1, 2, 3, 4} {
        saved := dest[i]
        dest[i] = v
        need(!decoded.UnmarshalCDR(dest[:1180]), "go2 header accepted")
        dest[i] = saved
    }
    need(decoded == expected, "go2 malformed input mutated value")
    preserved := append([]byte(nil), dest...)
    var noReceiver *unitreego.LowState
    need(!noReceiver.UnmarshalCDR(frame) && !noReceiver.MarshalCDR(dest, order), "go2 nil receiver")
    need(!decoded.MarshalCDR(dest, nil), "go2 nil byte order")
    need(!decoded.MarshalCDR(dest[:1180-1], order), "go2 short output")
    need(bytes.Equal(dest, preserved), "go2 rejected output mutated buffer")
  }
}
func check_hg(little, big []byte) {
  var expected unitreehg.LowState
  expected.Version[0] = 2442145851
  expected.Version[1] = 2442158198
  expected.ModePr = 70
  expected.ModeMachine = 93
  expected.Tick = 2442195239
  expected.IMUState.Quaternion[0] = 0.75
  expected.IMUState.Quaternion[1] = -0.875
  expected.IMUState.Quaternion[2] = 1.0
  expected.IMUState.Quaternion[3] = -1.125
  expected.IMUState.Gyroscope[0] = 1.25
  expected.IMUState.Gyroscope[1] = -1.375
  expected.IMUState.Gyroscope[2] = 1.5
  expected.IMUState.Accelerometer[0] = -1.625
  expected.IMUState.Accelerometer[1] = 1.75
  expected.IMUState.Accelerometer[2] = -1.875
  expected.IMUState.RPY[0] = 2.0
  expected.IMUState.RPY[1] = -2.125
  expected.IMUState.RPY[2] = 2.25
  expected.IMUState.Temperature = -19943
  expected.MotorState[0].Mode = 206
  expected.MotorState[0].Q = -2.625
  expected.MotorState[0].DQ = 2.75
  expected.MotorState[0].DDQ = -2.875
  expected.MotorState[0].TauEst = 3.0
  expected.MotorState[0].Temperature[0] = -19925
  expected.MotorState[0].Temperature[1] = -19922
  expected.MotorState[0].Vol = -3.375
  expected.MotorState[0].Sensor[0] = 2442479220
  expected.MotorState[0].Sensor[1] = 2442491567
  expected.MotorState[0].Motorstate = 2442503914
  expected.MotorState[0].Reserve[0] = 2442516261
  expected.MotorState[0].Reserve[1] = 2442528608
  expected.MotorState[0].Reserve[2] = 2442540955
  expected.MotorState[0].Reserve[3] = 2442553302
  expected.MotorState[1].Mode = 41
  expected.MotorState[1].Q = 4.5
  expected.MotorState[1].DQ = -4.625
  expected.MotorState[1].DDQ = 4.75
  expected.MotorState[1].TauEst = -4.875
  expected.MotorState[1].Temperature[0] = -19880
  expected.MotorState[1].Temperature[1] = -19877
  expected.MotorState[1].Vol = 5.25
  expected.MotorState[1].Sensor[0] = 2442664425
  expected.MotorState[1].Sensor[1] = 2442676772
  expected.MotorState[1].Motorstate = 2442689119
  expected.MotorState[1].Reserve[0] = 2442701466
  expected.MotorState[1].Reserve[1] = 2442713813
  expected.MotorState[1].Reserve[2] = 2442726160
  expected.MotorState[1].Reserve[3] = 2442738507
  expected.MotorState[2].Mode = 131
  expected.MotorState[2].Q = -6.375
  expected.MotorState[2].DQ = 6.5
  expected.MotorState[2].DDQ = -6.625
  expected.MotorState[2].TauEst = 6.75
  expected.MotorState[2].Temperature[0] = -19835
  expected.MotorState[2].Temperature[1] = -19832
  expected.MotorState[2].Vol = -7.125
  expected.MotorState[2].Sensor[0] = 2442849630
  expected.MotorState[2].Sensor[1] = 2442861977
  expected.MotorState[2].Motorstate = 2442874324
  expected.MotorState[2].Reserve[0] = 2442886671
  expected.MotorState[2].Reserve[1] = 2442899018
  expected.MotorState[2].Reserve[2] = 2442911365
  expected.MotorState[2].Reserve[3] = 2442923712
  expected.MotorState[3].Mode = 221
  expected.MotorState[3].Q = 8.25
  expected.MotorState[3].DQ = -8.375
  expected.MotorState[3].DDQ = 8.5
  expected.MotorState[3].TauEst = -8.625
  expected.MotorState[3].Temperature[0] = -19790
  expected.MotorState[3].Temperature[1] = -19787
  expected.MotorState[3].Vol = 9.0
  expected.MotorState[3].Sensor[0] = 2443034835
  expected.MotorState[3].Sensor[1] = 2443047182
  expected.MotorState[3].Motorstate = 2443059529
  expected.MotorState[3].Reserve[0] = 2443071876
  expected.MotorState[3].Reserve[1] = 2443084223
  expected.MotorState[3].Reserve[2] = 2443096570
  expected.MotorState[3].Reserve[3] = 2443108917
  expected.MotorState[4].Mode = 56
  expected.MotorState[4].Q = -10.125
  expected.MotorState[4].DQ = 10.25
  expected.MotorState[4].DDQ = -10.375
  expected.MotorState[4].TauEst = 10.5
  expected.MotorState[4].Temperature[0] = -19745
  expected.MotorState[4].Temperature[1] = -19742
  expected.MotorState[4].Vol = -10.875
  expected.MotorState[4].Sensor[0] = 2443220040
  expected.MotorState[4].Sensor[1] = 2443232387
  expected.MotorState[4].Motorstate = 2443244734
  expected.MotorState[4].Reserve[0] = 2443257081
  expected.MotorState[4].Reserve[1] = 2443269428
  expected.MotorState[4].Reserve[2] = 2443281775
  expected.MotorState[4].Reserve[3] = 2443294122
  expected.MotorState[5].Mode = 146
  expected.MotorState[5].Q = 12.0
  expected.MotorState[5].DQ = -12.125
  expected.MotorState[5].DDQ = 12.25
  expected.MotorState[5].TauEst = -12.375
  expected.MotorState[5].Temperature[0] = -19700
  expected.MotorState[5].Temperature[1] = -19697
  expected.MotorState[5].Vol = 12.75
  expected.MotorState[5].Sensor[0] = 2443405245
  expected.MotorState[5].Sensor[1] = 2443417592
  expected.MotorState[5].Motorstate = 2443429939
  expected.MotorState[5].Reserve[0] = 2443442286
  expected.MotorState[5].Reserve[1] = 2443454633
  expected.MotorState[5].Reserve[2] = 2443466980
  expected.MotorState[5].Reserve[3] = 2443479327
  expected.MotorState[6].Mode = 236
  expected.MotorState[6].Q = -13.875
  expected.MotorState[6].DQ = 14.0
  expected.MotorState[6].DDQ = -14.125
  expected.MotorState[6].TauEst = 14.25
  expected.MotorState[6].Temperature[0] = -19655
  expected.MotorState[6].Temperature[1] = -19652
  expected.MotorState[6].Vol = -14.625
  expected.MotorState[6].Sensor[0] = 2443590450
  expected.MotorState[6].Sensor[1] = 2443602797
  expected.MotorState[6].Motorstate = 2443615144
  expected.MotorState[6].Reserve[0] = 2443627491
  expected.MotorState[6].Reserve[1] = 2443639838
  expected.MotorState[6].Reserve[2] = 2443652185
  expected.MotorState[6].Reserve[3] = 2443664532
  expected.MotorState[7].Mode = 71
  expected.MotorState[7].Q = 15.75
  expected.MotorState[7].DQ = -15.875
  expected.MotorState[7].DDQ = 16.0
  expected.MotorState[7].TauEst = -16.125
  expected.MotorState[7].Temperature[0] = -19610
  expected.MotorState[7].Temperature[1] = -19607
  expected.MotorState[7].Vol = 16.5
  expected.MotorState[7].Sensor[0] = 2443775655
  expected.MotorState[7].Sensor[1] = 2443788002
  expected.MotorState[7].Motorstate = 2443800349
  expected.MotorState[7].Reserve[0] = 2443812696
  expected.MotorState[7].Reserve[1] = 2443825043
  expected.MotorState[7].Reserve[2] = 2443837390
  expected.MotorState[7].Reserve[3] = 2443849737
  expected.MotorState[8].Mode = 161
  expected.MotorState[8].Q = -17.625
  expected.MotorState[8].DQ = 17.75
  expected.MotorState[8].DDQ = -17.875
  expected.MotorState[8].TauEst = 18.0
  expected.MotorState[8].Temperature[0] = -19565
  expected.MotorState[8].Temperature[1] = -19562
  expected.MotorState[8].Vol = -18.375
  expected.MotorState[8].Sensor[0] = 2443960860
  expected.MotorState[8].Sensor[1] = 2443973207
  expected.MotorState[8].Motorstate = 2443985554
  expected.MotorState[8].Reserve[0] = 2443997901
  expected.MotorState[8].Reserve[1] = 2444010248
  expected.MotorState[8].Reserve[2] = 2444022595
  expected.MotorState[8].Reserve[3] = 2444034942
  expected.MotorState[9].Mode = 251
  expected.MotorState[9].Q = 19.5
  expected.MotorState[9].DQ = -19.625
  expected.MotorState[9].DDQ = 19.75
  expected.MotorState[9].TauEst = -19.875
  expected.MotorState[9].Temperature[0] = -19520
  expected.MotorState[9].Temperature[1] = -19517
  expected.MotorState[9].Vol = 20.25
  expected.MotorState[9].Sensor[0] = 2444146065
  expected.MotorState[9].Sensor[1] = 2444158412
  expected.MotorState[9].Motorstate = 2444170759
  expected.MotorState[9].Reserve[0] = 2444183106
  expected.MotorState[9].Reserve[1] = 2444195453
  expected.MotorState[9].Reserve[2] = 2444207800
  expected.MotorState[9].Reserve[3] = 2444220147
  expected.MotorState[10].Mode = 86
  expected.MotorState[10].Q = -21.375
  expected.MotorState[10].DQ = 21.5
  expected.MotorState[10].DDQ = -21.625
  expected.MotorState[10].TauEst = 21.75
  expected.MotorState[10].Temperature[0] = -19475
  expected.MotorState[10].Temperature[1] = -19472
  expected.MotorState[10].Vol = -22.125
  expected.MotorState[10].Sensor[0] = 2444331270
  expected.MotorState[10].Sensor[1] = 2444343617
  expected.MotorState[10].Motorstate = 2444355964
  expected.MotorState[10].Reserve[0] = 2444368311
  expected.MotorState[10].Reserve[1] = 2444380658
  expected.MotorState[10].Reserve[2] = 2444393005
  expected.MotorState[10].Reserve[3] = 2444405352
  expected.MotorState[11].Mode = 176
  expected.MotorState[11].Q = 23.25
  expected.MotorState[11].DQ = -23.375
  expected.MotorState[11].DDQ = 23.5
  expected.MotorState[11].TauEst = -23.625
  expected.MotorState[11].Temperature[0] = -19430
  expected.MotorState[11].Temperature[1] = -19427
  expected.MotorState[11].Vol = 24.0
  expected.MotorState[11].Sensor[0] = 2444516475
  expected.MotorState[11].Sensor[1] = 2444528822
  expected.MotorState[11].Motorstate = 2444541169
  expected.MotorState[11].Reserve[0] = 2444553516
  expected.MotorState[11].Reserve[1] = 2444565863
  expected.MotorState[11].Reserve[2] = 2444578210
  expected.MotorState[11].Reserve[3] = 2444590557
  expected.MotorState[12].Mode = 11
  expected.MotorState[12].Q = -25.125
  expected.MotorState[12].DQ = 25.25
  expected.MotorState[12].DDQ = -25.375
  expected.MotorState[12].TauEst = 25.5
  expected.MotorState[12].Temperature[0] = -19385
  expected.MotorState[12].Temperature[1] = -19382
  expected.MotorState[12].Vol = -25.875
  expected.MotorState[12].Sensor[0] = 2444701680
  expected.MotorState[12].Sensor[1] = 2444714027
  expected.MotorState[12].Motorstate = 2444726374
  expected.MotorState[12].Reserve[0] = 2444738721
  expected.MotorState[12].Reserve[1] = 2444751068
  expected.MotorState[12].Reserve[2] = 2444763415
  expected.MotorState[12].Reserve[3] = 2444775762
  expected.MotorState[13].Mode = 101
  expected.MotorState[13].Q = 27.0
  expected.MotorState[13].DQ = -27.125
  expected.MotorState[13].DDQ = 27.25
  expected.MotorState[13].TauEst = -27.375
  expected.MotorState[13].Temperature[0] = -19340
  expected.MotorState[13].Temperature[1] = -19337
  expected.MotorState[13].Vol = 27.75
  expected.MotorState[13].Sensor[0] = 2444886885
  expected.MotorState[13].Sensor[1] = 2444899232
  expected.MotorState[13].Motorstate = 2444911579
  expected.MotorState[13].Reserve[0] = 2444923926
  expected.MotorState[13].Reserve[1] = 2444936273
  expected.MotorState[13].Reserve[2] = 2444948620
  expected.MotorState[13].Reserve[3] = 2444960967
  expected.MotorState[14].Mode = 191
  expected.MotorState[14].Q = -28.875
  expected.MotorState[14].DQ = 29.0
  expected.MotorState[14].DDQ = -29.125
  expected.MotorState[14].TauEst = 29.25
  expected.MotorState[14].Temperature[0] = -19295
  expected.MotorState[14].Temperature[1] = -19292
  expected.MotorState[14].Vol = -29.625
  expected.MotorState[14].Sensor[0] = 2445072090
  expected.MotorState[14].Sensor[1] = 2445084437
  expected.MotorState[14].Motorstate = 2445096784
  expected.MotorState[14].Reserve[0] = 2445109131
  expected.MotorState[14].Reserve[1] = 2445121478
  expected.MotorState[14].Reserve[2] = 2445133825
  expected.MotorState[14].Reserve[3] = 2445146172
  expected.MotorState[15].Mode = 26
  expected.MotorState[15].Q = 30.75
  expected.MotorState[15].DQ = -30.875
  expected.MotorState[15].DDQ = 31.0
  expected.MotorState[15].TauEst = -31.125
  expected.MotorState[15].Temperature[0] = -19250
  expected.MotorState[15].Temperature[1] = -19247
  expected.MotorState[15].Vol = 31.5
  expected.MotorState[15].Sensor[0] = 2445257295
  expected.MotorState[15].Sensor[1] = 2445269642
  expected.MotorState[15].Motorstate = 2445281989
  expected.MotorState[15].Reserve[0] = 2445294336
  expected.MotorState[15].Reserve[1] = 2445306683
  expected.MotorState[15].Reserve[2] = 2445319030
  expected.MotorState[15].Reserve[3] = 2445331377
  expected.MotorState[16].Mode = 116
  expected.MotorState[16].Q = -32.625
  expected.MotorState[16].DQ = 32.75
  expected.MotorState[16].DDQ = -32.875
  expected.MotorState[16].TauEst = 33.0
  expected.MotorState[16].Temperature[0] = -19205
  expected.MotorState[16].Temperature[1] = -19202
  expected.MotorState[16].Vol = -33.375
  expected.MotorState[16].Sensor[0] = 2445442500
  expected.MotorState[16].Sensor[1] = 2445454847
  expected.MotorState[16].Motorstate = 2445467194
  expected.MotorState[16].Reserve[0] = 2445479541
  expected.MotorState[16].Reserve[1] = 2445491888
  expected.MotorState[16].Reserve[2] = 2445504235
  expected.MotorState[16].Reserve[3] = 2445516582
  expected.MotorState[17].Mode = 206
  expected.MotorState[17].Q = 34.5
  expected.MotorState[17].DQ = -34.625
  expected.MotorState[17].DDQ = 34.75
  expected.MotorState[17].TauEst = -34.875
  expected.MotorState[17].Temperature[0] = -19160
  expected.MotorState[17].Temperature[1] = -19157
  expected.MotorState[17].Vol = 35.25
  expected.MotorState[17].Sensor[0] = 2445627705
  expected.MotorState[17].Sensor[1] = 2445640052
  expected.MotorState[17].Motorstate = 2445652399
  expected.MotorState[17].Reserve[0] = 2445664746
  expected.MotorState[17].Reserve[1] = 2445677093
  expected.MotorState[17].Reserve[2] = 2445689440
  expected.MotorState[17].Reserve[3] = 2445701787
  expected.MotorState[18].Mode = 41
  expected.MotorState[18].Q = -36.375
  expected.MotorState[18].DQ = 36.5
  expected.MotorState[18].DDQ = -36.625
  expected.MotorState[18].TauEst = 36.75
  expected.MotorState[18].Temperature[0] = -19115
  expected.MotorState[18].Temperature[1] = -19112
  expected.MotorState[18].Vol = -37.125
  expected.MotorState[18].Sensor[0] = 2445812910
  expected.MotorState[18].Sensor[1] = 2445825257
  expected.MotorState[18].Motorstate = 2445837604
  expected.MotorState[18].Reserve[0] = 2445849951
  expected.MotorState[18].Reserve[1] = 2445862298
  expected.MotorState[18].Reserve[2] = 2445874645
  expected.MotorState[18].Reserve[3] = 2445886992
  expected.MotorState[19].Mode = 131
  expected.MotorState[19].Q = 38.25
  expected.MotorState[19].DQ = -38.375
  expected.MotorState[19].DDQ = 38.5
  expected.MotorState[19].TauEst = -38.625
  expected.MotorState[19].Temperature[0] = -19070
  expected.MotorState[19].Temperature[1] = -19067
  expected.MotorState[19].Vol = 39.0
  expected.MotorState[19].Sensor[0] = 2445998115
  expected.MotorState[19].Sensor[1] = 2446010462
  expected.MotorState[19].Motorstate = 2446022809
  expected.MotorState[19].Reserve[0] = 2446035156
  expected.MotorState[19].Reserve[1] = 2446047503
  expected.MotorState[19].Reserve[2] = 2446059850
  expected.MotorState[19].Reserve[3] = 2446072197
  expected.MotorState[20].Mode = 221
  expected.MotorState[20].Q = -40.125
  expected.MotorState[20].DQ = 40.25
  expected.MotorState[20].DDQ = -40.375
  expected.MotorState[20].TauEst = 40.5
  expected.MotorState[20].Temperature[0] = -19025
  expected.MotorState[20].Temperature[1] = -19022
  expected.MotorState[20].Vol = -40.875
  expected.MotorState[20].Sensor[0] = 2446183320
  expected.MotorState[20].Sensor[1] = 2446195667
  expected.MotorState[20].Motorstate = 2446208014
  expected.MotorState[20].Reserve[0] = 2446220361
  expected.MotorState[20].Reserve[1] = 2446232708
  expected.MotorState[20].Reserve[2] = 2446245055
  expected.MotorState[20].Reserve[3] = 2446257402
  expected.MotorState[21].Mode = 56
  expected.MotorState[21].Q = 42.0
  expected.MotorState[21].DQ = -42.125
  expected.MotorState[21].DDQ = 42.25
  expected.MotorState[21].TauEst = -42.375
  expected.MotorState[21].Temperature[0] = -18980
  expected.MotorState[21].Temperature[1] = -18977
  expected.MotorState[21].Vol = 42.75
  expected.MotorState[21].Sensor[0] = 2446368525
  expected.MotorState[21].Sensor[1] = 2446380872
  expected.MotorState[21].Motorstate = 2446393219
  expected.MotorState[21].Reserve[0] = 2446405566
  expected.MotorState[21].Reserve[1] = 2446417913
  expected.MotorState[21].Reserve[2] = 2446430260
  expected.MotorState[21].Reserve[3] = 2446442607
  expected.MotorState[22].Mode = 146
  expected.MotorState[22].Q = -43.875
  expected.MotorState[22].DQ = 44.0
  expected.MotorState[22].DDQ = -44.125
  expected.MotorState[22].TauEst = 44.25
  expected.MotorState[22].Temperature[0] = -18935
  expected.MotorState[22].Temperature[1] = -18932
  expected.MotorState[22].Vol = -44.625
  expected.MotorState[22].Sensor[0] = 2446553730
  expected.MotorState[22].Sensor[1] = 2446566077
  expected.MotorState[22].Motorstate = 2446578424
  expected.MotorState[22].Reserve[0] = 2446590771
  expected.MotorState[22].Reserve[1] = 2446603118
  expected.MotorState[22].Reserve[2] = 2446615465
  expected.MotorState[22].Reserve[3] = 2446627812
  expected.MotorState[23].Mode = 236
  expected.MotorState[23].Q = 45.75
  expected.MotorState[23].DQ = -45.875
  expected.MotorState[23].DDQ = 46.0
  expected.MotorState[23].TauEst = -46.125
  expected.MotorState[23].Temperature[0] = -18890
  expected.MotorState[23].Temperature[1] = -18887
  expected.MotorState[23].Vol = 46.5
  expected.MotorState[23].Sensor[0] = 2446738935
  expected.MotorState[23].Sensor[1] = 2446751282
  expected.MotorState[23].Motorstate = 2446763629
  expected.MotorState[23].Reserve[0] = 2446775976
  expected.MotorState[23].Reserve[1] = 2446788323
  expected.MotorState[23].Reserve[2] = 2446800670
  expected.MotorState[23].Reserve[3] = 2446813017
  expected.MotorState[24].Mode = 71
  expected.MotorState[24].Q = -47.625
  expected.MotorState[24].DQ = 47.75
  expected.MotorState[24].DDQ = -47.875
  expected.MotorState[24].TauEst = 48.0
  expected.MotorState[24].Temperature[0] = -18845
  expected.MotorState[24].Temperature[1] = -18842
  expected.MotorState[24].Vol = -48.375
  expected.MotorState[24].Sensor[0] = 2446924140
  expected.MotorState[24].Sensor[1] = 2446936487
  expected.MotorState[24].Motorstate = 2446948834
  expected.MotorState[24].Reserve[0] = 2446961181
  expected.MotorState[24].Reserve[1] = 2446973528
  expected.MotorState[24].Reserve[2] = 2446985875
  expected.MotorState[24].Reserve[3] = 2446998222
  expected.MotorState[25].Mode = 161
  expected.MotorState[25].Q = 49.5
  expected.MotorState[25].DQ = -49.625
  expected.MotorState[25].DDQ = 49.75
  expected.MotorState[25].TauEst = -49.875
  expected.MotorState[25].Temperature[0] = -18800
  expected.MotorState[25].Temperature[1] = -18797
  expected.MotorState[25].Vol = 50.25
  expected.MotorState[25].Sensor[0] = 2447109345
  expected.MotorState[25].Sensor[1] = 2447121692
  expected.MotorState[25].Motorstate = 2447134039
  expected.MotorState[25].Reserve[0] = 2447146386
  expected.MotorState[25].Reserve[1] = 2447158733
  expected.MotorState[25].Reserve[2] = 2447171080
  expected.MotorState[25].Reserve[3] = 2447183427
  expected.MotorState[26].Mode = 251
  expected.MotorState[26].Q = -51.375
  expected.MotorState[26].DQ = 51.5
  expected.MotorState[26].DDQ = -51.625
  expected.MotorState[26].TauEst = 51.75
  expected.MotorState[26].Temperature[0] = -18755
  expected.MotorState[26].Temperature[1] = -18752
  expected.MotorState[26].Vol = -52.125
  expected.MotorState[26].Sensor[0] = 2447294550
  expected.MotorState[26].Sensor[1] = 2447306897
  expected.MotorState[26].Motorstate = 2447319244
  expected.MotorState[26].Reserve[0] = 2447331591
  expected.MotorState[26].Reserve[1] = 2447343938
  expected.MotorState[26].Reserve[2] = 2447356285
  expected.MotorState[26].Reserve[3] = 2447368632
  expected.MotorState[27].Mode = 86
  expected.MotorState[27].Q = 53.25
  expected.MotorState[27].DQ = -53.375
  expected.MotorState[27].DDQ = 53.5
  expected.MotorState[27].TauEst = -53.625
  expected.MotorState[27].Temperature[0] = -18710
  expected.MotorState[27].Temperature[1] = -18707
  expected.MotorState[27].Vol = 54.0
  expected.MotorState[27].Sensor[0] = 2447479755
  expected.MotorState[27].Sensor[1] = 2447492102
  expected.MotorState[27].Motorstate = 2447504449
  expected.MotorState[27].Reserve[0] = 2447516796
  expected.MotorState[27].Reserve[1] = 2447529143
  expected.MotorState[27].Reserve[2] = 2447541490
  expected.MotorState[27].Reserve[3] = 2447553837
  expected.MotorState[28].Mode = 176
  expected.MotorState[28].Q = -55.125
  expected.MotorState[28].DQ = 55.25
  expected.MotorState[28].DDQ = -55.375
  expected.MotorState[28].TauEst = 55.5
  expected.MotorState[28].Temperature[0] = -18665
  expected.MotorState[28].Temperature[1] = -18662
  expected.MotorState[28].Vol = -55.875
  expected.MotorState[28].Sensor[0] = 2447664960
  expected.MotorState[28].Sensor[1] = 2447677307
  expected.MotorState[28].Motorstate = 2447689654
  expected.MotorState[28].Reserve[0] = 2447702001
  expected.MotorState[28].Reserve[1] = 2447714348
  expected.MotorState[28].Reserve[2] = 2447726695
  expected.MotorState[28].Reserve[3] = 2447739042
  expected.MotorState[29].Mode = 11
  expected.MotorState[29].Q = 57.0
  expected.MotorState[29].DQ = -57.125
  expected.MotorState[29].DDQ = 57.25
  expected.MotorState[29].TauEst = -57.375
  expected.MotorState[29].Temperature[0] = -18620
  expected.MotorState[29].Temperature[1] = -18617
  expected.MotorState[29].Vol = 57.75
  expected.MotorState[29].Sensor[0] = 2447850165
  expected.MotorState[29].Sensor[1] = 2447862512
  expected.MotorState[29].Motorstate = 2447874859
  expected.MotorState[29].Reserve[0] = 2447887206
  expected.MotorState[29].Reserve[1] = 2447899553
  expected.MotorState[29].Reserve[2] = 2447911900
  expected.MotorState[29].Reserve[3] = 2447924247
  expected.MotorState[30].Mode = 101
  expected.MotorState[30].Q = -58.875
  expected.MotorState[30].DQ = 59.0
  expected.MotorState[30].DDQ = -59.125
  expected.MotorState[30].TauEst = 59.25
  expected.MotorState[30].Temperature[0] = -18575
  expected.MotorState[30].Temperature[1] = -18572
  expected.MotorState[30].Vol = -59.625
  expected.MotorState[30].Sensor[0] = 2448035370
  expected.MotorState[30].Sensor[1] = 2448047717
  expected.MotorState[30].Motorstate = 2448060064
  expected.MotorState[30].Reserve[0] = 2448072411
  expected.MotorState[30].Reserve[1] = 2448084758
  expected.MotorState[30].Reserve[2] = 2448097105
  expected.MotorState[30].Reserve[3] = 2448109452
  expected.MotorState[31].Mode = 191
  expected.MotorState[31].Q = 60.75
  expected.MotorState[31].DQ = -60.875
  expected.MotorState[31].DDQ = 61.0
  expected.MotorState[31].TauEst = -61.125
  expected.MotorState[31].Temperature[0] = -18530
  expected.MotorState[31].Temperature[1] = -18527
  expected.MotorState[31].Vol = 61.5
  expected.MotorState[31].Sensor[0] = 2448220575
  expected.MotorState[31].Sensor[1] = 2448232922
  expected.MotorState[31].Motorstate = 2448245269
  expected.MotorState[31].Reserve[0] = 2448257616
  expected.MotorState[31].Reserve[1] = 2448269963
  expected.MotorState[31].Reserve[2] = 2448282310
  expected.MotorState[31].Reserve[3] = 2448294657
  expected.MotorState[32].Mode = 26
  expected.MotorState[32].Q = -62.625
  expected.MotorState[32].DQ = 62.75
  expected.MotorState[32].DDQ = -62.875
  expected.MotorState[32].TauEst = 63.0
  expected.MotorState[32].Temperature[0] = -18485
  expected.MotorState[32].Temperature[1] = -18482
  expected.MotorState[32].Vol = -63.375
  expected.MotorState[32].Sensor[0] = 2448405780
  expected.MotorState[32].Sensor[1] = 2448418127
  expected.MotorState[32].Motorstate = 2448430474
  expected.MotorState[32].Reserve[0] = 2448442821
  expected.MotorState[32].Reserve[1] = 2448455168
  expected.MotorState[32].Reserve[2] = 2448467515
  expected.MotorState[32].Reserve[3] = 2448479862
  expected.MotorState[33].Mode = 116
  expected.MotorState[33].Q = 64.5
  expected.MotorState[33].DQ = -64.625
  expected.MotorState[33].DDQ = 64.75
  expected.MotorState[33].TauEst = -64.875
  expected.MotorState[33].Temperature[0] = -18440
  expected.MotorState[33].Temperature[1] = -18437
  expected.MotorState[33].Vol = 65.25
  expected.MotorState[33].Sensor[0] = 2448590985
  expected.MotorState[33].Sensor[1] = 2448603332
  expected.MotorState[33].Motorstate = 2448615679
  expected.MotorState[33].Reserve[0] = 2448628026
  expected.MotorState[33].Reserve[1] = 2448640373
  expected.MotorState[33].Reserve[2] = 2448652720
  expected.MotorState[33].Reserve[3] = 2448665067
  expected.MotorState[34].Mode = 206
  expected.MotorState[34].Q = -66.375
  expected.MotorState[34].DQ = 66.5
  expected.MotorState[34].DDQ = -66.625
  expected.MotorState[34].TauEst = 66.75
  expected.MotorState[34].Temperature[0] = -18395
  expected.MotorState[34].Temperature[1] = -18392
  expected.MotorState[34].Vol = -67.125
  expected.MotorState[34].Sensor[0] = 2448776190
  expected.MotorState[34].Sensor[1] = 2448788537
  expected.MotorState[34].Motorstate = 2448800884
  expected.MotorState[34].Reserve[0] = 2448813231
  expected.MotorState[34].Reserve[1] = 2448825578
  expected.MotorState[34].Reserve[2] = 2448837925
  expected.MotorState[34].Reserve[3] = 2448850272
  expected.WirelessRemote[0] = 41
  expected.WirelessRemote[1] = 64
  expected.WirelessRemote[2] = 87
  expected.WirelessRemote[3] = 110
  expected.WirelessRemote[4] = 133
  expected.WirelessRemote[5] = 156
  expected.WirelessRemote[6] = 179
  expected.WirelessRemote[7] = 202
  expected.WirelessRemote[8] = 225
  expected.WirelessRemote[9] = 248
  expected.WirelessRemote[10] = 16
  expected.WirelessRemote[11] = 39
  expected.WirelessRemote[12] = 62
  expected.WirelessRemote[13] = 85
  expected.WirelessRemote[14] = 108
  expected.WirelessRemote[15] = 131
  expected.WirelessRemote[16] = 154
  expected.WirelessRemote[17] = 177
  expected.WirelessRemote[18] = 200
  expected.WirelessRemote[19] = 223
  expected.WirelessRemote[20] = 246
  expected.WirelessRemote[21] = 14
  expected.WirelessRemote[22] = 37
  expected.WirelessRemote[23] = 60
  expected.WirelessRemote[24] = 83
  expected.WirelessRemote[25] = 106
  expected.WirelessRemote[26] = 129
  expected.WirelessRemote[27] = 152
  expected.WirelessRemote[28] = 175
  expected.WirelessRemote[29] = 198
  expected.WirelessRemote[30] = 221
  expected.WirelessRemote[31] = 244
  expected.WirelessRemote[32] = 12
  expected.WirelessRemote[33] = 35
  expected.WirelessRemote[34] = 58
  expected.WirelessRemote[35] = 81
  expected.WirelessRemote[36] = 104
  expected.WirelessRemote[37] = 127
  expected.WirelessRemote[38] = 150
  expected.WirelessRemote[39] = 173
  expected.Reserve[0] = 2449356499
  expected.Reserve[1] = 2449368846
  expected.Reserve[2] = 2449381193
  expected.Reserve[3] = 2449393540
  expected.CRC = 2449405887
  need(unitreehg.LowStateCDRSize == 2092, "hg frame size")
  for index, frame := range [][]byte{little, big} {
    var order binary.ByteOrder = binary.LittleEndian
    if index == 1 { order = binary.BigEndian }
    need(len(frame) == 2092, "hg oracle length")
    var decoded unitreehg.LowState
    need(decoded.UnmarshalCDR(frame), "hg decode")
    need(decoded == expected, "hg all scalar fields")
    dest := make([]byte, len(frame) + 5)
    for i := range dest { dest[i] = 0xac }
    need(decoded.MarshalCDR(dest, order), "hg encode")
    need(bytes.Equal(dest[:2092], frame), "hg Fast-CDR bytes")
    need(bytes.Equal(dest[2092:], []byte{0xac, 0xac, 0xac, 0xac, 0xac}), "hg trailing output")
    for i := range frame {
        need(!decoded.UnmarshalCDR(frame[:i]), "hg truncated input accepted")
    }
    need(!decoded.UnmarshalCDR(dest), "hg long input accepted")
    for i, v := range []byte{1, 2, 3, 4} {
        saved := dest[i]
        dest[i] = v
        need(!decoded.UnmarshalCDR(dest[:2092]), "hg header accepted")
        dest[i] = saved
    }
    need(decoded == expected, "hg malformed input mutated value")
    preserved := append([]byte(nil), dest...)
    var noReceiver *unitreehg.LowState
    need(!noReceiver.UnmarshalCDR(frame) && !noReceiver.MarshalCDR(dest, order), "hg nil receiver")
    need(!decoded.MarshalCDR(dest, nil), "hg nil byte order")
    need(!decoded.MarshalCDR(dest[:2092-1], order), "hg short output")
    need(bytes.Equal(dest, preserved), "hg rejected output mutated buffer")
  }
}
func main() {
    major := u2rosv2.ABI()
    need(major == 2, "ABI version")
    words := unsafe.Sizeof(uintptr(major)) * 8
    need(words == expectedWordBits, "Go uintptr width")
    need(unsafe.Sizeof(int(major))*8 == expectedWordBits, "Go int width")
    need(unsafe.Sizeof(&major)*8 == expectedWordBits, "Go pointer width")
    checkShapes()
    check_go2(go2LE, go2BE)
    check_hg(hgLE, hgBE)
}
