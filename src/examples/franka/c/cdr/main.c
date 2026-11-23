#include <uwrosv2/franka/cdr/records.h>
#include "elbow_frames.h"

typedef uwrosv2_franka_cdr_franka_msgs_Elbow Elbow;
typedef uwrosv2_franka_cdr_franka_msgs_PTPMotion_SendGoal_Request SendGoal;
typedef uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Request Query;
typedef uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Response Reply;
typedef uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Event Event;

static int transcode_elbow(const volatile uint8_t *source, const uint8_t *expected,
                           uwrosv2_franka_cdr_endian order) {
    uint8_t input[sizeof elbow_be], output[sizeof elbow_be];
    size_t written;
    Elbow elbow;
    for (size_t i = 0; i < sizeof input; ++i) input[i] = source[i];
    if (!uwrosv2_franka_cdr_franka_msgs_Elbow_decode(input, sizeof input, &elbow)) return 0;
    if (elbow.position[0] != 1.125 || elbow.desired_position[0] != -0.75 ||
        elbow.commanded_position[0] != 0.25 || elbow.commanded_velocity[0] != 0.03125 ||
        elbow.commanded_acceleration[0] != 0.125) return 0;
    return uwrosv2_franka_cdr_franka_msgs_Elbow_encode(&elbow, order, output, sizeof output, &written)
        && written == sizeof output && memcmp(output, expected, written) == 0;
}

/* Joint data from franka_hardware/test/ptp_motion_test.cpp in the pinned Franka release. */
static int read_goal(void) {
    const double positions[] = {0, -1, 0, -2, 0, 1.5, 0.5};
    const double velocities[] = {1, 1, 1, 1, 1, 1, 1};
    SendGoal request = uwrosv2_franka_cdr_franka_msgs_PTPMotion_SendGoal_Request_defaults();
    SendGoal decoded;
    uint8_t bytes[192];
    size_t written;
    request.goal.goal_joint_configuration = uwrosv2_franka_cdr_float64_sequence_values(positions, 7);
    request.goal.maximum_joint_velocities = uwrosv2_franka_cdr_float64_sequence_values(velocities, 7);
    request.goal.goal_tolerance = 0.01;
    if (!uwrosv2_franka_cdr_franka_msgs_PTPMotion_SendGoal_Request_encode(
            &request, uwrosv2_franka_cdr_big_endian, bytes, sizeof bytes, &written) ||
        !uwrosv2_franka_cdr_franka_msgs_PTPMotion_SendGoal_Request_decode(bytes, written, &decoded) ||
        decoded.goal.goal_tolerance != 0.01 || decoded.goal.goal_joint_configuration.count != 7) return 0;
    uwrosv2_franka_cdr_float64_sequence_iterator it =
        uwrosv2_franka_cdr_float64_sequence_iter(&decoded.goal.goal_joint_configuration);
    for (size_t i = 0; i < 7; ++i) {
        double joint;
        if (!uwrosv2_franka_cdr_float64_sequence_next(&it, &joint) || joint != positions[i]) return 0;
    }
    return 1;
}

/* GetPosition cache test in the upstream spine server reports success and 0.42 metres. */
static int read_position_service(void) {
    Query request = uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Request_defaults(), received;
    Reply response = {0.42, 1}, observed;
    Event event = uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Event_defaults(), recorded;
    uint8_t bytes[128];
    size_t written;
    if (!uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Request_encode(
            &request, uwrosv2_franka_cdr_big_endian, bytes, sizeof bytes, &written) ||
        written != 5 || !uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Request_decode(bytes, written, &received) ||
        received.structure_needs_at_least_one_member != 0) return 0;
    event.info.event_type = uwrosv2_franka_cdr_service_msgs_ServiceEventInfo_RESPONSE_SENT;
    event.response = uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Response_sequence_values(&response, 1);
    if (!uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Event_encode(
            &event, uwrosv2_franka_cdr_little_endian, bytes, sizeof bytes, &written) ||
        !uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Event_decode(bytes, written, &recorded) ||
        recorded.request.count != 0 || recorded.response.count != 1) return 0;
    uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Response_sequence_iterator it =
        uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Response_sequence_iter(&recorded.response);
    return uwrosv2_franka_cdr_franka_spine_msgs_GetPosition_Response_sequence_next(&it, &observed)
        && observed.success && observed.position == 0.42;
}

void _start(void) {
    if (!transcode_elbow(elbow_be, elbow_le, uwrosv2_franka_cdr_little_endian) ||
        !transcode_elbow(elbow_le, elbow_be, uwrosv2_franka_cdr_big_endian) ||
        !read_goal() || !read_position_service()) __builtin_trap();
}
