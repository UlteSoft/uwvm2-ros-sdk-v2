#include <uwrosv2/abb/ros1/records.hpp>
#include <string.h>

namespace ros = uwrosv2::abb::ros1;
namespace robot = ros::abb_robot_msgs;

static ros::String text(const char *s) UWROSV2_ABB_ROS1_NOEXCEPT {
    const ros::String result = {reinterpret_cast<const uint8_t *>(s), strlen(s)};
    return result;
}

static bool equals(ros::String field, const char *s) UWROSV2_ABB_ROS1_NOEXCEPT {
    return field.size == strlen(s) && (!field.size || memcmp(field.data, s, field.size) == 0);
}

/* A local service handler supplies a sample measurement for a known RAPID symbol. */
static bool read_symbol(const uint8_t *query, size_t size, uint8_t *reply,
                        size_t capacity, size_t &written) UWROSV2_ABB_ROS1_NOEXCEPT {
    robot::GetRAPIDNum::Request request;
    if (!ros::decode(query, size, request)) return false;
    robot::GetRAPIDNum::Response response;
    if (equals(request.path.task, "T_ROB1") && equals(request.path.module, "Survey")
        && equals(request.path.symbol, "sample")) {
        response.value = 12.5f;
        response.result_code = robot::ServiceResponses::RC_SUCCESS;
        response.message = text("");
    } else {
        response.value = 0;
        response.result_code = robot::ServiceResponses::RC_FAILED;
        response.message = text("Unknown symbol");
    }
    return ros::encode(response, reply, capacity, written);
}

static bool service_exchange() UWROSV2_ABB_ROS1_NOEXCEPT {
    uint8_t query[64], reply[64];
    size_t query_size, reply_size;
    const robot::GetRAPIDNum::Request request = {{text("T_ROB1"), text("Survey"), text("sample")}};
    robot::GetRAPIDNum::Response response;
    return ros::encode(request, query, sizeof query, query_size)
        && read_symbol(query, query_size, reply, sizeof reply, reply_size)
        && ros::decode(reply, reply_size, response)
        && response.result_code == robot::ServiceResponses::RC_SUCCESS
        && response.value == 12.5f && response.message.size == 0;
}

static bool inspect_system() UWROSV2_ABB_ROS1_NOEXCEPT {
    const robot::RAPIDTaskState tasks[] = {{text("T_ROB1"), true, robot::RAPIDTaskState::EXECUTION_STATE_STARTED, true}};
    const robot::MechanicalUnitState units[] = {{text("ROB_1"), true}};
    robot::SystemState state = robot::SystemState();
    state.header.seq = 7;
    state.header.stamp.sec = 42;
    state.header.frame_id = text("base");
    state.motors_on = true;
    state.rapid_running = true;
    state.rapid_tasks = ros::Sequence<robot::RAPIDTaskState>::from_values(tasks, 1);
    state.mechanical_units = ros::Sequence<robot::MechanicalUnitState>::from_values(units, 1);
    uint8_t payload[128];
    size_t size;
    robot::SystemState received;
    if (!ros::encode(state, payload, sizeof payload, size) || !ros::decode(payload, size, received)) return false;
    robot::RAPIDTaskState task;
    robot::MechanicalUnitState unit;
    return equals(received.header.frame_id, "base") && received.header.stamp.sec == 42
        && received.rapid_tasks.iter().next(task) && equals(task.name, "T_ROB1") && task.motion_task
        && received.mechanical_units.iter().next(unit) && equals(unit.name, "ROB_1") && unit.activated;
}

extern "C" void _start() UWROSV2_ABB_ROS1_NOEXCEPT {
    if (!service_exchange() || !inspect_system()) __builtin_trap();
}
