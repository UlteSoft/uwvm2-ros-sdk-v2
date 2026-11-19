// Validate the Roslyn entry IL before lowering the two managed calls.
// The referenced assembly is built separately from user input in this invocation.
using System;
using System.Buffers.Binary;
using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;

static class SceneEntry
{
    static void Require(bool condition)
    {
        if (!condition) throw new Exception("scene entry must return its local integer policy applied to the selected Wros.Scene operation");
    }

    static EntityHandle Call(byte[] il, int offset)
    {
        Require(il[offset] == 0x28);
        return MetadataTokens.EntityHandle(BinaryPrimitives.ReadInt32LittleEndian(il.AsSpan(offset + 1, 4)));
    }

    public static MethodDefinitionHandle Policy(PEReader image, MetadataReader data, string owner, string entry, bool driver, out string alias)
    {
        MethodDefinitionHandle selected = default;
        alias = "";
        foreach (var th in data.TypeDefinitions) {
            var type = data.GetTypeDefinition(th);
            if (!type.Namespace.IsNil || !type.GetDeclaringType().IsNil || data.GetString(type.Name) != owner) continue;
            foreach (var mh in type.GetMethods()) {
                var method = data.GetMethodDefinition(mh);
                if (data.GetString(method.Name) != entry) continue;
                Require(selected.IsNil && method.RelativeVirtualAddress != 0 && method.GetGenericParameters().Count == 0);
                Require((method.Attributes & (MethodAttributes.Static | MethodAttributes.MemberAccessMask)) ==
                        (MethodAttributes.Static | MethodAttributes.Public));
                Require(method.ImplAttributes == MethodImplAttributes.IL);
                Require(data.GetBlobBytes(method.Signature).AsSpan().SequenceEqual(new byte[]{0,0,8}));
                var body = image.GetMethodBody(method.RelativeVirtualAddress);
                byte[] il = body.GetILBytes();
                int offset = driver ? 5 : 0;
                Require(body.ExceptionRegions.IsEmpty && body.LocalSignature.IsNil && il.Length == offset + 11 && il[offset + 10] == 0x2a);
                if (driver) {
                    Require(il[0] == 0x72);
                    int token = BinaryPrimitives.ReadInt32LittleEndian(il.AsSpan(1, 4));
                    Require((token >> 24) == 0x70);
                    alias = data.GetUserString(MetadataTokens.UserStringHandle(token & 0x00ffffff));
                    Require(alias != "." && alias != ".." && System.Text.RegularExpressions.Regex.IsMatch(alias, @"\A[A-Za-z0-9_.-]{1,255}\z"));
                }
                var call = Call(il, offset);
                Require(call.Kind == HandleKind.MemberReference);
                var member = data.GetMemberReference((MemberReferenceHandle)call);
                Require(data.GetString(member.Name) == (driver ? "DriverConnectionStatus" : "Abi") && member.Parent.Kind == HandleKind.TypeReference &&
                        data.GetBlobBytes(member.Signature).AsSpan().SequenceEqual(driver ? new byte[]{0,1,8,14} : new byte[]{0,0,8}));
                var target = data.GetTypeReference((TypeReferenceHandle)member.Parent);
                Require(data.GetString(target.Name) == "Scene" && data.GetString(target.Namespace) == "Wros" &&
                        target.ResolutionScope.Kind == HandleKind.AssemblyReference);
                var reference = data.GetAssemblyReference((AssemblyReferenceHandle)target.ResolutionScope);
                Require(data.GetString(reference.Name) == "Wros.Scene.Bindings" && reference.PublicKeyOrToken.IsNil &&
                        reference.Culture.IsNil && reference.Version == new Version(0,0,0,0));
                var policy = Call(il, offset + 5);
                Require(policy.Kind == HandleKind.MethodDefinition);
                selected = (MethodDefinitionHandle)policy;
                Require(data.GetMethodDefinition(selected).GetDeclaringType() == th);
            }
        }
        Require(!selected.IsNil);
        return selected;
    }
}
