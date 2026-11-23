/** @file main.ts
 * @brief Check the guest filter and its explicitly exposed ROSv2 ABI.
 */
import { wr_abi } from "uwrosv2/capability";
import {sumSquares} from "./filter";
const samples: ReadonlyArray<number> = [1, 2, 3, 4];
if (sumSquares(samples) !== 30 || wr_abi() !== 2) {
    throw new Error("unexpected filter result or ROSv2 ABI");
}
