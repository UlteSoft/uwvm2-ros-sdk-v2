// Generated AssemblyScript external function declarations.
@external("uwvm_ros_v2", "abi")
export declare function wr_abi(): u32;
@external("uwvm_ros_v2", "capability.open")
export declare function wr_capability_open(arg0: u32, arg1: u64, arg2: u64, arg3: u64): u32;
@external("uwvm_ros_v2", "capability.close")
export declare function wr_capability_close(arg0: u64): u32;
@external("uwvm_ros_v2", "guard.create")
export declare function wr_guard_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "guard.trigger")
export declare function wr_guard_trigger(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "guard.take")
export declare function wr_guard_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "clock.create")
export declare function wr_clock_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "clock.read")
export declare function wr_clock_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "clock.update")
export declare function wr_clock_update(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "timer.create")
export declare function wr_timer_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "timer.reset")
export declare function wr_timer_reset(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "timer.cancel")
export declare function wr_timer_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "timer.take")
export declare function wr_timer_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "wait.create")
export declare function wr_wait_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "wait.add")
export declare function wr_wait_add(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "wait.remove")
export declare function wr_wait_remove(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "wait.acknowledge")
export declare function wr_wait_acknowledge(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "wait.poll")
export declare function wr_wait_poll(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "resource.close")
export declare function wr_resource_close(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "context.open")
export declare function wr_context_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "context.describe")
export declare function wr_context_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "context.shutdown")
export declare function wr_context_shutdown(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "node.open")
export declare function wr_node_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "node.describe")
export declare function wr_node_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "type.describe")
export declare function wr_type_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "topic.open")
export declare function wr_topic_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "topic.publish")
export declare function wr_topic_publish(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "topic.take")
export declare function wr_topic_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "topic.describe")
export declare function wr_topic_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "qos.describe")
export declare function wr_qos_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "qos.liveliness.assert")
export declare function wr_qos_liveliness_assert(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "qos.acknowledgements.wait")
export declare function wr_qos_acknowledgements_wait(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.open")
export declare function wr_service_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.submit")
export declare function wr_service_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.take")
export declare function wr_service_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.respond")
export declare function wr_service_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.available")
export declare function wr_service_available(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.abandon")
export declare function wr_service_abandon(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "action.open")
export declare function wr_action_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "action.submit")
export declare function wr_action_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "action.take")
export declare function wr_action_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "action.respond")
export declare function wr_action_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "action.cancel")
export declare function wr_action_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "action.describe")
export declare function wr_action_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.open")
export declare function wr_parameter_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.declare")
export declare function wr_parameter_declare(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.undeclare")
export declare function wr_parameter_undeclare(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.get")
export declare function wr_parameter_get(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.describe")
export declare function wr_parameter_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.list")
export declare function wr_parameter_list(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.set")
export declare function wr_parameter_set(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.set.atomic")
export declare function wr_parameter_set_atomic(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.take")
export declare function wr_parameter_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.respond")
export declare function wr_parameter_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "lifecycle.open")
export declare function wr_lifecycle_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "lifecycle.state")
export declare function wr_lifecycle_state(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "lifecycle.transitions")
export declare function wr_lifecycle_transitions(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "lifecycle.submit")
export declare function wr_lifecycle_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "lifecycle.take")
export declare function wr_lifecycle_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "lifecycle.respond")
export declare function wr_lifecycle_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.open")
export declare function wr_transform_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.publish")
export declare function wr_transform_publish(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.lookup")
export declare function wr_transform_lookup(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.available")
export declare function wr_transform_available(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.velocity")
export declare function wr_transform_velocity(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.submit")
export declare function wr_transform_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.take")
export declare function wr_transform_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.cancel")
export declare function wr_transform_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "transform.clear")
export declare function wr_transform_clear(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "graph.snapshot")
export declare function wr_graph_snapshot(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "graph.watch")
export declare function wr_graph_watch(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "event.stream.open")
export declare function wr_event_stream_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "event.stream.poll")
export declare function wr_event_stream_poll(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "event.stream.close")
export declare function wr_event_stream_close(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "buffer.create")
export declare function wr_buffer_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "buffer.write")
export declare function wr_buffer_write(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "buffer.seal")
export declare function wr_buffer_seal(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "buffer.read")
export declare function wr_buffer_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "buffer.describe")
export declare function wr_buffer_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.open")
export declare function wr_artifact_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.read")
export declare function wr_artifact_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.describe")
export declare function wr_artifact_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.begin")
export declare function wr_artifact_begin(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.append")
export declare function wr_artifact_append(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.commit")
export declare function wr_artifact_commit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.abort")
export declare function wr_artifact_abort(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.remove")
export declare function wr_artifact_remove(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "sensor.open")
export declare function wr_sensor_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "sensor.take")
export declare function wr_sensor_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "sensor.describe")
export declare function wr_sensor_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "device.open")
export declare function wr_device_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "device.submit")
export declare function wr_device_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "device.result")
export declare function wr_device_result(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "device.stop")
export declare function wr_device_stop(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "device.describe")
export declare function wr_device_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "control.open")
export declare function wr_control_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "control.sample")
export declare function wr_control_sample(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "control.submit")
export declare function wr_control_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "control.result")
export declare function wr_control_result(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "control.stop")
export declare function wr_control_stop(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "media.open")
export declare function wr_media_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "media.submit")
export declare function wr_media_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "media.take")
export declare function wr_media_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "media.close")
export declare function wr_media_close(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "recording.open")
export declare function wr_recording_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "recording.append")
export declare function wr_recording_append(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "recording.checkpoint")
export declare function wr_recording_checkpoint(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "recording.stop")
export declare function wr_recording_stop(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "replay.open")
export declare function wr_replay_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "replay.read")
export declare function wr_replay_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "replay.seek")
export declare function wr_replay_seek(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "model.open")
export declare function wr_model_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "model.submit")
export declare function wr_model_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "model.take")
export declare function wr_model_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "model.cancel")
export declare function wr_model_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "model.describe")
export declare function wr_model_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "proposal.read")
export declare function wr_proposal_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "proposal.accept")
export declare function wr_proposal_accept(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "bridge.create")
export declare function wr_bridge_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "bridge.start")
export declare function wr_bridge_start(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "bridge.stop")
export declare function wr_bridge_stop(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "bridge.describe")
export declare function wr_bridge_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "log.emit")
export declare function wr_log_emit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "diagnostic.read")
export declare function wr_diagnostic_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "request.describe")
export declare function wr_request_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "request.release")
export declare function wr_request_release(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.status")
export declare function wr_artifact_status(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.receipt")
export declare function wr_artifact_receipt(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "artifact.publish")
export declare function wr_artifact_publish(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "proposal.capture")
export declare function wr_proposal_capture(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "proposal.publish")
export declare function wr_proposal_publish(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "communication.open.take")
export declare function wr_communication_open_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "communication.open.cancel")
export declare function wr_communication_open_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "capability.revoke")
export declare function wr_capability_revoke(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "topic.reserve")
export declare function wr_topic_reserve(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "topic.acknowledge")
export declare function wr_topic_acknowledge(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "topic.release")
export declare function wr_topic_release(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.reserve")
export declare function wr_service_reserve(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.acknowledge")
export declare function wr_service_acknowledge(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.release")
export declare function wr_service_release(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.exists")
export declare function wr_parameter_exists(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "parameter.search")
export declare function wr_parameter_search(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "action.cancel.set")
export declare function wr_action_cancel_set(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "service.describe")
export declare function wr_service_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "permission.report")
export declare function wr_permission_report(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.describe")
export declare function wr_module_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.imports")
export declare function wr_module_imports(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.exports")
export declare function wr_module_exports(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.group")
export declare function wr_module_group(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.permission.report")
export declare function wr_module_permission_report(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.importers")
export declare function wr_module_importers(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "vm.describe")
export declare function wr_vm_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.call.submit")
export declare function wr_module_call_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.call.take")
export declare function wr_module_call_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.call.respond")
export declare function wr_module_call_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.call.result")
export declare function wr_module_call_result(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.call.acknowledge")
export declare function wr_module_call_acknowledge(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "module.call.cancel")
export declare function wr_module_call_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "driver.connect")
export declare function wr_driver_connect(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "driver.submit")
export declare function wr_driver_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "driver.result")
export declare function wr_driver_result(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "driver.describe")
export declare function wr_driver_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
@external("uwvm_ros_v2", "driver.disconnect")
export declare function wr_driver_disconnect(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64): u32;
