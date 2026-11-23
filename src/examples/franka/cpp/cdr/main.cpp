#include <uwrosv2/franka/cdr/records.hpp>
#include "elbow_frames.h"

namespace cdr = uwrosv2::franka::cdr;
namespace arm = cdr::franka_msgs;
namespace spine = cdr::franka_spine_msgs;

static bool transcode_elbow(const volatile uint8_t *source, const uint8_t *expected,
                            cdr::endian order) UWROSV2_FRANKA_CDR_NOEXCEPT {
    uint8_t input[sizeof elbow_be], output[sizeof elbow_be];
    for (size_t i = 0; i < sizeof input; ++i) input[i] = source[i];
    arm::Elbow elbow;
    size_t written;
    return cdr::decode(input, sizeof input, elbow)
        && elbow.position[0] == 1.125 && elbow.desired_position[0] == -0.75
        && elbow.commanded_position[0] == 0.25 && elbow.commanded_velocity[0] == 0.03125
        && elbow.commanded_acceleration[0] == 0.125
        && cdr::encode(elbow, order, output, sizeof output, written)
        && written == sizeof output && memcmp(output, expected, written) == 0;
}

/* Joint data from franka_hardware/test/ptp_motion_test.cpp in the pinned Franka release. */
static bool read_goal() UWROSV2_FRANKA_CDR_NOEXCEPT {
    const double positions[] = {0, -1, 0, -2, 0, 1.5, 0.5};
    const double velocities[] = {1, 1, 1, 1, 1, 1, 1};
    typedef arm::PTPMotion::SendGoal::Request Request;
    Request request = Request::defaults(), decoded;
    request.goal.goal_joint_configuration = cdr::Sequence<double>::from_values(positions, 7);
    request.goal.maximum_joint_velocities = cdr::Sequence<double>::from_values(velocities, 7);
    request.goal.goal_tolerance = 0.01;
    uint8_t bytes[192];
    size_t written;
    if (!cdr::encode(request, cdr::big_endian, bytes, sizeof bytes, written) ||
        !cdr::decode(bytes, written, decoded) || decoded.goal.goal_tolerance != 0.01 ||
        decoded.goal.goal_joint_configuration.size() != 7) return false;
    cdr::Sequence<double>::iterator it = decoded.goal.goal_joint_configuration.iter();
    for (size_t i = 0; i < 7; ++i) {
        double joint;
        if (!it.next(joint) || joint != positions[i]) return false;
    }
    return true;
}

/* The upstream spine server's concurrent GetPosition sample reports 0.42 metres. */
static bool read_position_service() UWROSV2_FRANKA_CDR_NOEXCEPT {
    typedef spine::GetPosition Service;
    const Service::Request query = Service::Request::defaults();
    Service::Request received;
    uint8_t bytes[128];
    size_t written;
    if (!cdr::encode(query, cdr::big_endian, bytes, sizeof bytes, written) || written != 5 ||
        !cdr::decode(bytes, written, received) || received.structure_needs_at_least_one_member != 0) return false;
    const Service::Response response = {0.42, true};
    Service::Event event = Service::Event::defaults(), recorded;
    event.info.event_type = cdr::service_msgs::ServiceEventInfo::RESPONSE_SENT;
    event.response = cdr::Sequence<Service::Response>::from_values(&response, 1);
    if (!cdr::encode(event, cdr::little_endian, bytes, sizeof bytes, written) ||
        !cdr::decode(bytes, written, recorded) || recorded.request.size() != 0 || recorded.response.size() != 1) return false;
    Service::Response observed;
    return recorded.response.iter().next(observed) && observed.success && observed.position == 0.42;
}

extern "C" void _start() UWROSV2_FRANKA_CDR_NOEXCEPT {
    if (!transcode_elbow(elbow_be, elbow_le, cdr::little_endian) ||
        !transcode_elbow(elbow_le, elbow_be, cdr::big_endian) ||
        !read_goal() || !read_position_service()) __builtin_trap();
}
