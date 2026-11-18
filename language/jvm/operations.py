"""Generate exactly the JVM source methods selected from the trusted ROS operation catalogue."""
import json
import re

GENERAL = (("i64", "i32", "i64", "i64", "i64", "i64", "i64"), ("i32",))
SPECIAL = {"abi": ((), ("i32",)),
           "capability.open": (("i32","i64","i64","i64"), ("i32",)),
           "capability.close": (("i64",), ("i32",))}


def method(name):
    first, *tail = re.split(r"[._]", name)
    return first + "".join(s[0].upper()+s[1:] for s in tail)


def render(catalog, requested, work):
    if not requested:
        return [], []
    if len(set(requested)) != len(requested):
        raise ValueError("duplicate ROS operation")
    rows={r["name"]:r for r in json.loads(catalog.read_text())["operations"]}
    methods=["wros/scene/Calls.<init>(II)V"]
    code = ['package wros.scene;', 'import org.teavm.interop.Import;',
            'public final class Calls {', 'private final MessageFrame frame;',
            'public Calls(int inputLimit,int outputLimit){frame=new MessageFrame(inputLimit,outputLimit);}']
    for name in sorted(requested):
        if name not in rows or not re.fullmatch(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*",name):
            raise ValueError("unknown ROS operation: " + name)
        row=rows[name]["wasm_signature"]
        actual=(tuple(row["parameters"]),tuple(row["results"]))
        if actual != SPECIAL.get(name, GENERAL):
            raise ValueError("unsupported ROS signature: "+name)
        symbol="wr_"+name.replace(".","_")
        member=method(name)
        if name=="abi":
            block = '''@Import(name="wr_abi") private static native int rawAbi();
                public static int abi(){return rawAbi();}'''
            descriptor="()I"
        elif name=="capability.open":
            block = '''@Import(name="wr_capability_open") private static native int rawOpen(int m,long input,long len,long out);
                public int capabilityOpen(byte[] alias) {
                    if (frame.token != 0) return 16;
                    if (alias == null || alias.length == 0) return 22;
                    if (alias.length > frame.input.length) return 90;
                    long input=frame.prepare(alias);
                    return frame.finishOpen(rawOpen(0,input,alias.length,MessageFrame.address(frame.count)),alias.length);
                }'''
            descriptor="([B)I"
        elif name=="capability.close":
            block = '''@Import(name="wr_capability_close") private static native int rawClose(long token);
                public int capabilityClose() {
                    if (frame.token == 0) return 9;
                    int status=rawClose(frame.token);
                    if (status==0) frame.token=0;
                    return status;
                }'''
            descriptor="()I"
        else:
            permission_report = str(name in ("permission.report", "module.permission.report")).lower()
            block=f'''@Import(name="{symbol}") private static native int raw_{member}(long t,int m,long i,long n,long o,long cap,long w);
                public int {member}(byte[] request,byte[] reply,long[] written) {{
                    if (request==null || reply==null || written==null || written.length!=1) return 22;
                    if (request.length>frame.input.length || reply.length>frame.output.length) return 90;
                    long input=frame.prepare(request);
                    long output=reply.length==0 ? 0 : MessageFrame.address(frame.output);
                    int status=raw_{member}(frame.token,0,input,request.length,output,reply.length,frame.lengthSlot());
                    return frame.finish(status,request.length,reply,written,{permission_report});
                }}'''
            descriptor="([B[B[J)I"
        methods.append("wros/scene/Calls."+member+descriptor)
        code.append(block)
    if len(methods)!=len(set(methods)):
        raise ValueError("colliding Java ROS operation names")
    code.append("}")
    source=work/"Calls.java";source.write_text("\n".join(code)+"\n")
    return [source],methods
