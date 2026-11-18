package wros.scene;

/** Walk the canonical wire shape on a private copy. Each element consumes at least a word. */
final class CapabilityCursor {
    final byte[] input;
    final int size;
    final Calls[] sources;
    int offset, next, status;

    CapabilityCursor(byte[] input, int size, Calls[] sources) {
        this.input=input;
        this.size=size;
        this.sources=sources;
    }
    void skip(int bytes) {
        if (status!=0) return;
        if (bytes<0 || bytes>size-offset) status=22;
        else offset+=bytes;
    }
    private long word() {
        int start=offset;
        skip(8);
        if (status!=0) return 0;
        long value=0;
        for(int i=0; i<8; ++i) value|=((long)input[start+i]&255L)<<(i*8);
        return value;
    }
    boolean present() {
        long flag=word();
        if (flag!=0 && flag!=1 && status==0) status=22;
        return flag==1;
    }
    int elements() {
        long count=word();
        if (count<0 || count>(size-offset)/8) {
            if (status==0) status=22;
            return 0;
        }
        return (int)count;
    }
    void blob() {
        long bytes=word();
        if (bytes<0 || bytes>size-offset) {
            if (status==0) status=22;
        } else skip((int)bytes);
    }
    void bind() {
        int field=offset;
        long place=word();
        if (status!=0) return;
        if (place!=0 || next>=sources.length) { status=22; return; }
        Calls source=sources[next++];
        long token=source==null ? 0 : source.handleForBinding();
        if (token==0) { status=9; return; }
        for (int i=0; i<8; ++i) input[field+i]=(byte)(token >>> (i*8));
    }
    int finish() {
        return status!=0 ? status : (offset==size && next==sources.length ? 0 : 22);
    }
}
