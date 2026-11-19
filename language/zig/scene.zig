//! Generated ROSv2 raw bindings. Preserve pointer tag bits in every address argument.
//! Request and result layouts are defined in share/abi/ros.json.

extern "uwvm_ros_v2" fn @"abi"() u32;
/// @brief Invoke the registered `abi` operation.
pub const wr_abi = @"abi";

extern "uwvm_ros_v2" fn @"capability.open"(memory: u32, alias: u64, length: u64, result: u64) u32;
/// @brief Invoke the registered `capability.open` operation.
pub const wr_capability_open = @"capability.open";

extern "uwvm_ros_v2" fn @"capability.close"(capability: u64) u32;
/// @brief Invoke the registered `capability.close` operation.
pub const wr_capability_close = @"capability.close";

extern "uwvm_ros_v2" fn @"guard.create"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `guard.create` operation.
pub const wr_guard_create = @"guard.create";

extern "uwvm_ros_v2" fn @"guard.trigger"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `guard.trigger` operation.
pub const wr_guard_trigger = @"guard.trigger";

extern "uwvm_ros_v2" fn @"guard.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `guard.take` operation.
pub const wr_guard_take = @"guard.take";

extern "uwvm_ros_v2" fn @"clock.create"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `clock.create` operation.
pub const wr_clock_create = @"clock.create";

extern "uwvm_ros_v2" fn @"clock.read"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `clock.read` operation.
pub const wr_clock_read = @"clock.read";

extern "uwvm_ros_v2" fn @"clock.update"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `clock.update` operation.
pub const wr_clock_update = @"clock.update";

extern "uwvm_ros_v2" fn @"timer.create"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `timer.create` operation.
pub const wr_timer_create = @"timer.create";

extern "uwvm_ros_v2" fn @"timer.reset"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `timer.reset` operation.
pub const wr_timer_reset = @"timer.reset";

extern "uwvm_ros_v2" fn @"timer.cancel"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `timer.cancel` operation.
pub const wr_timer_cancel = @"timer.cancel";

extern "uwvm_ros_v2" fn @"timer.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `timer.take` operation.
pub const wr_timer_take = @"timer.take";

extern "uwvm_ros_v2" fn @"wait.create"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `wait.create` operation.
pub const wr_wait_create = @"wait.create";

extern "uwvm_ros_v2" fn @"wait.add"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `wait.add` operation.
pub const wr_wait_add = @"wait.add";

extern "uwvm_ros_v2" fn @"wait.remove"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `wait.remove` operation.
pub const wr_wait_remove = @"wait.remove";

extern "uwvm_ros_v2" fn @"wait.acknowledge"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `wait.acknowledge` operation.
pub const wr_wait_acknowledge = @"wait.acknowledge";

extern "uwvm_ros_v2" fn @"wait.poll"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `wait.poll` operation.
pub const wr_wait_poll = @"wait.poll";

extern "uwvm_ros_v2" fn @"resource.close"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `resource.close` operation.
pub const wr_resource_close = @"resource.close";

extern "uwvm_ros_v2" fn @"context.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `context.open` operation.
pub const wr_context_open = @"context.open";

extern "uwvm_ros_v2" fn @"context.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `context.describe` operation.
pub const wr_context_describe = @"context.describe";

extern "uwvm_ros_v2" fn @"context.shutdown"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `context.shutdown` operation.
pub const wr_context_shutdown = @"context.shutdown";

extern "uwvm_ros_v2" fn @"node.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `node.open` operation.
pub const wr_node_open = @"node.open";

extern "uwvm_ros_v2" fn @"node.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `node.describe` operation.
pub const wr_node_describe = @"node.describe";

extern "uwvm_ros_v2" fn @"type.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `type.describe` operation.
pub const wr_type_describe = @"type.describe";

extern "uwvm_ros_v2" fn @"topic.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `topic.open` operation.
pub const wr_topic_open = @"topic.open";

extern "uwvm_ros_v2" fn @"topic.publish"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `topic.publish` operation.
pub const wr_topic_publish = @"topic.publish";

extern "uwvm_ros_v2" fn @"topic.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `topic.take` operation.
pub const wr_topic_take = @"topic.take";

extern "uwvm_ros_v2" fn @"topic.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `topic.describe` operation.
pub const wr_topic_describe = @"topic.describe";

extern "uwvm_ros_v2" fn @"qos.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `qos.describe` operation.
pub const wr_qos_describe = @"qos.describe";

extern "uwvm_ros_v2" fn @"qos.liveliness.assert"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `qos.liveliness.assert` operation.
pub const wr_qos_liveliness_assert = @"qos.liveliness.assert";

extern "uwvm_ros_v2" fn @"qos.acknowledgements.wait"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `qos.acknowledgements.wait` operation.
pub const wr_qos_acknowledgements_wait = @"qos.acknowledgements.wait";

extern "uwvm_ros_v2" fn @"service.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.open` operation.
pub const wr_service_open = @"service.open";

extern "uwvm_ros_v2" fn @"service.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.submit` operation.
pub const wr_service_submit = @"service.submit";

extern "uwvm_ros_v2" fn @"service.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.take` operation.
pub const wr_service_take = @"service.take";

extern "uwvm_ros_v2" fn @"service.respond"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.respond` operation.
pub const wr_service_respond = @"service.respond";

extern "uwvm_ros_v2" fn @"service.available"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.available` operation.
pub const wr_service_available = @"service.available";

extern "uwvm_ros_v2" fn @"service.abandon"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.abandon` operation.
pub const wr_service_abandon = @"service.abandon";

extern "uwvm_ros_v2" fn @"action.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `action.open` operation.
pub const wr_action_open = @"action.open";

extern "uwvm_ros_v2" fn @"action.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `action.submit` operation.
pub const wr_action_submit = @"action.submit";

extern "uwvm_ros_v2" fn @"action.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `action.take` operation.
pub const wr_action_take = @"action.take";

extern "uwvm_ros_v2" fn @"action.respond"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `action.respond` operation.
pub const wr_action_respond = @"action.respond";

extern "uwvm_ros_v2" fn @"action.cancel"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `action.cancel` operation.
pub const wr_action_cancel = @"action.cancel";

extern "uwvm_ros_v2" fn @"action.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `action.describe` operation.
pub const wr_action_describe = @"action.describe";

extern "uwvm_ros_v2" fn @"parameter.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.open` operation.
pub const wr_parameter_open = @"parameter.open";

extern "uwvm_ros_v2" fn @"parameter.declare"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.declare` operation.
pub const wr_parameter_declare = @"parameter.declare";

extern "uwvm_ros_v2" fn @"parameter.undeclare"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.undeclare` operation.
pub const wr_parameter_undeclare = @"parameter.undeclare";

extern "uwvm_ros_v2" fn @"parameter.get"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.get` operation.
pub const wr_parameter_get = @"parameter.get";

extern "uwvm_ros_v2" fn @"parameter.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.describe` operation.
pub const wr_parameter_describe = @"parameter.describe";

extern "uwvm_ros_v2" fn @"parameter.list"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.list` operation.
pub const wr_parameter_list = @"parameter.list";

extern "uwvm_ros_v2" fn @"parameter.set"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.set` operation.
pub const wr_parameter_set = @"parameter.set";

extern "uwvm_ros_v2" fn @"parameter.set.atomic"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.set.atomic` operation.
pub const wr_parameter_set_atomic = @"parameter.set.atomic";

extern "uwvm_ros_v2" fn @"parameter.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.take` operation.
pub const wr_parameter_take = @"parameter.take";

extern "uwvm_ros_v2" fn @"parameter.respond"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.respond` operation.
pub const wr_parameter_respond = @"parameter.respond";

extern "uwvm_ros_v2" fn @"lifecycle.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `lifecycle.open` operation.
pub const wr_lifecycle_open = @"lifecycle.open";

extern "uwvm_ros_v2" fn @"lifecycle.state"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `lifecycle.state` operation.
pub const wr_lifecycle_state = @"lifecycle.state";

extern "uwvm_ros_v2" fn @"lifecycle.transitions"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `lifecycle.transitions` operation.
pub const wr_lifecycle_transitions = @"lifecycle.transitions";

extern "uwvm_ros_v2" fn @"lifecycle.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `lifecycle.submit` operation.
pub const wr_lifecycle_submit = @"lifecycle.submit";

extern "uwvm_ros_v2" fn @"lifecycle.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `lifecycle.take` operation.
pub const wr_lifecycle_take = @"lifecycle.take";

extern "uwvm_ros_v2" fn @"lifecycle.respond"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `lifecycle.respond` operation.
pub const wr_lifecycle_respond = @"lifecycle.respond";

extern "uwvm_ros_v2" fn @"transform.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.open` operation.
pub const wr_transform_open = @"transform.open";

extern "uwvm_ros_v2" fn @"transform.publish"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.publish` operation.
pub const wr_transform_publish = @"transform.publish";

extern "uwvm_ros_v2" fn @"transform.lookup"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.lookup` operation.
pub const wr_transform_lookup = @"transform.lookup";

extern "uwvm_ros_v2" fn @"transform.available"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.available` operation.
pub const wr_transform_available = @"transform.available";

extern "uwvm_ros_v2" fn @"transform.velocity"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.velocity` operation.
pub const wr_transform_velocity = @"transform.velocity";

extern "uwvm_ros_v2" fn @"transform.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.submit` operation.
pub const wr_transform_submit = @"transform.submit";

extern "uwvm_ros_v2" fn @"transform.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.take` operation.
pub const wr_transform_take = @"transform.take";

extern "uwvm_ros_v2" fn @"transform.cancel"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.cancel` operation.
pub const wr_transform_cancel = @"transform.cancel";

extern "uwvm_ros_v2" fn @"transform.clear"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `transform.clear` operation.
pub const wr_transform_clear = @"transform.clear";

extern "uwvm_ros_v2" fn @"graph.snapshot"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `graph.snapshot` operation.
pub const wr_graph_snapshot = @"graph.snapshot";

extern "uwvm_ros_v2" fn @"graph.watch"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `graph.watch` operation.
pub const wr_graph_watch = @"graph.watch";

extern "uwvm_ros_v2" fn @"event.stream.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `event.stream.open` operation.
pub const wr_event_stream_open = @"event.stream.open";

extern "uwvm_ros_v2" fn @"event.stream.poll"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `event.stream.poll` operation.
pub const wr_event_stream_poll = @"event.stream.poll";

extern "uwvm_ros_v2" fn @"event.stream.close"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `event.stream.close` operation.
pub const wr_event_stream_close = @"event.stream.close";

extern "uwvm_ros_v2" fn @"buffer.create"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `buffer.create` operation.
pub const wr_buffer_create = @"buffer.create";

extern "uwvm_ros_v2" fn @"buffer.write"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `buffer.write` operation.
pub const wr_buffer_write = @"buffer.write";

extern "uwvm_ros_v2" fn @"buffer.seal"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `buffer.seal` operation.
pub const wr_buffer_seal = @"buffer.seal";

extern "uwvm_ros_v2" fn @"buffer.read"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `buffer.read` operation.
pub const wr_buffer_read = @"buffer.read";

extern "uwvm_ros_v2" fn @"buffer.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `buffer.describe` operation.
pub const wr_buffer_describe = @"buffer.describe";

extern "uwvm_ros_v2" fn @"artifact.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.open` operation.
pub const wr_artifact_open = @"artifact.open";

extern "uwvm_ros_v2" fn @"artifact.read"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.read` operation.
pub const wr_artifact_read = @"artifact.read";

extern "uwvm_ros_v2" fn @"artifact.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.describe` operation.
pub const wr_artifact_describe = @"artifact.describe";

extern "uwvm_ros_v2" fn @"artifact.begin"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.begin` operation.
pub const wr_artifact_begin = @"artifact.begin";

extern "uwvm_ros_v2" fn @"artifact.append"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.append` operation.
pub const wr_artifact_append = @"artifact.append";

extern "uwvm_ros_v2" fn @"artifact.commit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.commit` operation.
pub const wr_artifact_commit = @"artifact.commit";

extern "uwvm_ros_v2" fn @"artifact.abort"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.abort` operation.
pub const wr_artifact_abort = @"artifact.abort";

extern "uwvm_ros_v2" fn @"artifact.remove"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.remove` operation.
pub const wr_artifact_remove = @"artifact.remove";

extern "uwvm_ros_v2" fn @"sensor.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `sensor.open` operation.
pub const wr_sensor_open = @"sensor.open";

extern "uwvm_ros_v2" fn @"sensor.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `sensor.take` operation.
pub const wr_sensor_take = @"sensor.take";

extern "uwvm_ros_v2" fn @"sensor.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `sensor.describe` operation.
pub const wr_sensor_describe = @"sensor.describe";

extern "uwvm_ros_v2" fn @"device.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `device.open` operation.
pub const wr_device_open = @"device.open";

extern "uwvm_ros_v2" fn @"device.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `device.submit` operation.
pub const wr_device_submit = @"device.submit";

extern "uwvm_ros_v2" fn @"device.result"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `device.result` operation.
pub const wr_device_result = @"device.result";

extern "uwvm_ros_v2" fn @"device.stop"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `device.stop` operation.
pub const wr_device_stop = @"device.stop";

extern "uwvm_ros_v2" fn @"device.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `device.describe` operation.
pub const wr_device_describe = @"device.describe";

extern "uwvm_ros_v2" fn @"control.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `control.open` operation.
pub const wr_control_open = @"control.open";

extern "uwvm_ros_v2" fn @"control.sample"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `control.sample` operation.
pub const wr_control_sample = @"control.sample";

extern "uwvm_ros_v2" fn @"control.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `control.submit` operation.
pub const wr_control_submit = @"control.submit";

extern "uwvm_ros_v2" fn @"control.result"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `control.result` operation.
pub const wr_control_result = @"control.result";

extern "uwvm_ros_v2" fn @"control.stop"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `control.stop` operation.
pub const wr_control_stop = @"control.stop";

extern "uwvm_ros_v2" fn @"media.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `media.open` operation.
pub const wr_media_open = @"media.open";

extern "uwvm_ros_v2" fn @"media.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `media.submit` operation.
pub const wr_media_submit = @"media.submit";

extern "uwvm_ros_v2" fn @"media.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `media.take` operation.
pub const wr_media_take = @"media.take";

extern "uwvm_ros_v2" fn @"media.close"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `media.close` operation.
pub const wr_media_close = @"media.close";

extern "uwvm_ros_v2" fn @"recording.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `recording.open` operation.
pub const wr_recording_open = @"recording.open";

extern "uwvm_ros_v2" fn @"recording.append"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `recording.append` operation.
pub const wr_recording_append = @"recording.append";

extern "uwvm_ros_v2" fn @"recording.checkpoint"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `recording.checkpoint` operation.
pub const wr_recording_checkpoint = @"recording.checkpoint";

extern "uwvm_ros_v2" fn @"recording.stop"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `recording.stop` operation.
pub const wr_recording_stop = @"recording.stop";

extern "uwvm_ros_v2" fn @"replay.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `replay.open` operation.
pub const wr_replay_open = @"replay.open";

extern "uwvm_ros_v2" fn @"replay.read"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `replay.read` operation.
pub const wr_replay_read = @"replay.read";

extern "uwvm_ros_v2" fn @"replay.seek"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `replay.seek` operation.
pub const wr_replay_seek = @"replay.seek";

extern "uwvm_ros_v2" fn @"model.open"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `model.open` operation.
pub const wr_model_open = @"model.open";

extern "uwvm_ros_v2" fn @"model.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `model.submit` operation.
pub const wr_model_submit = @"model.submit";

extern "uwvm_ros_v2" fn @"model.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `model.take` operation.
pub const wr_model_take = @"model.take";

extern "uwvm_ros_v2" fn @"model.cancel"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `model.cancel` operation.
pub const wr_model_cancel = @"model.cancel";

extern "uwvm_ros_v2" fn @"model.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `model.describe` operation.
pub const wr_model_describe = @"model.describe";

extern "uwvm_ros_v2" fn @"proposal.read"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `proposal.read` operation.
pub const wr_proposal_read = @"proposal.read";

extern "uwvm_ros_v2" fn @"proposal.accept"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `proposal.accept` operation.
pub const wr_proposal_accept = @"proposal.accept";

extern "uwvm_ros_v2" fn @"bridge.create"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `bridge.create` operation.
pub const wr_bridge_create = @"bridge.create";

extern "uwvm_ros_v2" fn @"bridge.start"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `bridge.start` operation.
pub const wr_bridge_start = @"bridge.start";

extern "uwvm_ros_v2" fn @"bridge.stop"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `bridge.stop` operation.
pub const wr_bridge_stop = @"bridge.stop";

extern "uwvm_ros_v2" fn @"bridge.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `bridge.describe` operation.
pub const wr_bridge_describe = @"bridge.describe";

extern "uwvm_ros_v2" fn @"log.emit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `log.emit` operation.
pub const wr_log_emit = @"log.emit";

extern "uwvm_ros_v2" fn @"diagnostic.read"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `diagnostic.read` operation.
pub const wr_diagnostic_read = @"diagnostic.read";

extern "uwvm_ros_v2" fn @"request.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `request.describe` operation.
pub const wr_request_describe = @"request.describe";

extern "uwvm_ros_v2" fn @"request.release"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `request.release` operation.
pub const wr_request_release = @"request.release";

extern "uwvm_ros_v2" fn @"artifact.status"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.status` operation.
pub const wr_artifact_status = @"artifact.status";

extern "uwvm_ros_v2" fn @"artifact.receipt"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.receipt` operation.
pub const wr_artifact_receipt = @"artifact.receipt";

extern "uwvm_ros_v2" fn @"artifact.publish"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `artifact.publish` operation.
pub const wr_artifact_publish = @"artifact.publish";

extern "uwvm_ros_v2" fn @"proposal.capture"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `proposal.capture` operation.
pub const wr_proposal_capture = @"proposal.capture";

extern "uwvm_ros_v2" fn @"proposal.publish"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `proposal.publish` operation.
pub const wr_proposal_publish = @"proposal.publish";

extern "uwvm_ros_v2" fn @"communication.open.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `communication.open.take` operation.
pub const wr_communication_open_take = @"communication.open.take";

extern "uwvm_ros_v2" fn @"communication.open.cancel"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `communication.open.cancel` operation.
pub const wr_communication_open_cancel = @"communication.open.cancel";

extern "uwvm_ros_v2" fn @"capability.revoke"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `capability.revoke` operation.
pub const wr_capability_revoke = @"capability.revoke";

extern "uwvm_ros_v2" fn @"topic.reserve"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `topic.reserve` operation.
pub const wr_topic_reserve = @"topic.reserve";

extern "uwvm_ros_v2" fn @"topic.acknowledge"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `topic.acknowledge` operation.
pub const wr_topic_acknowledge = @"topic.acknowledge";

extern "uwvm_ros_v2" fn @"topic.release"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `topic.release` operation.
pub const wr_topic_release = @"topic.release";

extern "uwvm_ros_v2" fn @"service.reserve"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.reserve` operation.
pub const wr_service_reserve = @"service.reserve";

extern "uwvm_ros_v2" fn @"service.acknowledge"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.acknowledge` operation.
pub const wr_service_acknowledge = @"service.acknowledge";

extern "uwvm_ros_v2" fn @"service.release"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.release` operation.
pub const wr_service_release = @"service.release";

extern "uwvm_ros_v2" fn @"parameter.exists"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.exists` operation.
pub const wr_parameter_exists = @"parameter.exists";

extern "uwvm_ros_v2" fn @"parameter.search"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `parameter.search` operation.
pub const wr_parameter_search = @"parameter.search";

extern "uwvm_ros_v2" fn @"action.cancel.set"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `action.cancel.set` operation.
pub const wr_action_cancel_set = @"action.cancel.set";

extern "uwvm_ros_v2" fn @"service.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `service.describe` operation.
pub const wr_service_describe = @"service.describe";

extern "uwvm_ros_v2" fn @"permission.report"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `permission.report` operation.
pub const wr_permission_report = @"permission.report";

extern "uwvm_ros_v2" fn @"module.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.describe` operation.
pub const wr_module_describe = @"module.describe";

extern "uwvm_ros_v2" fn @"module.imports"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.imports` operation.
pub const wr_module_imports = @"module.imports";

extern "uwvm_ros_v2" fn @"module.exports"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.exports` operation.
pub const wr_module_exports = @"module.exports";

extern "uwvm_ros_v2" fn @"module.group"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.group` operation.
pub const wr_module_group = @"module.group";

extern "uwvm_ros_v2" fn @"module.permission.report"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.permission.report` operation.
pub const wr_module_permission_report = @"module.permission.report";

extern "uwvm_ros_v2" fn @"module.importers"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.importers` operation.
pub const wr_module_importers = @"module.importers";

extern "uwvm_ros_v2" fn @"vm.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `vm.describe` operation.
pub const wr_vm_describe = @"vm.describe";

extern "uwvm_ros_v2" fn @"module.call.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.call.submit` operation.
pub const wr_module_call_submit = @"module.call.submit";

extern "uwvm_ros_v2" fn @"module.call.take"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.call.take` operation.
pub const wr_module_call_take = @"module.call.take";

extern "uwvm_ros_v2" fn @"module.call.respond"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.call.respond` operation.
pub const wr_module_call_respond = @"module.call.respond";

extern "uwvm_ros_v2" fn @"module.call.result"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.call.result` operation.
pub const wr_module_call_result = @"module.call.result";

extern "uwvm_ros_v2" fn @"module.call.acknowledge"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.call.acknowledge` operation.
pub const wr_module_call_acknowledge = @"module.call.acknowledge";

extern "uwvm_ros_v2" fn @"module.call.cancel"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `module.call.cancel` operation.
pub const wr_module_call_cancel = @"module.call.cancel";

extern "uwvm_ros_v2" fn @"driver.connect"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `driver.connect` operation.
pub const wr_driver_connect = @"driver.connect";

extern "uwvm_ros_v2" fn @"driver.submit"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `driver.submit` operation.
pub const wr_driver_submit = @"driver.submit";

extern "uwvm_ros_v2" fn @"driver.result"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `driver.result` operation.
pub const wr_driver_result = @"driver.result";

extern "uwvm_ros_v2" fn @"driver.describe"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `driver.describe` operation.
pub const wr_driver_describe = @"driver.describe";

extern "uwvm_ros_v2" fn @"driver.disconnect"(capability: u64, memory: u32, request: u64, length: u64, reply: u64, capacity: u64, written: u64) u32;
/// @brief Invoke the registered `driver.disconnect` operation.
pub const wr_driver_disconnect = @"driver.disconnect";
