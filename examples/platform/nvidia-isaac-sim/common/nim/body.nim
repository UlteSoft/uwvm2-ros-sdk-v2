## @brief Check the ROSv2 ABI inside the guest and fail on mismatch.
import wros_scene

proc squaredSum(samples: openArray[int32]): int32 =
  for sample in samples:
    result += sample * sample

doAssert squaredSum([1'i32, 2, 3]) == 14
doAssert wr_abi() == 2
