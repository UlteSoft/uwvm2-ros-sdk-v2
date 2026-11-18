package example;

import wros.scene.Calls;

/** A canonical eight-byte guard resource request, bound independently of its compile-time import. */
final class Exchange {
    static void require(boolean ok) { if (!ok) throw new AssertionError(); }
    public static void main(String[] args) {
        Calls signal = new Calls(8,8);
        Calls limited = new Calls(8,8);
        byte[] empty = new byte[0], handle = new byte[8], count = new byte[8];
        long[] written = {-1};
        byte[] alias={'s','i','g','n','a','l'};
        require(signal.capabilityOpen(alias) == 0 && alias[0]=='s');
        require(limited.capabilityOpen(new byte[]{'l','i','m','i','t','e','d'}) == 0);
        require(signal.guardCreate(empty,handle,written) == 0 && written[0] == 8);
        count[0]=85;
        require(limited.guardTrigger(handle,count,written) == 13 && count[0]==85);
        require(signal.guardTrigger(handle,empty,new long[0]) == 22);
        require(signal.guardTrigger(handle,empty,written) == 0);
        require(signal.guardTake(handle,new byte[9],written) == 90);
        require(signal.guardTake(handle,count,written) == 0 && written[0] == 8 && count[0] == 1);
        require(signal.capabilityClose() == 0 && signal.capabilityClose() == 9);
        require(limited.capabilityClose() == 0);
    }
}
