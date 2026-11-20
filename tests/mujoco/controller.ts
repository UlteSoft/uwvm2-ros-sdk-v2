/** @file controller.ts
 * @brief Produce joint positions for the bound simulation fixture.
 */
export function jointTarget(sequence: u64, scenario: i32): f64 {
    if (sequence == 0) unreachable();
    if (scenario == 1) return 2.0;
    if (scenario == 2) return 0.5;
    if (scenario != 0) unreachable();
    return (sequence & 1) != 0 ? 0.5 : -0.5;
}

export function _start(): void {}
