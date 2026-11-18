## Fixed-width Wasm imports supplied by the ROSv2 VM.
## Address arguments select a guest linear memory. Retain all pointer bits.
template wrAddress*(p: pointer): uint64 = uint64(cast[uint](p))

proc wr_abi*(): uint32
  {.importc: "wr_abi", header: "wros/scene.h".}

proc wr_capability_open*(a0: uint32, a1: uint64, a2: uint64, a3: uint64): uint32
  {.importc: "wr_capability_open", header: "wros/scene.h".}

proc wr_capability_close*(a0: uint64): uint32
  {.importc: "wr_capability_close", header: "wros/scene.h".}

proc wr_guard_create*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_guard_create", header: "wros/scene.h".}

proc wr_guard_trigger*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_guard_trigger", header: "wros/scene.h".}

proc wr_guard_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_guard_take", header: "wros/scene.h".}

proc wr_clock_create*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_clock_create", header: "wros/scene.h".}

proc wr_clock_read*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_clock_read", header: "wros/scene.h".}

proc wr_clock_update*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_clock_update", header: "wros/scene.h".}

proc wr_timer_create*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_timer_create", header: "wros/scene.h".}

proc wr_timer_reset*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_timer_reset", header: "wros/scene.h".}

proc wr_timer_cancel*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_timer_cancel", header: "wros/scene.h".}

proc wr_timer_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_timer_take", header: "wros/scene.h".}

proc wr_wait_create*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_wait_create", header: "wros/scene.h".}

proc wr_wait_add*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_wait_add", header: "wros/scene.h".}

proc wr_wait_remove*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_wait_remove", header: "wros/scene.h".}

proc wr_wait_acknowledge*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_wait_acknowledge", header: "wros/scene.h".}

proc wr_wait_poll*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_wait_poll", header: "wros/scene.h".}

proc wr_resource_close*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_resource_close", header: "wros/scene.h".}

proc wr_context_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_context_open", header: "wros/scene.h".}

proc wr_context_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_context_describe", header: "wros/scene.h".}

proc wr_context_shutdown*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_context_shutdown", header: "wros/scene.h".}

proc wr_node_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_node_open", header: "wros/scene.h".}

proc wr_node_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_node_describe", header: "wros/scene.h".}

proc wr_type_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_type_describe", header: "wros/scene.h".}

proc wr_topic_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_topic_open", header: "wros/scene.h".}

proc wr_topic_publish*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_topic_publish", header: "wros/scene.h".}

proc wr_topic_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_topic_take", header: "wros/scene.h".}

proc wr_topic_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_topic_describe", header: "wros/scene.h".}

proc wr_qos_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_qos_describe", header: "wros/scene.h".}

proc wr_qos_liveliness_assert*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_qos_liveliness_assert", header: "wros/scene.h".}

proc wr_qos_acknowledgements_wait*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_qos_acknowledgements_wait", header: "wros/scene.h".}

proc wr_service_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_open", header: "wros/scene.h".}

proc wr_service_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_submit", header: "wros/scene.h".}

proc wr_service_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_take", header: "wros/scene.h".}

proc wr_service_respond*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_respond", header: "wros/scene.h".}

proc wr_service_available*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_available", header: "wros/scene.h".}

proc wr_service_abandon*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_abandon", header: "wros/scene.h".}

proc wr_action_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_action_open", header: "wros/scene.h".}

proc wr_action_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_action_submit", header: "wros/scene.h".}

proc wr_action_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_action_take", header: "wros/scene.h".}

proc wr_action_respond*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_action_respond", header: "wros/scene.h".}

proc wr_action_cancel*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_action_cancel", header: "wros/scene.h".}

proc wr_action_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_action_describe", header: "wros/scene.h".}

proc wr_parameter_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_open", header: "wros/scene.h".}

proc wr_parameter_declare*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_declare", header: "wros/scene.h".}

proc wr_parameter_undeclare*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_undeclare", header: "wros/scene.h".}

proc wr_parameter_get*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_get", header: "wros/scene.h".}

proc wr_parameter_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_describe", header: "wros/scene.h".}

proc wr_parameter_list*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_list", header: "wros/scene.h".}

proc wr_parameter_set*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_set", header: "wros/scene.h".}

proc wr_parameter_set_atomic*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_set_atomic", header: "wros/scene.h".}

proc wr_parameter_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_take", header: "wros/scene.h".}

proc wr_parameter_respond*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_respond", header: "wros/scene.h".}

proc wr_lifecycle_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_lifecycle_open", header: "wros/scene.h".}

proc wr_lifecycle_state*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_lifecycle_state", header: "wros/scene.h".}

proc wr_lifecycle_transitions*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_lifecycle_transitions", header: "wros/scene.h".}

proc wr_lifecycle_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_lifecycle_submit", header: "wros/scene.h".}

proc wr_lifecycle_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_lifecycle_take", header: "wros/scene.h".}

proc wr_lifecycle_respond*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_lifecycle_respond", header: "wros/scene.h".}

proc wr_transform_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_open", header: "wros/scene.h".}

proc wr_transform_publish*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_publish", header: "wros/scene.h".}

proc wr_transform_lookup*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_lookup", header: "wros/scene.h".}

proc wr_transform_available*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_available", header: "wros/scene.h".}

proc wr_transform_velocity*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_velocity", header: "wros/scene.h".}

proc wr_transform_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_submit", header: "wros/scene.h".}

proc wr_transform_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_take", header: "wros/scene.h".}

proc wr_transform_cancel*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_cancel", header: "wros/scene.h".}

proc wr_transform_clear*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_transform_clear", header: "wros/scene.h".}

proc wr_graph_snapshot*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_graph_snapshot", header: "wros/scene.h".}

proc wr_graph_watch*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_graph_watch", header: "wros/scene.h".}

proc wr_event_stream_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_event_stream_open", header: "wros/scene.h".}

proc wr_event_stream_poll*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_event_stream_poll", header: "wros/scene.h".}

proc wr_event_stream_close*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_event_stream_close", header: "wros/scene.h".}

proc wr_buffer_create*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_buffer_create", header: "wros/scene.h".}

proc wr_buffer_write*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_buffer_write", header: "wros/scene.h".}

proc wr_buffer_seal*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_buffer_seal", header: "wros/scene.h".}

proc wr_buffer_read*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_buffer_read", header: "wros/scene.h".}

proc wr_buffer_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_buffer_describe", header: "wros/scene.h".}

proc wr_artifact_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_open", header: "wros/scene.h".}

proc wr_artifact_read*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_read", header: "wros/scene.h".}

proc wr_artifact_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_describe", header: "wros/scene.h".}

proc wr_artifact_begin*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_begin", header: "wros/scene.h".}

proc wr_artifact_append*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_append", header: "wros/scene.h".}

proc wr_artifact_commit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_commit", header: "wros/scene.h".}

proc wr_artifact_abort*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_abort", header: "wros/scene.h".}

proc wr_artifact_remove*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_remove", header: "wros/scene.h".}

proc wr_sensor_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_sensor_open", header: "wros/scene.h".}

proc wr_sensor_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_sensor_take", header: "wros/scene.h".}

proc wr_sensor_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_sensor_describe", header: "wros/scene.h".}

proc wr_device_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_device_open", header: "wros/scene.h".}

proc wr_device_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_device_submit", header: "wros/scene.h".}

proc wr_device_result*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_device_result", header: "wros/scene.h".}

proc wr_device_stop*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_device_stop", header: "wros/scene.h".}

proc wr_device_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_device_describe", header: "wros/scene.h".}

proc wr_control_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_control_open", header: "wros/scene.h".}

proc wr_control_sample*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_control_sample", header: "wros/scene.h".}

proc wr_control_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_control_submit", header: "wros/scene.h".}

proc wr_control_result*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_control_result", header: "wros/scene.h".}

proc wr_control_stop*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_control_stop", header: "wros/scene.h".}

proc wr_media_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_media_open", header: "wros/scene.h".}

proc wr_media_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_media_submit", header: "wros/scene.h".}

proc wr_media_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_media_take", header: "wros/scene.h".}

proc wr_media_close*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_media_close", header: "wros/scene.h".}

proc wr_recording_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_recording_open", header: "wros/scene.h".}

proc wr_recording_append*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_recording_append", header: "wros/scene.h".}

proc wr_recording_checkpoint*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_recording_checkpoint", header: "wros/scene.h".}

proc wr_recording_stop*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_recording_stop", header: "wros/scene.h".}

proc wr_replay_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_replay_open", header: "wros/scene.h".}

proc wr_replay_read*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_replay_read", header: "wros/scene.h".}

proc wr_replay_seek*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_replay_seek", header: "wros/scene.h".}

proc wr_model_open*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_model_open", header: "wros/scene.h".}

proc wr_model_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_model_submit", header: "wros/scene.h".}

proc wr_model_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_model_take", header: "wros/scene.h".}

proc wr_model_cancel*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_model_cancel", header: "wros/scene.h".}

proc wr_model_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_model_describe", header: "wros/scene.h".}

proc wr_proposal_read*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_proposal_read", header: "wros/scene.h".}

proc wr_proposal_accept*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_proposal_accept", header: "wros/scene.h".}

proc wr_bridge_create*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_bridge_create", header: "wros/scene.h".}

proc wr_bridge_start*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_bridge_start", header: "wros/scene.h".}

proc wr_bridge_stop*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_bridge_stop", header: "wros/scene.h".}

proc wr_bridge_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_bridge_describe", header: "wros/scene.h".}

proc wr_log_emit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_log_emit", header: "wros/scene.h".}

proc wr_diagnostic_read*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_diagnostic_read", header: "wros/scene.h".}

proc wr_request_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_request_describe", header: "wros/scene.h".}

proc wr_request_release*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_request_release", header: "wros/scene.h".}

proc wr_artifact_status*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_status", header: "wros/scene.h".}

proc wr_artifact_receipt*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_receipt", header: "wros/scene.h".}

proc wr_artifact_publish*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_artifact_publish", header: "wros/scene.h".}

proc wr_proposal_capture*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_proposal_capture", header: "wros/scene.h".}

proc wr_proposal_publish*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_proposal_publish", header: "wros/scene.h".}

proc wr_communication_open_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_communication_open_take", header: "wros/scene.h".}

proc wr_communication_open_cancel*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_communication_open_cancel", header: "wros/scene.h".}

proc wr_capability_revoke*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_capability_revoke", header: "wros/scene.h".}

proc wr_topic_reserve*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_topic_reserve", header: "wros/scene.h".}

proc wr_topic_acknowledge*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_topic_acknowledge", header: "wros/scene.h".}

proc wr_topic_release*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_topic_release", header: "wros/scene.h".}

proc wr_service_reserve*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_reserve", header: "wros/scene.h".}

proc wr_service_acknowledge*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_acknowledge", header: "wros/scene.h".}

proc wr_service_release*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_release", header: "wros/scene.h".}

proc wr_parameter_exists*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_exists", header: "wros/scene.h".}

proc wr_parameter_search*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_parameter_search", header: "wros/scene.h".}

proc wr_action_cancel_set*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_action_cancel_set", header: "wros/scene.h".}

proc wr_service_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_service_describe", header: "wros/scene.h".}

proc wr_permission_report*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_permission_report", header: "wros/scene.h".}

proc wr_module_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_describe", header: "wros/scene.h".}

proc wr_module_imports*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_imports", header: "wros/scene.h".}

proc wr_module_exports*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_exports", header: "wros/scene.h".}

proc wr_module_group*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_group", header: "wros/scene.h".}

proc wr_module_permission_report*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_permission_report", header: "wros/scene.h".}

proc wr_module_importers*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_importers", header: "wros/scene.h".}

proc wr_vm_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_vm_describe", header: "wros/scene.h".}

proc wr_module_call_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_call_submit", header: "wros/scene.h".}

proc wr_module_call_take*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_call_take", header: "wros/scene.h".}

proc wr_module_call_respond*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_call_respond", header: "wros/scene.h".}

proc wr_module_call_result*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_call_result", header: "wros/scene.h".}

proc wr_module_call_acknowledge*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_call_acknowledge", header: "wros/scene.h".}

proc wr_module_call_cancel*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_module_call_cancel", header: "wros/scene.h".}

proc wr_driver_connect*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_driver_connect", header: "wros/scene.h".}

proc wr_driver_submit*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_driver_submit", header: "wros/scene.h".}

proc wr_driver_result*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_driver_result", header: "wros/scene.h".}

proc wr_driver_describe*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_driver_describe", header: "wros/scene.h".}

proc wr_driver_disconnect*(a0: uint64, a1: uint32, a2: uint64, a3: uint64, a4: uint64, a5: uint64, a6: uint64): uint32
  {.importc: "wr_driver_disconnect", header: "wros/scene.h".}
