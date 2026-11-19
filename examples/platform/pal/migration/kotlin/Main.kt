/** @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates. */
@file:JvmName("Main")
package example
private fun cell(width: Int, x: Int, y: Int) = y*width+x
fun main(args: Array<String>) { check(cell(400,7,3)==1207 && cell(17,16,0)==16 && cell(9,0,5)==45) }
