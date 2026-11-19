/** @brief Validate the median of an outlier window and a tied range reading. */
function median(a, b, c) {
    return [a, b, c].sort((left, right) => left - right)[1];
}
if (median(407, 399, 2000) !== 407 || median(300, 2000, 300) !== 300)
    throw Error("range filter mismatch");
