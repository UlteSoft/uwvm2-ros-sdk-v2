/** @brief Check the ROSv2 ABI and the result of a local sensor sample reduction. */
const values = [1, 2, 3, 4];
if (wros.abi() !== 2 || values.reduce((sum, x) => sum+x*x, 0) !== 30) throw Error("unexpected sample or ABI");
