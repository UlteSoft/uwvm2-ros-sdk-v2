// @brief Read the parent ROSv2 ABI before using a separately provisioned platform.
package robot

// @brief Check the host ABI passed to this module's entry point.
// @param abi Result of the real authorized uwvm_ros_v2.abi query.
// @return Zero for ROSv2 ABI 2. All other values cause the guest to trap.
// @details This preflight checks the parent ABI only. Device identity, child
// enablement and driver authority require separate checks by the host.
func Start(abi uint32) uint32 { return abi - 2 }
