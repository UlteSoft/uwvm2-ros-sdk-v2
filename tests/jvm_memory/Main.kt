@file:JvmName("Main")
package example
import wros.scene.Scene

private class Node(val value: Int, val next: Node?) {
    val data = IntArray((value and 3) + 1)
    init { data[data.size - 1] = value }
}
private var retained: Node? = null

fun main(args: Array<String>) {
    check(args.isEmpty() && Scene.abi() == 2)
    var head: Node? = null
    for (i in 0 until 240) head = Node(i, head)
    System.gc()
    check(head != null && head.data.size == 4)
    retained = head
    head = null
    System.gc()
    var node = retained
    var sum = 0
    while (node != null) {
        sum += node.data[node.data.size - 1]
        node = node.next
    }
    retained = null
    check(sum == 28680)
}
