#![no_std]
#[cfg(target_arch = "wasm32")]
use core::arch::wasm32::unreachable;
#[cfg(target_arch = "wasm64")]
use wros_runtime::abort as unreachable;
use core::panic::PanicInfo;
use wros_observation::ros1::{abb_robot_msgs::*, std_msgs::Header, Error, Message, Sequence, Time};

#[panic_handler]
fn panic(_: &PanicInfo) -> ! { unreachable() }

// A local service handler supplies a sample measurement for a known RAPID symbol.
fn read_symbol(query: &[u8], reply: &mut [u8]) -> Result<usize, Error> {
    let request = GetRAPIDNumRequest::decode(query)?;
    let known = request.path.task == b"T_ROB1" && request.path.module == b"Survey" && request.path.symbol == b"sample";
    let response = if known {
        GetRAPIDNumResponse { value: 12.5, result_code: ServiceResponses::RC_SUCCESS, message: b"" }
    } else {
        GetRAPIDNumResponse { value: 0.0, result_code: ServiceResponses::RC_FAILED, message: b"Unknown symbol" }
    };
    response.encode(reply)
}

fn service_exchange() -> Result<bool, Error> {
    let request = GetRAPIDNumRequest { path: RAPIDSymbolPath { task: b"T_ROB1", module: b"Survey", symbol: b"sample" } };
    let mut query = [0; 64];
    let mut reply = [0; 64];
    let query_size = request.encode(&mut query)?;
    let reply_size = read_symbol(&query[..query_size], &mut reply)?;
    let response = GetRAPIDNumResponse::decode(&reply[..reply_size])?;
    Ok(response.result_code == ServiceResponses::RC_SUCCESS && response.value == 12.5 && response.message.is_empty())
}

fn inspect_system() -> Result<bool, Error> {
    let tasks = [RAPIDTaskState {
        name: b"T_ROB1", activated: true, execution_state: RAPIDTaskState::EXECUTION_STATE_STARTED, motion_task: true,
    }];
    let units = [MechanicalUnitState { name: b"ROB_1", activated: true }];
    let state = SystemState {
        header: Header { seq: 7, stamp: Time { sec: 42, nsec: 0 }, frame_id: b"base" },
        motors_on: true, auto_mode: false, rapid_running: true,
        rapid_tasks: Sequence::from_values(&tasks), mechanical_units: Sequence::from_values(&units),
    };
    let mut payload = [0; 128];
    let size = state.encode(&mut payload)?;
    let got = SystemState::decode(&payload[..size])?;
    let task = got.rapid_tasks.iter().next();
    let unit = got.mechanical_units.iter().next();
    Ok(got.header.frame_id == b"base" && got.header.stamp.sec == 42
        && matches!(task, Some(t) if t.name == b"T_ROB1" && t.motion_task)
        && matches!(unit, Some(u) if u.name == b"ROB_1" && u.activated))
}

#[no_mangle]
pub extern "C" fn _start() {
    if service_exchange() != Ok(true) || inspect_system() != Ok(true) { unreachable() }
}
