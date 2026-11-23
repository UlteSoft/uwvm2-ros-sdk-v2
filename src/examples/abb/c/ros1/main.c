#include <uwrosv2/abb/ros1/records.h>
#include <string.h>

typedef uwrosv2_abb_ros1_abb_robot_msgs_RAPIDTaskState Task;
typedef uwrosv2_abb_ros1_abb_robot_msgs_MechanicalUnitState Unit;
typedef uwrosv2_abb_ros1_abb_robot_msgs_SystemState SystemState;
typedef uwrosv2_abb_ros1_abb_robot_msgs_GetRAPIDNumRequest Query;
typedef uwrosv2_abb_ros1_abb_robot_msgs_GetRAPIDNumResponse Reply;

static uwrosv2_abb_ros1_string text(const char *s) {
    uwrosv2_abb_ros1_string result = {(const uint8_t *)s, strlen(s)};
    return result;
}

static int equals(uwrosv2_abb_ros1_string field, const char *s) {
    return field.size == strlen(s) && (!field.size || memcmp(field.data, s, field.size) == 0);
}

/* A local service handler supplies a sample measurement for a known RAPID symbol. */
static int read_symbol(const uint8_t *query, size_t size, uint8_t *reply,
                       size_t capacity, size_t *written) {
    Query request;
    Reply response;
    if (!uwrosv2_abb_ros1_abb_robot_msgs_GetRAPIDNumRequest_decode(query, size, &request)) return 0;
    if (equals(request.path.task, "T_ROB1") && equals(request.path.module, "Survey")
        && equals(request.path.symbol, "sample")) {
        response.value = 12.5f;
        response.result_code = uwrosv2_abb_ros1_abb_robot_msgs_ServiceResponses_RC_SUCCESS;
        response.message = text("");
    } else {
        response.value = 0;
        response.result_code = uwrosv2_abb_ros1_abb_robot_msgs_ServiceResponses_RC_FAILED;
        response.message = text("Unknown symbol");
    }
    return uwrosv2_abb_ros1_abb_robot_msgs_GetRAPIDNumResponse_encode(&response, reply, capacity, written);
}

static int service_exchange(void) {
    uint8_t query[64], reply[64];
    size_t query_size, reply_size;
    Query request = {{text("T_ROB1"), text("Survey"), text("sample")}};
    Reply response;
    if (!uwrosv2_abb_ros1_abb_robot_msgs_GetRAPIDNumRequest_encode(&request, query, sizeof query, &query_size)
        || !read_symbol(query, query_size, reply, sizeof reply, &reply_size)
        || !uwrosv2_abb_ros1_abb_robot_msgs_GetRAPIDNumResponse_decode(reply, reply_size, &response)) return 0;
    return response.result_code == uwrosv2_abb_ros1_abb_robot_msgs_ServiceResponses_RC_SUCCESS
        && response.value == 12.5f && response.message.size == 0;
}

static int inspect_system(void) {
    Task tasks[] = {{text("T_ROB1"), 1, uwrosv2_abb_ros1_abb_robot_msgs_RAPIDTaskState_EXECUTION_STATE_STARTED, 1}};
    Unit units[] = {{text("ROB_1"), 1}};
    SystemState state = {0}, received;
    uint8_t payload[128];
    size_t size;
    Task task;
    Unit unit;
    uwrosv2_abb_ros1_abb_robot_msgs_RAPIDTaskState_iterator task_it;
    uwrosv2_abb_ros1_abb_robot_msgs_MechanicalUnitState_iterator unit_it;
    state.header.seq = 7;
    state.header.stamp.sec = 42;
    state.header.frame_id = text("base");
    state.motors_on = 1;
    state.rapid_running = 1;
    state.rapid_tasks = uwrosv2_abb_ros1_abb_robot_msgs_RAPIDTaskState_array_values(tasks, 1);
    state.mechanical_units = uwrosv2_abb_ros1_abb_robot_msgs_MechanicalUnitState_array_values(units, 1);
    if (!uwrosv2_abb_ros1_abb_robot_msgs_SystemState_encode(&state, payload, sizeof payload, &size)
        || !uwrosv2_abb_ros1_abb_robot_msgs_SystemState_decode(payload, size, &received)) return 0;
    task_it = uwrosv2_abb_ros1_abb_robot_msgs_RAPIDTaskState_array_iter(&received.rapid_tasks);
    unit_it = uwrosv2_abb_ros1_abb_robot_msgs_MechanicalUnitState_array_iter(&received.mechanical_units);
    return equals(received.header.frame_id, "base") && received.header.stamp.sec == 42
        && uwrosv2_abb_ros1_abb_robot_msgs_RAPIDTaskState_array_next(&task_it, &task)
        && equals(task.name, "T_ROB1") && task.motion_task
        && uwrosv2_abb_ros1_abb_robot_msgs_MechanicalUnitState_array_next(&unit_it, &unit)
        && equals(unit.name, "ROB_1") && unit.activated;
}

void _start(void) {
    if (!service_exchange() || !inspect_system()) __builtin_trap();
}
