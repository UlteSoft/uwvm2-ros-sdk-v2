/** @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates. */
package example;
public final class Main {
    static int cell(int width,int x,int y) { return y*width+x; }
    public static void main(String[] args) {
        if (cell(400,7,3)!=1207 || cell(17,16,0)!=16 || cell(9,0,5)!=45) throw new AssertionError();
    }
}
