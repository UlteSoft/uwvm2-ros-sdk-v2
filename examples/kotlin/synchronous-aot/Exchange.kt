@file:JvmName("Exchange")
package example
import wros.scene.Calls

private fun requireOk(ok: Boolean) { if (!ok) throw AssertionError() }
fun main(args: Array<String>) {
    val signal=Calls(8,8)
    val limited=Calls(8,8)
    val empty=ByteArray(0)
    val handle=ByteArray(8)
    val count=ByteArray(8)
    val written=longArrayOf(-1)
    val alias=byteArrayOf(115,105,103,110,97,108)
    requireOk(signal.capabilityOpen(alias)==0 && alias[0].toInt()==115)
    requireOk(limited.capabilityOpen(byteArrayOf(108,105,109,105,116,101,100)) == 0)
    requireOk(signal.guardCreate(empty,handle,written) == 0 && written[0] == 8L)
    count[0]=85
    requireOk(limited.guardTrigger(handle,count,written)==13 && count[0].toInt()==85)
    requireOk(signal.guardTrigger(handle,empty,LongArray(0)) == 22)
    requireOk(signal.guardTrigger(handle,empty,written) == 0)
    requireOk(signal.guardTake(handle,ByteArray(9),written) == 90)
    requireOk(signal.guardTake(handle,count,written) == 0 && written[0] == 8L && count[0].toInt() == 1)
    requireOk(signal.capabilityClose() == 0 && signal.capabilityClose() == 9)
    requireOk(limited.capabilityClose() == 0)
}
