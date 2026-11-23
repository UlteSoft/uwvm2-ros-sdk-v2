//! Zig bindings for the registered ROSv2 scene operations.
//! Pass guest addresses through `address` and use the contract's byte lengths on both pointer widths.

/// Convert a guest pointer to the i64 carrier, including its WasmMTE tag.
pub inline fn address(pointer: anytype) u64 {
    return @intFromPtr(pointer);
}

/// Status codes returned by scene operations other than ABI discovery.
pub const Status = struct {
    pub const success: u32 = 0;
    pub const io: u32 = 5;
    pub const bad_handle: u32 = 9;
    pub const again: u32 = 11;
    pub const no_memory: u32 = 12;
    pub const denied: u32 = 13;
    pub const conflict: u32 = 17;
    pub const invalid: u32 = 22;
    pub const too_large: u32 = 90;
    pub const unsupported: u32 = 95;
    pub const timeout: u32 = 110;
    pub const cancelled: u32 = 125;
};

/// Registered operations in the `action` domain.
pub const action = @import("domains/action.zig");
/// Registered operations in the `artifact` domain.
pub const artifact = @import("domains/artifact.zig");
/// Registered operations in the `bridge` domain.
pub const bridge = @import("domains/bridge.zig");
/// Registered operations in the `buffer` domain.
pub const buffer = @import("domains/buffer.zig");
/// Registered operations in the `capability` domain.
pub const capability = @import("domains/capability.zig");
/// Registered operations in the `clock` domain.
pub const clock = @import("domains/clock.zig");
/// Registered operations in the `communication` domain.
pub const communication = @import("domains/communication.zig");
/// Registered operations in the `context` domain.
pub const context = @import("domains/context.zig");
/// Registered operations in the `control` domain.
pub const control = @import("domains/control.zig");
/// Registered operations in the `device` domain.
pub const device = @import("domains/device.zig");
/// Registered operations in the `diagnostic` domain.
pub const diagnostic = @import("domains/diagnostic.zig");
/// Registered operations in the `driver` domain.
pub const driver = @import("domains/driver.zig");
/// Registered operations in the `event` domain.
pub const event = @import("domains/event.zig");
/// Registered operations in the `graph` domain.
pub const graph = @import("domains/graph.zig");
/// Registered operations in the `guard` domain.
pub const guard = @import("domains/guard.zig");
/// Registered operations in the `lifecycle` domain.
pub const lifecycle = @import("domains/lifecycle.zig");
/// Registered operations in the `log` domain.
pub const log = @import("domains/log.zig");
/// Registered operations in the `media` domain.
pub const media = @import("domains/media.zig");
/// Registered operations in the `model` domain.
pub const model = @import("domains/model.zig");
/// Registered operations in the `module_call` domain.
pub const module_call = @import("domains/module_call.zig");
/// Registered operations in the `modules` domain.
pub const modules = @import("domains/modules.zig");
/// Registered operations in the `node` domain.
pub const node = @import("domains/node.zig");
/// Registered operations in the `parameter` domain.
pub const parameter = @import("domains/parameter.zig");
/// Registered operations in the `permission` domain.
pub const permission = @import("domains/permission.zig");
/// Registered operations in the `proposal` domain.
pub const proposal = @import("domains/proposal.zig");
/// Registered operations in the `qos` domain.
pub const qos = @import("domains/qos.zig");
/// Registered operations in the `recording` domain.
pub const recording = @import("domains/recording.zig");
/// Registered operations in the `replay` domain.
pub const replay = @import("domains/replay.zig");
/// Registered operations in the `request` domain.
pub const request = @import("domains/request.zig");
/// Registered operations in the `resource` domain.
pub const resource = @import("domains/resource.zig");
/// Registered operations in the `sensor` domain.
pub const sensor = @import("domains/sensor.zig");
/// Registered operations in the `service` domain.
pub const service = @import("domains/service.zig");
/// Registered operations in the `timer` domain.
pub const timer = @import("domains/timer.zig");
/// Registered operations in the `topic` domain.
pub const topic = @import("domains/topic.zig");
/// Registered operations in the `transform` domain.
pub const transform = @import("domains/transform.zig");
/// Registered operations in the `types` domain.
pub const types = @import("domains/types.zig");
/// Registered operations in the `vm` domain.
pub const vm = @import("domains/vm.zig");
/// Registered operations in the `wait` domain.
pub const wait = @import("domains/wait.zig");
