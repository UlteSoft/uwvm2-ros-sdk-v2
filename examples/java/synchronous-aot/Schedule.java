package example;

import wros.scene.Calls;

/** The private clock reference is supplied only in the declared clock-capability slot. */
final class Schedule {
    static void check(boolean value) { if(!value) throw new AssertionError(); }
    static byte[] words(long... values) {
        byte[] record=new byte[8*values.length];
        for(int i=0;i<values.length;i++) for(int j=0;j<8;j++)
            record[8*i+j]=(byte)(values[i] >>> (8*j));
        return record;
    }
    static long word(byte[] record,int i) {
        long value=0;
        for(int j=0;j<8;j++) value|=((long)record[8*i+j]&255L)<<(8*j);
        return value;
    }
    public static void main(String[] args) {
        Calls clock=new Calls(64,64), timer=new Calls(64,64), other=new Calls(64,64);
        byte[] result=new byte[32], empty=new byte[0]; long[] written={99};
        check(clock.capabilityOpen(new byte[]{'t','i','m','e'})==0);
        check(timer.capabilityOpen(new byte[]{'t','i','m','e','r'})==0);
        check(other.capabilityOpen(new byte[]{'o','t','h','e','r'})==0);
        check(clock.clockCreate(words(2),result,written)==0);
        long id=word(result,0);
        byte[] update=words(0,id,100,1);
        check(clock.clockUpdate(update,empty,written,new Calls[]{clock})==0 && word(update,0)==0);
        check(clock.clockRead(words(id),result,written)==0 && word(result,0)==100);
        byte[] record=words(0,id);
        check(timer.timerCreate(record,result,written,new Calls[]{other})==13);
        check(timer.timerCreate(record,result,written,new Calls[0])==22);
        check(timer.timerCreate(words(1,id),result,written,new Calls[]{clock})==22);
        check(timer.timerCreate(record,result,written,new Calls[]{clock})==0 && word(record,0)==0);
        long alarm=word(result,0);
        check(timer.timerReset(words(alarm,105,10),empty,written)==0);
        check(timer.timerTake(words(alarm),result,written)==11);
        check(clock.clockUpdate(words(0,id,125,1),empty,written,new Calls[]{clock})==0);
        check(timer.timerTake(words(alarm),result,written)==0 && word(result,0)==105 &&
              word(result,1)==125 && word(result,2)==3);
        check(timer.timerCancel(words(alarm),empty,written)==0);
        check(timer.timerTake(words(alarm),result,written)==11);
        check(timer.resourceClose(words(alarm),empty,written)==0);
        check(clock.resourceClose(words(id),empty,written)==0);
        check(clock.capabilityClose()==0);
        check(timer.timerCreate(record,result,written,new Calls[]{clock})==9);
        check(timer.capabilityClose()==0 && other.capabilityClose()==0);
    }
}
