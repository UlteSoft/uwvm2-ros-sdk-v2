@file:JvmName("Denied")
package simulation
import wros.scene.Driver

fun main(args: Array<String>) {
    val driver = Driver()
    if (driver.open(byteArrayOf(110,111,110,101),8,8)!=13) throw AssertionError()
    if (driver.open(byteArrayOf(114,101,97,100),8,8)!=0) throw AssertionError()
    if (driver.connect()!=13 || driver.close()!=0) throw AssertionError()
}
