package simulation;

import wros.scene.Driver;

/** Drive the fixture through the deployment-provisioned humanoid joint alias. */
final class Controller {
    private static void require(boolean condition) {
        if (!condition) throw new AssertionError();
    }
    private static void put(byte[] target, int offset, long value) {
        for (int i=0; i<8; ++i) target[offset+i] = (byte) (value >>> (8*i));
    }
    private static long get(byte[] source) {
        long value=0;
        for (int i=0; i<8; i++) value |= ((long) source[i] & 255L) << (8*i);
        return value;
    }
    public static void main(String[] args) {
        Driver driver = new Driver();
        byte[] body = Settings.payload(), reply = new byte[256];
        long[] result = new long[2], state = new long[4];
        require(driver.connect() == 9);
        require(driver.open(new byte[]{106,111,105,110,116},4096,256) == 0);
        int status = 11, tries = 0;
        while (status == 11 && tries++ < 10000000) status = driver.connect();
        require(status == 0);
        require(driver.submit(0,Settings.DEADLINE,body) == 22);
        for (long sequence=1; sequence<=Settings.STEPS; sequence++) {
            put(body,8,sequence);
            if (Settings.SUCCESS) body[Settings.TARGET+7] = (byte)((sequence & 1) == 1 ? 63 : 191);
            status=11; tries=0;
            while (status==11 && tries++<10000000) status=driver.submit(sequence,Settings.DEADLINE,body);
            require(status == 0);
            require(driver.result(sequence,new byte[0],result) == 22);
            status=11; tries=0;
            while (status==11 && tries++<10000000) status=driver.result(sequence,reply,result);
            if (Settings.CRASH) {
                require((status==5 || status==13) && driver.describe(state)==0);
                require(state[0]==6 && state[3]==1);
            } else {
                require(status==0 && result[0]==(Settings.SUCCESS ? 0 : 13));
                require(result[1]>=8 && get(reply)==sequence);
            }
        }
        require(driver.disconnect()==0);
    }
}
