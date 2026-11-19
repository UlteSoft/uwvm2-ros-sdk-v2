/** @file filter.ts
 * @brief Compute the sum of squares without modifying the sample array.
 * @param samples Finite input observations.
 * @returns Sum of the squared observations.
 */
export function sumSquares(samples: readonly number[]): number {
    return samples.reduce((sum, value) => sum + value * value, 0);
}
