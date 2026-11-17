// Generated raw Wasm imports.
#[link(wasm_import_module = "uwvm_ros_v2")]
unsafe extern "C" {
    #[link_name = "abi"]
    pub fn wr_abi() -> u32;
    #[link_name = "capability.open"]
    pub fn wr_capability_open(arg0: u32, arg1: u64, arg2: u64, arg3: u64) -> u32;
    #[link_name = "capability.close"]
    pub fn wr_capability_close(arg0: u64) -> u32;
    #[link_name = "guard.create"]
    pub fn wr_guard_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "guard.trigger"]
    pub fn wr_guard_trigger(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "guard.take"]
    pub fn wr_guard_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "clock.create"]
    pub fn wr_clock_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "clock.read"]
    pub fn wr_clock_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "clock.update"]
    pub fn wr_clock_update(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "timer.create"]
    pub fn wr_timer_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "timer.reset"]
    pub fn wr_timer_reset(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "timer.cancel"]
    pub fn wr_timer_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "timer.take"]
    pub fn wr_timer_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "wait.create"]
    pub fn wr_wait_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "wait.add"]
    pub fn wr_wait_add(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "wait.remove"]
    pub fn wr_wait_remove(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "wait.acknowledge"]
    pub fn wr_wait_acknowledge(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "wait.poll"]
    pub fn wr_wait_poll(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "resource.close"]
    pub fn wr_resource_close(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "context.open"]
    pub fn wr_context_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "context.describe"]
    pub fn wr_context_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "context.shutdown"]
    pub fn wr_context_shutdown(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "node.open"]
    pub fn wr_node_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "node.describe"]
    pub fn wr_node_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "type.describe"]
    pub fn wr_type_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "topic.open"]
    pub fn wr_topic_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "topic.publish"]
    pub fn wr_topic_publish(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "topic.take"]
    pub fn wr_topic_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "topic.describe"]
    pub fn wr_topic_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "qos.describe"]
    pub fn wr_qos_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "qos.liveliness.assert"]
    pub fn wr_qos_liveliness_assert(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "qos.acknowledgements.wait"]
    pub fn wr_qos_acknowledgements_wait(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.open"]
    pub fn wr_service_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.submit"]
    pub fn wr_service_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.take"]
    pub fn wr_service_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.respond"]
    pub fn wr_service_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.available"]
    pub fn wr_service_available(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.abandon"]
    pub fn wr_service_abandon(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "action.open"]
    pub fn wr_action_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "action.submit"]
    pub fn wr_action_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "action.take"]
    pub fn wr_action_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "action.respond"]
    pub fn wr_action_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "action.cancel"]
    pub fn wr_action_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "action.describe"]
    pub fn wr_action_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.open"]
    pub fn wr_parameter_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.declare"]
    pub fn wr_parameter_declare(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.undeclare"]
    pub fn wr_parameter_undeclare(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.get"]
    pub fn wr_parameter_get(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.describe"]
    pub fn wr_parameter_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.list"]
    pub fn wr_parameter_list(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.set"]
    pub fn wr_parameter_set(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.set.atomic"]
    pub fn wr_parameter_set_atomic(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.take"]
    pub fn wr_parameter_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.respond"]
    pub fn wr_parameter_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "lifecycle.open"]
    pub fn wr_lifecycle_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "lifecycle.state"]
    pub fn wr_lifecycle_state(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "lifecycle.transitions"]
    pub fn wr_lifecycle_transitions(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "lifecycle.submit"]
    pub fn wr_lifecycle_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "lifecycle.take"]
    pub fn wr_lifecycle_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "lifecycle.respond"]
    pub fn wr_lifecycle_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.open"]
    pub fn wr_transform_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.publish"]
    pub fn wr_transform_publish(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.lookup"]
    pub fn wr_transform_lookup(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.available"]
    pub fn wr_transform_available(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.velocity"]
    pub fn wr_transform_velocity(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.submit"]
    pub fn wr_transform_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.take"]
    pub fn wr_transform_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.cancel"]
    pub fn wr_transform_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "transform.clear"]
    pub fn wr_transform_clear(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "graph.snapshot"]
    pub fn wr_graph_snapshot(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "graph.watch"]
    pub fn wr_graph_watch(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "event.stream.open"]
    pub fn wr_event_stream_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "event.stream.poll"]
    pub fn wr_event_stream_poll(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "event.stream.close"]
    pub fn wr_event_stream_close(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "buffer.create"]
    pub fn wr_buffer_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "buffer.write"]
    pub fn wr_buffer_write(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "buffer.seal"]
    pub fn wr_buffer_seal(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "buffer.read"]
    pub fn wr_buffer_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "buffer.describe"]
    pub fn wr_buffer_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.open"]
    pub fn wr_artifact_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.read"]
    pub fn wr_artifact_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.describe"]
    pub fn wr_artifact_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.begin"]
    pub fn wr_artifact_begin(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.append"]
    pub fn wr_artifact_append(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.commit"]
    pub fn wr_artifact_commit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.abort"]
    pub fn wr_artifact_abort(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.remove"]
    pub fn wr_artifact_remove(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "sensor.open"]
    pub fn wr_sensor_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "sensor.take"]
    pub fn wr_sensor_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "sensor.describe"]
    pub fn wr_sensor_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "device.open"]
    pub fn wr_device_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "device.submit"]
    pub fn wr_device_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "device.result"]
    pub fn wr_device_result(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "device.stop"]
    pub fn wr_device_stop(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "device.describe"]
    pub fn wr_device_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "control.open"]
    pub fn wr_control_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "control.sample"]
    pub fn wr_control_sample(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "control.submit"]
    pub fn wr_control_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "control.result"]
    pub fn wr_control_result(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "control.stop"]
    pub fn wr_control_stop(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "media.open"]
    pub fn wr_media_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "media.submit"]
    pub fn wr_media_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "media.take"]
    pub fn wr_media_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "media.close"]
    pub fn wr_media_close(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "recording.open"]
    pub fn wr_recording_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "recording.append"]
    pub fn wr_recording_append(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "recording.checkpoint"]
    pub fn wr_recording_checkpoint(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "recording.stop"]
    pub fn wr_recording_stop(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "replay.open"]
    pub fn wr_replay_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "replay.read"]
    pub fn wr_replay_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "replay.seek"]
    pub fn wr_replay_seek(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "model.open"]
    pub fn wr_model_open(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "model.submit"]
    pub fn wr_model_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "model.take"]
    pub fn wr_model_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "model.cancel"]
    pub fn wr_model_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "model.describe"]
    pub fn wr_model_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "proposal.read"]
    pub fn wr_proposal_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "proposal.accept"]
    pub fn wr_proposal_accept(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "bridge.create"]
    pub fn wr_bridge_create(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "bridge.start"]
    pub fn wr_bridge_start(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "bridge.stop"]
    pub fn wr_bridge_stop(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "bridge.describe"]
    pub fn wr_bridge_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "log.emit"]
    pub fn wr_log_emit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "diagnostic.read"]
    pub fn wr_diagnostic_read(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "request.describe"]
    pub fn wr_request_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "request.release"]
    pub fn wr_request_release(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.status"]
    pub fn wr_artifact_status(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.receipt"]
    pub fn wr_artifact_receipt(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "artifact.publish"]
    pub fn wr_artifact_publish(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "proposal.capture"]
    pub fn wr_proposal_capture(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "proposal.publish"]
    pub fn wr_proposal_publish(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "communication.open.take"]
    pub fn wr_communication_open_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "communication.open.cancel"]
    pub fn wr_communication_open_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "capability.revoke"]
    pub fn wr_capability_revoke(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "topic.reserve"]
    pub fn wr_topic_reserve(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "topic.acknowledge"]
    pub fn wr_topic_acknowledge(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "topic.release"]
    pub fn wr_topic_release(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.reserve"]
    pub fn wr_service_reserve(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.acknowledge"]
    pub fn wr_service_acknowledge(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.release"]
    pub fn wr_service_release(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.exists"]
    pub fn wr_parameter_exists(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "parameter.search"]
    pub fn wr_parameter_search(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "action.cancel.set"]
    pub fn wr_action_cancel_set(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "service.describe"]
    pub fn wr_service_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "permission.report"]
    pub fn wr_permission_report(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.describe"]
    pub fn wr_module_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.imports"]
    pub fn wr_module_imports(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.exports"]
    pub fn wr_module_exports(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.group"]
    pub fn wr_module_group(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.permission.report"]
    pub fn wr_module_permission_report(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.importers"]
    pub fn wr_module_importers(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "vm.describe"]
    pub fn wr_vm_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.call.submit"]
    pub fn wr_module_call_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.call.take"]
    pub fn wr_module_call_take(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.call.respond"]
    pub fn wr_module_call_respond(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.call.result"]
    pub fn wr_module_call_result(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.call.acknowledge"]
    pub fn wr_module_call_acknowledge(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "module.call.cancel"]
    pub fn wr_module_call_cancel(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "driver.connect"]
    pub fn wr_driver_connect(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "driver.submit"]
    pub fn wr_driver_submit(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "driver.result"]
    pub fn wr_driver_result(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "driver.describe"]
    pub fn wr_driver_describe(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
    #[link_name = "driver.disconnect"]
    pub fn wr_driver_disconnect(arg0: u64, arg1: u32, arg2: u64, arg3: u64, arg4: u64, arg5: u64, arg6: u64) -> u32;
}
