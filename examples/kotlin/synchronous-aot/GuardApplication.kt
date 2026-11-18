@file:JvmName("GuardApplication")
package example

import wros.scene.Guard

fun main(args: Array<String>) {
    check(args.isEmpty())
    val guard = Guard()
    val alias = byteArrayOf(115, 105, 103, 110, 97, 108) // UTF-8 "signal"
    check(guard.open(null) == 22 && guard.create() == 9)
    check(guard.open(alias) == 0 && guard.create() == 0)
    check(guard.open(alias) == 16 && guard.create() == 16)
    val count = longArrayOf(-1)
    check(guard.trigger() == 0 && guard.take(count) == 0 && count[0] == 1L)
    check(guard.close() == 0)
}
