import java.io.File;
import java.net.URLClassLoader;
import java.util.*;
import org.teavm.tooling.*;
import org.teavm.vm.TeaVMOptimizationLevel;
public final class Translate {
    public static void main(String[] args) throws Exception {
        var entries = new ArrayList<File>();
        var urls = new ArrayList<java.net.URL>();
        for(String p : args[2].split(File.pathSeparator)) {
            var f = new File(p); entries.add(f); urls.add(f.toURI().toURL());
        }
        try(var loader = new URLClassLoader(urls.toArray(java.net.URL[]::new),Translate.class.getClassLoader())) {
            var compiler = new TeaVMTool();
            var log = new ConsoleTeaVMToolLog(false);
            compiler.setClassLoader(loader);
            compiler.setClassPath(entries);
            compiler.setMainClass(args[3]);
            compiler.setTargetType(TeaVMTargetType.valueOf(args[0]));
            compiler.setTargetDirectory(new File(args[1]));
            compiler.setTargetFileName("app");
            compiler.setOptimizationLevel(TeaVMOptimizationLevel.FULL);
            // Preserve bytecode source positions through TeaVM's C line directives.
            compiler.setDebugInformationGenerated(true);
            compiler.setStrict(true);
            compiler.setObfuscated(false);
            compiler.setMinHeapSize(2*1024*1024);
            compiler.setMaxHeapSize(16*1024*1024);
            compiler.setLog(log);
            compiler.generate();
            if(compiler.getDependencyInfo()!=null)
                TeaVMProblemRenderer.describeProblems(compiler.getDependencyInfo().getCallGraph(),compiler.getProblemProvider(),log);
            if(!compiler.getProblemProvider().getSevereProblems().isEmpty()) throw new IllegalStateException("AOT rejected");
        }
    }
}
