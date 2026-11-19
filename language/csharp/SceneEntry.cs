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
        if (!condition) throw new Exception("scene entry must return its local integer policy applied to Wros.Scene.Abi()");
    }

    static EntityHandle Call(byte[] il, int offset)
    {
        Require(il[offset] == 0x28);
        return MetadataTokens.EntityHandle(BinaryPrimitives.ReadInt32LittleEndian(il.AsSpan(offset + 1, 4)));
    }

    public static MethodDefinitionHandle Policy(PEReader image, MetadataReader data, string owner, string entry)
    {
        MethodDefinitionHandle selected = default;
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
                Require(body.ExceptionRegions.IsEmpty && body.LocalSignature.IsNil && il.Length == 11 && il[10] == 0x2a);
                var call = Call(il, 0);
                Require(call.Kind == HandleKind.MemberReference);
                var member = data.GetMemberReference((MemberReferenceHandle)call);
                Require(data.GetString(member.Name) == "Abi" && member.Parent.Kind == HandleKind.TypeReference &&
                        data.GetBlobBytes(member.Signature).AsSpan().SequenceEqual(new byte[]{0,0,8}));
                var target = data.GetTypeReference((TypeReferenceHandle)member.Parent);
                Require(data.GetString(target.Name) == "Scene" && data.GetString(target.Namespace) == "Wros" &&
                        target.ResolutionScope.Kind == HandleKind.AssemblyReference);
                var reference = data.GetAssemblyReference((AssemblyReferenceHandle)target.ResolutionScope);
                Require(data.GetString(reference.Name) == "Wros.Scene.Bindings" && reference.PublicKeyOrToken.IsNil &&
                        reference.Culture.IsNil && reference.Version == new Version(0,0,0,0));
                var policy = Call(il, 5);
                Require(policy.Kind == HandleKind.MethodDefinition);
                selected = (MethodDefinitionHandle)policy;
                Require(data.GetMethodDefinition(selected).GetDeclaringType() == th);
            }
        }
        Require(!selected.IsNil);
        return selected;
    }
}
