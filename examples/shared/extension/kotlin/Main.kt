@file:JvmName("Main")
package example
import wros.scene.Calls
/** @brief Exercise the denied driver connection through the Kotlin capability binding. */
fun main(args: Array<String>) {
    val arm = Calls(8, 8)
    val reply = ByteArray(8)
    reply[0] = 42
    check(arm.capabilityOpen(byteArrayOf(97, 114, 109)) == 0)
    check(arm.driverConnect(ByteArray(0), reply, LongArray(1)) == 13 && reply[0].toInt() == 42)
    check(arm.capabilityClose() == 0)
}
