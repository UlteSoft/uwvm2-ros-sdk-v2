/** @brief Return the median of three range readings in millimetres. */
function median(a: number, b: number, c: number): number {
    return [a, b, c].sort((left, right) => left - right)[1];
}
if (median(407, 399, 2000) !== 407 || median(300, 2000, 300) !== 300)
    throw new Error("range filter mismatch");
