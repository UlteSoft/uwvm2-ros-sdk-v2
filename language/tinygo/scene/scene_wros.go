// Code generated from share/abi/ros.json.
//go:build wasm || tinygo.wasm

// Package scene declares the ROSv2 Wasm guest imports.
package scene

//go:wasmimport uwvm_ros_v2 abi
func Abi() uint32

//go:wasmimport uwvm_ros_v2 capability.open
func CapabilityOpen(arg0 uint32, arg1 uint64, arg2 uint64, arg3 uint64) uint32

//go:wasmimport uwvm_ros_v2 capability.close
func CapabilityClose(arg0 uint64) uint32

//go:wasmimport uwvm_ros_v2 guard.create
func GuardCreate(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 guard.trigger
func GuardTrigger(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 guard.take
func GuardTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 clock.create
func ClockCreate(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 clock.read
func ClockRead(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 clock.update
func ClockUpdate(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 timer.create
func TimerCreate(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 timer.reset
func TimerReset(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 timer.cancel
func TimerCancel(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 timer.take
func TimerTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 wait.create
func WaitCreate(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 wait.add
func WaitAdd(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 wait.remove
func WaitRemove(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 wait.acknowledge
func WaitAcknowledge(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 wait.poll
func WaitPoll(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 resource.close
func ResourceClose(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 context.open
func ContextOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 context.describe
func ContextDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 context.shutdown
func ContextShutdown(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 node.open
func NodeOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 node.describe
func NodeDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 type.describe
func TypeDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 topic.open
func TopicOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 topic.publish
func TopicPublish(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 topic.take
func TopicTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 topic.describe
func TopicDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 qos.describe
func QosDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 qos.liveliness.assert
func QosLivelinessAssert(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 qos.acknowledgements.wait
func QosAcknowledgementsWait(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.open
func ServiceOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.submit
func ServiceSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.take
func ServiceTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.respond
func ServiceRespond(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.available
func ServiceAvailable(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.abandon
func ServiceAbandon(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 action.open
func ActionOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 action.submit
func ActionSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 action.take
func ActionTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 action.respond
func ActionRespond(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 action.cancel
func ActionCancel(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 action.describe
func ActionDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.open
func ParameterOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.declare
func ParameterDeclare(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.undeclare
func ParameterUndeclare(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.get
func ParameterGet(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.describe
func ParameterDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.list
func ParameterList(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.set
func ParameterSet(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.set.atomic
func ParameterSetAtomic(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.take
func ParameterTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.respond
func ParameterRespond(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 lifecycle.open
func LifecycleOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 lifecycle.state
func LifecycleState(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 lifecycle.transitions
func LifecycleTransitions(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 lifecycle.submit
func LifecycleSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 lifecycle.take
func LifecycleTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 lifecycle.respond
func LifecycleRespond(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.open
func TransformOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.publish
func TransformPublish(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.lookup
func TransformLookup(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.available
func TransformAvailable(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.velocity
func TransformVelocity(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.submit
func TransformSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.take
func TransformTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.cancel
func TransformCancel(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 transform.clear
func TransformClear(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 graph.snapshot
func GraphSnapshot(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 graph.watch
func GraphWatch(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 event.stream.open
func EventStreamOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 event.stream.poll
func EventStreamPoll(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 event.stream.close
func EventStreamClose(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 buffer.create
func BufferCreate(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 buffer.write
func BufferWrite(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 buffer.seal
func BufferSeal(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 buffer.read
func BufferRead(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 buffer.describe
func BufferDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.open
func ArtifactOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.read
func ArtifactRead(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.describe
func ArtifactDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.begin
func ArtifactBegin(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.append
func ArtifactAppend(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.commit
func ArtifactCommit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.abort
func ArtifactAbort(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.remove
func ArtifactRemove(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 sensor.open
func SensorOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 sensor.take
func SensorTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 sensor.describe
func SensorDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 device.open
func DeviceOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 device.submit
func DeviceSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 device.result
func DeviceResult(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 device.stop
func DeviceStop(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 device.describe
func DeviceDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 control.open
func ControlOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 control.sample
func ControlSample(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 control.submit
func ControlSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 control.result
func ControlResult(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 control.stop
func ControlStop(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 media.open
func MediaOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 media.submit
func MediaSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 media.take
func MediaTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 media.close
func MediaClose(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 recording.open
func RecordingOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 recording.append
func RecordingAppend(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 recording.checkpoint
func RecordingCheckpoint(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 recording.stop
func RecordingStop(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 replay.open
func ReplayOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 replay.read
func ReplayRead(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 replay.seek
func ReplaySeek(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 model.open
func ModelOpen(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 model.submit
func ModelSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 model.take
func ModelTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 model.cancel
func ModelCancel(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 model.describe
func ModelDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 proposal.read
func ProposalRead(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 proposal.accept
func ProposalAccept(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 bridge.create
func BridgeCreate(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 bridge.start
func BridgeStart(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 bridge.stop
func BridgeStop(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 bridge.describe
func BridgeDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 log.emit
func LogEmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 diagnostic.read
func DiagnosticRead(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 request.describe
func RequestDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 request.release
func RequestRelease(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.status
func ArtifactStatus(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.receipt
func ArtifactReceipt(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 artifact.publish
func ArtifactPublish(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 proposal.capture
func ProposalCapture(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 proposal.publish
func ProposalPublish(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 communication.open.take
func CommunicationOpenTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 communication.open.cancel
func CommunicationOpenCancel(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 capability.revoke
func CapabilityRevoke(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 topic.reserve
func TopicReserve(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 topic.acknowledge
func TopicAcknowledge(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 topic.release
func TopicRelease(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.reserve
func ServiceReserve(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.acknowledge
func ServiceAcknowledge(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.release
func ServiceRelease(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.exists
func ParameterExists(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 parameter.search
func ParameterSearch(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 action.cancel.set
func ActionCancelSet(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 service.describe
func ServiceDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 permission.report
func PermissionReport(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.describe
func ModuleDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.imports
func ModuleImports(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.exports
func ModuleExports(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.group
func ModuleGroup(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.permission.report
func ModulePermissionReport(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.importers
func ModuleImporters(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 vm.describe
func VmDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.call.submit
func ModuleCallSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.call.take
func ModuleCallTake(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.call.respond
func ModuleCallRespond(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.call.result
func ModuleCallResult(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.call.acknowledge
func ModuleCallAcknowledge(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 module.call.cancel
func ModuleCallCancel(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 driver.connect
func DriverConnect(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 driver.submit
func DriverSubmit(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 driver.result
func DriverResult(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 driver.describe
func DriverDescribe(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32

//go:wasmimport uwvm_ros_v2 driver.disconnect
func DriverDisconnect(arg0 uint64, arg1 uint32, arg2 uint64, arg3 uint64, arg4 uint64, arg5 uint64, arg6 uint64) uint32
