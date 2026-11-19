// @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates.
package main
func cell(width,x,y uint32) uint32 { return y*width+x }
func main() {
    if cell(400,7,3)!=1207 || cell(17,16,0)!=16 || cell(9,0,5)!=45 { panic("cell index") }
}
