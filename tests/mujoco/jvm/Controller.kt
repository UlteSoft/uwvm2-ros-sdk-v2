@file:JvmName("Controller")
package simulation

import wros.scene.Driver

private fun requireThat(value: Boolean) {
    if (!value) throw AssertionError()
}

private fun put(target: ByteArray, offset: Int, value: Long) {
    var i = 0
    while (i < 8) { target[offset+i]=(value ushr (8*i)).toByte(); i++ }
}

private fun get(source: ByteArray): Long {
    var result = 0L
    var i = 0
    while (i < 8) { result = result or ((source[i].toLong() and 255L) shl (8*i)); i++ }
    return result
}

fun main(args: Array<String>) {
    val driver = Driver()
    val body = payload()
    val reply = ByteArray(256)
    val result = LongArray(2)
    val state = LongArray(4)
    requireThat(driver.connect() == 9)
    requireThat(driver.open(byteArrayOf(106,111,105,110,116),4096,256) == 0)
    var status=11
    var tries=0
    while (status==11 && tries++<10000000) status=driver.connect()
    requireThat(status==0)
    requireThat(driver.submit(0,DEADLINE,body)==22)
    var sequence=1L
    while (sequence<=STEPS) {
        put(body,8,sequence)
        if (SUCCESS) body[TARGET+7]=(if ((sequence and 1L)==1L) 63 else 191).toByte()
        status=11; tries=0
        while (status==11 && tries++<10000000) status=driver.submit(sequence,DEADLINE,body)
        requireThat(status==0)
        requireThat(driver.result(sequence,ByteArray(0),result)==22)
        status=11; tries=0
        while (status==11 && tries++<10000000) status=driver.result(sequence,reply,result)
        if (CRASH) {
            requireThat((status==5 || status==13) && driver.describe(state)==0)
            requireThat(state[0]==6L && state[3]==1L)
        } else {
            requireThat(status==0 && result[0]==(if (SUCCESS) 0L else 13L))
            requireThat(result[1]>=8 && get(reply)==sequence)
        }
        sequence++
    }
    requireThat(driver.disconnect()==0)
}
