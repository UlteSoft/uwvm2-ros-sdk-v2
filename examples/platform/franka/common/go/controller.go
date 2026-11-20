// @brief Fixed-width scalar controller with no guest memory or host imports.
package robot

// @brief Compute a fixed-point gain with 32-bit unsigned wraparound.
// @param sample Raw reading. @param scale Multiplier. @param bias Offset.
// @return The scaled reading in the same representation.
func Gain(sample, scale, bias uint32) uint32 { return sample*scale + bias }

// @brief Average accumulated readings, with zero representing an empty batch.
func Average(sum, samples uint32) uint32 {
	if samples == 0 {
		return 0
	}
	return sum / samples
}

// @brief Validate a reference value during xmake run.
// @return Zero when the sample and calibration agree.
func Start() uint32 { return Gain(7, 5, 4) - 39 + Average(45, 5) - 9 + Average(45, 0) }
