# @brief Query the installed ROS ABI and check a portable sensor calculation.
samples = [406, 940, 407, 402, 407]
raise "ABI version" unless WROS.abi == 2
raise "unexpected median" unless samples.sort[2] == 407
