/** @file wros.ts
 * @brief Bounded driver staging for the wasm32 AssemblyScript profile.
 */

/** @brief Set one byte in the 512-byte private request. */
@external("wros_as_driver", "writeByte")
export declare function writeByte(offset: u32, value: u32): void;

/** @brief Store one little-endian word in the private request. */
@external("wros_as_driver", "writeWord")
export declare function writeWord(offset: u32, value: u64): void;

/** @brief Control automatic erasure of this guest's consumed request bytes. Defaults to true. */
@external("wros_as_driver", "setRequestWipe")
export declare function setRequestWipe(enabled: bool): void;

/** @brief Zero the full private request. */
@external("wros_as_driver", "clearRequest")
export declare function clearRequest(): void;

/** @brief Open the alias bytes staged at the start of the request. */
@external("wros_as_driver", "open")
export declare function open(aliasSize: u32): u32;

/** @brief Return the handle from the last successful open, or zero. */
@external("wros_as_driver", "opened")
export declare function opened(): u64;

/** @brief Close an owned capability without granting any new operation. */
@external("wros_as_driver", "close")
export declare function close(capability: u64): u32;

/** @brief Connect the authorized external driver. */
@external("wros_as_driver", "connect")
export declare function connect(capability: u64): u32;

/** @brief Submit the staged request bytes, including the caller's sequence and deadline. */
@external("wros_as_driver", "submit")
export declare function submit(capability: u64, requestSize: u32): u32;

/** @brief Poll the result for a sequence using the default 512-byte reply capacity. */
@external("wros_as_driver", "result")
export declare function result(capability: u64, sequence: u64): u32;

/** @brief Poll the same sequence with an explicit reply capacity up to 4096 bytes. */
@external("wros_as_driver", "resultWithCapacity")
export declare function resultWithCapacity(capability: u64, sequence: u64, capacity: u32): u32;

/** @brief Read the driver's observed state without granting control authority. */
@external("wros_as_driver", "describe")
export declare function describe(capability: u64): u32;

/** @brief Disconnect the module's channel. */
@external("wros_as_driver", "disconnect")
export declare function disconnect(capability: u64): u32;

/** @brief Return the size of the successful reply or zero. */
@external("wros_as_driver", "replySize")
export declare function replySize(): u32;

/** @brief Return the last required length reported by a driver size error, or zero. */
@external("wros_as_driver", "replyRequired")
export declare function replyRequired(): u64;

/** @brief Load one little-endian word within the last successful reply. */
@external("wros_as_driver", "readWord")
export declare function readWord(offset: u32): u64;

/** @brief Zero the previous reply bytes, and reset length and required-size metadata. */
@external("wros_as_driver", "clearReply")
export declare function clearReply(): void;
