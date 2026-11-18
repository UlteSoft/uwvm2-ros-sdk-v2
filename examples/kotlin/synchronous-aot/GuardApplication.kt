@file:JvmName("GuardApplication")
package example
import wros.scene.Guard

fun main(args: Array<String>) {
    check(args.isEmpty())
    val g = Guard()
    val policy = 2
    val code = g.open(byteArrayOf(115,105,103,110,97,108))
    if (policy == 0) { check(code == 13); return }
    check(code == 0 && g.create() == 0)
    System.gc()
    val status = g.trigger()
    if (policy == 1) { check(status == 13 && g.close() == 0); return }
    val count = longArrayOf(-1)
    check(status == 0 && g.take(count) == 0 && count[0] == 1L && g.close() == 0)
}
