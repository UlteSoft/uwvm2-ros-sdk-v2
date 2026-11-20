/** @file controller.ts
 * @brief Fixed-point calculation and a read-only ROSv2 ABI check.
 */
@external("uwvm_ros_v2", "abi")
declare function rosAbi(): u32;

/** @brief Scale a sensor sample with signed wrapping arithmetic. */
export function gain(sample: i32, multiplier: i32, offset: i32): i32 {
  return sample * multiplier + offset;
}

/** @brief Check the selected host ABI and the arithmetic result. */
export function _start(): void {
  if (rosAbi() != 2 || gain(9, 4, -1) != 35) unreachable();
}
