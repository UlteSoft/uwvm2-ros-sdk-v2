@file:JvmName("Main")
package example
import wros.scene.Scene
fun main(args: Array<String>) {
    check(args.isEmpty() && Scene.abi() == 2)
}
