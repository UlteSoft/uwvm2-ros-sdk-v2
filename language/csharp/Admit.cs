// Inspect ECMA-335 metadata without loading or executing the user's assembly.
using System;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;

static class Admit
{
    // Each instruction operates on method arguments, local values or the
    // evaluation stack. The backend also checks the emitted IR for references
    // to native calls, globals and Mono's hidden context.
    static readonly HashSet<string> Numeric = new HashSet<string>(new[] {
        "nop", "ret", "dup", "pop", "add", "sub", "mul", "neg", "and", "or", "xor", "not",
        "shl", "shr", "shr.un", "ceq", "clt", "clt.un", "cgt", "cgt.un",
        "conv.i", "conv.u", "conv.i1", "conv.i2", "conv.i4", "conv.i8",
        "conv.u1", "conv.u2", "conv.u4", "conv.u8", "switch", "ldc.i8"
    });

    static readonly string[] LocalForms = {"ldarg", "starg", "ldloc", "ldloca", "stloc", "ldc.i4"};

    static int SwitchBytes(ReadOnlySpan<byte> operand)
    {
        int count = BinaryPrimitives.ReadInt32LittleEndian(operand);
        if (count < 0 || count > (operand.Length - 4) / 4) throw new Exception("invalid IL switch table");
        return 4 + 4 * count;
    }

    static void CheckCode(byte[] il)
    {
        var codes = new Dictionary<ushort, OpCode>();
        foreach (var field in typeof(OpCodes).GetFields(BindingFlags.Public | BindingFlags.Static))
            if (field.GetValue(null) is OpCode opcode) codes.Add(unchecked((ushort)opcode.Value), opcode);
        for (int pos = 0; pos < il.Length;) {
            int key = il[pos++];
            if (key == 0xfe && pos < il.Length) key = 0xfe00 | il[pos++];
            if (!codes.TryGetValue((ushort)key, out var code)) throw new Exception("invalid IL opcode");
            string name = code.Name;
            bool branch = code.FlowControl == FlowControl.Branch || code.FlowControl == FlowControl.Cond_Branch;
            bool local = false;
            foreach (var family in LocalForms)
                local |= name == family || name.StartsWith(family + ".", StringComparison.Ordinal);
            if (!Numeric.Contains(name) && !local && !(branch && name != "leave" && name != "leave.s" && name != "jmp"))
                throw new Exception("unsupported numeric IL operation: " + name);
            int bytes = code.OperandType switch {
                OperandType.InlineNone => 0,
                OperandType.ShortInlineBrTarget or OperandType.ShortInlineI or OperandType.ShortInlineVar => 1,
                OperandType.InlineVar => 2,
                OperandType.InlineBrTarget or OperandType.InlineI => 4,
                OperandType.InlineI8 => 8,
                OperandType.InlineSwitch => SwitchBytes(il.AsSpan(pos)),
                _ => throw new Exception("unsupported numeric IL operand")
            };
            if (bytes < 0 || bytes > il.Length - pos) throw new Exception("truncated numeric IL operand");
            pos += bytes;
        }
    }

    static int Main(string[] args)
    {
        try {
            using var file = File.OpenRead(args[0]);
            using var image = new PEReader(file);
            var data = image.GetMetadataReader();
            int selected = -1;
            foreach (var th in data.TypeDefinitions) {
                var type = data.GetTypeDefinition(th);
                foreach (var mh in type.GetMethods()) {
                    var method = data.GetMethodDefinition(mh);
                    string name = data.GetString(method.Name);
                    // Extracting a single member bypasses managed initialization.
                    if (name == ".cctor") throw new Exception("static or module initializer needs the CLR");
                    if (name != args[2] || data.GetString(type.Name) != args[1] || !type.Namespace.IsNil ||
                        !type.GetDeclaringType().IsNil) continue;
                    if ((type.Attributes & (TypeAttributes.Abstract | TypeAttributes.Sealed)) !=
                        (TypeAttributes.Abstract | TypeAttributes.Sealed) || type.GetGenericParameters().Count != 0)
                        throw new Exception("expected a non-generic static class");
                    var signature = data.GetBlobReader(method.Signature);
                    // DEFAULT managed calling convention, one parameter, I4 result and I4 parameter.
                    if (selected >= 0 || (method.Attributes & (MethodAttributes.Static | MethodAttributes.MemberAccessMask)) !=
                        (MethodAttributes.Static | MethodAttributes.Public) || method.RelativeVirtualAddress == 0 ||
                        signature.Length != 4 || signature.ReadByte() != 0 || signature.ReadByte() != 1 ||
                        signature.ReadByte() != 8 || signature.ReadByte() != 8)
                        throw new Exception("expected a single public static int method taking one int");
                    const MethodImplAttributes hints = MethodImplAttributes.NoInlining | MethodImplAttributes.NoOptimization |
                        MethodImplAttributes.AggressiveInlining | MethodImplAttributes.AggressiveOptimization;
                    if ((method.ImplAttributes & ~hints) != 0)
                        throw new Exception("managed method flags need the CLR");
                    var body = image.GetMethodBody(method.RelativeVirtualAddress);
                    if (!body.ExceptionRegions.IsEmpty) throw new Exception("managed handlers need the CLR");
                    CheckCode(body.GetILBytes());
                    selected = MetadataTokens.GetRowNumber(mh) - 1;
                }
            }
            if (selected < 0) throw new Exception("entry method was not found");
            using var symbols = File.OpenRead(args[3]);
            using var provider = MetadataReaderProvider.FromPortablePdbStream(symbols);
            var pdb = provider.GetMetadataReader();
            var info = pdb.GetMethodDebugInformation(MetadataTokens.MethodDebugInformationHandle(selected + 1));
            string digest = "";
            int firstLine = 0, visible = 0;
            foreach (var point in info.GetSequencePoints()) {
                if (point.IsHidden) continue;
                ++visible;
                if (visible != 1) continue;
                var document = pdb.GetDocument(point.Document.IsNil ? info.Document : point.Document);
                if (pdb.GetGuid(document.HashAlgorithm) != new Guid("8829d00f-11b8-4213-878b-770e8597ac16")) continue;
                digest = Convert.ToHexString(pdb.GetBlobBytes(document.Hash)).ToLowerInvariant();
                firstLine = point.StartLine;
            }
            Console.WriteLine($"{selected} {digest} {firstLine} {visible}");
            return 0;
        } catch (Exception error) {
            Console.Error.WriteLine(error.Message);
            return 1;
        }
    }
}
