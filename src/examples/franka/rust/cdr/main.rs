#![no_std]

#[cfg(target_arch = "wasm32")]
use core::arch::wasm32::unreachable;
#[cfg(target_arch = "wasm64")]
use wros_runtime::abort as unreachable;
use core::{hint::black_box, panic::PanicInfo};
use wros_observation::cdr::{franka_msgs as arm, franka_spine_msgs as spine, service_msgs::ServiceEventInfo};
use wros_observation::cdr::{Endian, Error, Message, Sequence};

mod elbow_frames;
use elbow_frames::{ELBOW_BE, ELBOW_LE};

#[panic_handler]
fn panic(_: &PanicInfo) -> ! { unreachable() }

fn transcode_elbow(source: &[u8], expected: &[u8], order: Endian) -> Result<bool, Error> {
    let elbow = arm::Elbow::decode(black_box(source))?;
    let mut output = [0; 84];
    let written = elbow.encode(order, &mut output)?;
    Ok(elbow.position[0] == 1.125 && elbow.desired_position[0] == -0.75
        && elbow.commanded_position[0] == 0.25 && elbow.commanded_velocity[0] == 0.03125
        && elbow.commanded_acceleration[0] == 0.125 && &output[..written] == expected)
}

// Joint data from franka_hardware/test/ptp_motion_test.cpp in the pinned Franka release.
fn read_goal() -> Result<bool, Error> {
    let positions = [0.0, -1.0, 0.0, -2.0, 0.0, 1.5, 0.5];
    let velocities = [1.0; 7];
    let request = arm::PTPMotion_SendGoal_Request {
        goal_id: Default::default(),
        goal: arm::PTPMotion_Goal {
            goal_joint_configuration: Sequence::from_values(&positions),
            maximum_joint_velocities: Sequence::from_values(&velocities),
            goal_tolerance: 0.01,
        },
    };
    let mut bytes = [0; 192];
    let written = request.encode(Endian::Big, &mut bytes)?;
    let decoded = arm::PTPMotion_SendGoal_Request::decode(&bytes[..written])?;
    Ok(decoded.goal.goal_tolerance == 0.01
        && decoded.goal.goal_joint_configuration.iter().eq(positions.iter().copied())
        && decoded.goal.maximum_joint_velocities.iter().eq(velocities.iter().copied()))
}

// The upstream spine server's concurrent GetPosition sample reports 0.42 metres.
fn read_position_service() -> Result<bool, Error> {
    let mut bytes = [0; 128];
    let size = spine::GetPosition_Request::default().encode(Endian::Big, &mut bytes)?;
    if size != 5 || spine::GetPosition_Request::decode(&bytes[..size])?.structure_needs_at_least_one_member != 0 {
        return Ok(false);
    }
    let replies = [spine::GetPosition_Response { position: 0.42, success: true }];
    let event = spine::GetPosition_Event {
        info: ServiceEventInfo { event_type: ServiceEventInfo::RESPONSE_SENT, ..Default::default() },
        response: Sequence::from_values(&replies),
        ..Default::default()
    };
    let size = event.encode(Endian::Little, &mut bytes)?;
    let recorded = spine::GetPosition_Event::decode(&bytes[..size])?;
    Ok(recorded.request.is_empty() && recorded.response.len() == 1
        && matches!(recorded.response.iter().next(), Some(reply) if reply.success && reply.position == 0.42))
}

#[no_mangle]
pub extern "C" fn _start() {
    if transcode_elbow(ELBOW_BE, ELBOW_LE, Endian::Little) != Ok(true)
        || transcode_elbow(ELBOW_LE, ELBOW_BE, Endian::Big) != Ok(true)
        || read_goal() != Ok(true) || read_position_service() != Ok(true) { unreachable() }
}
