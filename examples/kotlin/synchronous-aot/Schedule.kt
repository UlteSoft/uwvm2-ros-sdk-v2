@file:JvmName("Schedule")
package example
import wros.scene.Calls

private fun checkOk(value:Boolean) { if(!value) throw AssertionError() }
private fun words(vararg values:Long):ByteArray {
    val record=ByteArray(8*values.size)
    for (i in values.indices) for(j in 0..7) record[8*i+j]=(values[i] ushr (8*j)).toByte()
    return record
}
private fun word(record:ByteArray,i:Int):Long {
    var value=0L
    for (j in 0..7) value=value or ((record[8*i+j].toLong() and 255L) shl (8*j))
    return value
}
fun main(args:Array<String>) {
    val clock=Calls(64,64); val timer=Calls(64,64); val other=Calls(64,64)
    val result=ByteArray(32); val empty=ByteArray(0); val written=longArrayOf(99)
    checkOk(clock.capabilityOpen(byteArrayOf(116,105,109,101))==0)
    checkOk(timer.capabilityOpen(byteArrayOf(116,105,109,101,114))==0)
    checkOk(other.capabilityOpen(byteArrayOf(111,116,104,101,114))==0)
    checkOk(clock.clockCreate(words(2),result,written)==0)
    val id=word(result,0)
    val update=words(0,id,100,1)
    checkOk(clock.clockUpdate(update,empty,written,arrayOf(clock))==0 && word(update,0)==0L)
    checkOk(clock.clockRead(words(id),result,written)==0 && word(result,0)==100L)
    val record=words(0,id)
    checkOk(timer.timerCreate(record,result,written,arrayOf(other))==13)
    checkOk(timer.timerCreate(record,result,written,emptyArray<Calls>())==22)
    checkOk(timer.timerCreate(words(1,id),result,written,arrayOf(clock))==22)
    checkOk(timer.timerCreate(record,result,written,arrayOf(clock))==0 && word(record,0)==0L)
    val alarm=word(result,0)
    checkOk(timer.timerReset(words(alarm,105,10),empty,written)==0)
    checkOk(timer.timerTake(words(alarm),result,written)==11)
    checkOk(clock.clockUpdate(words(0,id,125,1),empty,written,arrayOf(clock))==0)
    checkOk(timer.timerTake(words(alarm),result,written)==0 && word(result,0)==105L &&
            word(result,1)==125L && word(result,2)==3L)
    checkOk(timer.timerCancel(words(alarm),empty,written)==0)
    checkOk(timer.timerTake(words(alarm),result,written)==11)
    checkOk(timer.resourceClose(words(alarm),empty,written)==0)
    checkOk(clock.resourceClose(words(id),empty,written)==0)
    checkOk(clock.capabilityClose()==0)
    checkOk(timer.timerCreate(record,result,written,arrayOf(clock))==9)
    checkOk(timer.capabilityClose()==0 && other.capabilityClose()==0)
}
