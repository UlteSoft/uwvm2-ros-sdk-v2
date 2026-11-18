import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import org.objectweb.asm.*;

/** Validate application bytecode before it joins the synchronous guest runtime. */
public final class Admit {
    private static final Set<String> CALLS = Set.of(
        "java/lang/Object.<init>()V", "java/lang/Object.getClass()Ljava/lang/Class;",
        "java/lang/AssertionError.<init>()V", "java/lang/IllegalStateException.<init>(Ljava/lang/String;)V",
        "java/lang/System.gc()V", "java/lang/System.nanoTime()J", "java/lang/System.currentTimeMillis()J",
        "kotlin/jvm/internal/Intrinsics.checkNotNullParameter(Ljava/lang/Object;Ljava/lang/String;)V",
        "wros/scene/Scene.abi()I", "wros/scene/Guard.<init>()V", "wros/scene/Guard.open([B)I",
        "wros/scene/Guard.create()I", "wros/scene/Guard.trigger()I",
        "wros/scene/Guard.take([J)I", "wros/scene/Guard.close()I"
    );
    private static final Set<String> BUILTINS = Set.of("java/lang/Object", "java/lang/String", "java/lang/Class",
        "java/lang/AssertionError", "java/lang/IllegalStateException", "wros/scene/Guard", "wros/scene/Scene");
    private static void refuse(String reason) { throw new IllegalArgumentException("unsupported synchronous JVM feature: " + reason); }
    private static void annotation(String type) { if (type.startsWith("Lorg/teavm/")) refuse(type); }
    public static void main(String[] args) throws Exception {
        Set<String> app = new HashSet<>();
        try (var stream = Files.walk(Path.of(args[0]))) {
            var paths = stream.filter(p -> p.toString().endsWith(".class")).limit(4097).toList();
            if (paths.isEmpty() || paths.size() > 4096) refuse("application class count");
            for (var p : paths) {
                String name = new ClassReader(Files.readAllBytes(p)).getClassName();
                if (name.startsWith("java/") || name.startsWith("javax/") || name.startsWith("jdk/") ||
                    name.startsWith("sun/") || name.startsWith("com/sun/") || name.startsWith("kotlin/") ||
                    name.startsWith("kotlinx/") || name.startsWith("org/teavm/") || name.startsWith("wros/") ||
                    !app.add(name) || Admit.class.getClassLoader().getResource(name + ".class") != null) refuse(name);
            }
            if (!app.contains(args[1].replace('.', '/'))) refuse("entry class not in application");
            for (var p : paths) {
                new ClassReader(Files.readAllBytes(p)).accept(new ClassVisitor(Opcodes.ASM9) {
                    private void type(String name) {
                        if (name == null) return;
                        if (name.startsWith("[")) {
                            Type element = Type.getType(name).getElementType();
                            if (element.getSort() != Type.OBJECT) return;
                            name = element.getInternalName();
                        }
                        if (!app.contains(name) && !BUILTINS.contains(name)) refuse(name);
                    }
                    @Override public void visit(int version,int access,String name,String signature,String parent,String[] interfaces) {
                        type(parent); for (String itf : interfaces) type(itf);
                    }
                    @Override public AnnotationVisitor visitAnnotation(String desc, boolean visible) { annotation(desc); return null; }
                    @Override public FieldVisitor visitField(int a,String n,String desc,String signature,Object value) {
                        Type t=Type.getType(desc);
                        if (t.getSort()==Type.OBJECT || t.getSort()==Type.ARRAY) type(t.getInternalName());
                        return new FieldVisitor(Opcodes.ASM9) {
                            @Override public AnnotationVisitor visitAnnotation(String desc, boolean visible) { annotation(desc); return null; }
                        };
                    }
                    @Override public MethodVisitor visitMethod(int access,String name,String desc,String signature,String[] exceptions) {
                        if ((access & (Opcodes.ACC_NATIVE | Opcodes.ACC_SYNCHRONIZED)) != 0) refuse(name);
                        return new MethodVisitor(Opcodes.ASM9) {
                            @Override public AnnotationVisitor visitAnnotation(String desc,boolean visible) { annotation(desc); return null; }
                            @Override public void visitInsn(int op) {
                                if(op==Opcodes.MONITORENTER || op==Opcodes.MONITOREXIT) refuse("monitor");
                            }
                            @Override public void visitTryCatchBlock(Label a,Label b,Label c,String exception) { refuse("exception handler"); }
                            @Override public void visitInvokeDynamicInsn(String n,String d,Handle h,Object... args) { refuse("invokedynamic"); }
                            @Override public void visitLdcInsn(Object value) {
                                if(value instanceof Handle || value instanceof ConstantDynamic) refuse("dynamic constant");
                                if(value instanceof Type t) {
                                    if(t.getSort()==Type.METHOD) refuse("method type");
                                    if(t.getSort()==Type.OBJECT || t.getSort()==Type.ARRAY) type(t.getInternalName());
                                }
                            }
                            @Override public void visitTypeInsn(int op,String n) { type(n); }
                            @Override public void visitMultiANewArrayInsn(String n,int dim) { type(n); }
                            @Override public void visitFieldInsn(int op,String owner,String field,String d) {
                                if(!app.contains(owner)) refuse(owner+"."+field);
                            }
                            @Override public void visitMethodInsn(int op,String owner,String n,String d,boolean itf) {
                                if(!app.contains(owner) && !CALLS.contains(owner+"."+n+d)) refuse(owner+"."+n+d);
                            }
                        };
                    }
                },ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
            }
        }
    }
}
