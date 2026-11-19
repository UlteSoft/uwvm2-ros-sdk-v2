/** @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates. */
function cell(width: number, x: number, y: number) { return (Math.imul(y,width)+x) >>> 0; }
if (cell(400,7,3)!==1207 || cell(17,16,0)!==16 || cell(9,0,5)!==45) throw Error("cell index");
