// @file Driver.fs
// @brief Check the selected platform driver permissions through one scoped connection.
module Driver

/// @brief Return zero only for a denied connection attempt.
let Check (status: int) = if status = 13 then 0 else 1

/// @brief Attempt one bounded connection against the literal arm alias.
let Start () = Check (Wros.Scene.DriverConnectionStatus("arm"))
