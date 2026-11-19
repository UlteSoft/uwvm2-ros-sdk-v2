// @brief Fixed-width scalar controller with no guest memory or host imports.
package robot

// @brief Compute a fixed-point gain with 32-bit unsigned wraparound.
// @param sample Raw reading. @param scale Multiplier. @param bias Offset.
// @return The scaled reading in the same representation.
func Gain(sample, scale, bias uint32) uint32 { return sample*scale + bias }

// @brief Validate a reference value during xmake run.
// @return Zero when the sample and calibration agree.
func Start() uint32 { return Gain(7, 5, 4) - 39 }
