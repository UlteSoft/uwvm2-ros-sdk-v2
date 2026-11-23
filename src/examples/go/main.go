package main

import "github.com/UlteSoft/uwvm2-ros-sdk-v2/u2rosv2"

func main() {
	if u2rosv2.ABI() != 2 {
		panic("uwvm_ros_v2 ABI query failed")
	}
}
