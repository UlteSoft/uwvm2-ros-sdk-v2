import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.TreeSet;
import java.util.stream.Collectors;
import javax.lang.model.SourceVersion;
import javax.tools.ToolProvider;

/** Compile user source with the installed OpenJDK, WROS TeaVM port and C backend. */
public final class WrosJava {
    private final TreeSet<Path> sources = new TreeSet<>();
    private final Path sdk;
    private final Path toolchain;
    private final String platform;
    private String mainClass;
    private String optimize = "-O2";
    private boolean debug;
    private Path output;
    private Path keep;

    private WrosJava(Path sdk) throws IOException {
        this.sdk = sdk;
        toolchain = sdk.resolve("share/toolchains/teavm");
        platform = Files.readString(toolchain.resolve("platform")).strip();
    }

    private void source(Path file) throws IOException {
        if (!Files.isRegularFile(file) || !file.toString().endsWith(".java")) {
            throw new IllegalArgumentException("expected a Java source file: " + file);
        }
        sources.add(file.toRealPath());
    }

    private void sourceRoot(Path root) throws IOException {
        if (!Files.isDirectory(root)) throw new IllegalArgumentException("missing source directory: " + root);
        try (var entries = Files.walk(root)) {
            var files = entries.filter(file -> file.toString().endsWith(".java") && Files.isRegularFile(file)).toList();
            if (files.isEmpty()) throw new IllegalArgumentException("empty source directory: " + root);
            for (Path file : files) source(file);
        }
    }

    private static String option(String[] args, int index) {
        if (index >= args.length) throw new IllegalArgumentException("missing value after " + args[index - 1]);
        return args[index];
    }

    private void parse(String[] args) throws IOException {
        boolean filesOnly = false;
        for (int i = 1; i < args.length; ++i) {
            String arg = args[i];
            if (filesOnly || !arg.startsWith("-")) {
                source(Path.of(arg));
                continue;
            }
            switch (arg) {
                case "--" -> filesOnly = true;
                case "--main-class" -> mainClass = option(args, ++i);
                case "--source-root" -> sourceRoot(Path.of(option(args, ++i)));
                case "--keep-work" -> keep = Path.of(option(args, ++i)).toAbsolutePath();
                case "-o", "--output" -> output = Path.of(option(args, ++i)).toAbsolutePath();
                case "-g" -> debug = true;
                case "-O0", "-O1", "-O2", "-O3", "-Os", "-Oz" -> optimize = arg;
                case "--platform", "--target", "--core" -> {
                    String expected = switch (arg) {
                        case "--platform" -> platform;
                        case "--target" -> "wasm32";
                        default -> "3.0";
                    };
                    if (!option(args, ++i).equals(expected)) {
                        throw new IllegalArgumentException(arg + " must match " + expected);
                    }
                }
                case "--memory64", "--eh", "--mte", "--no-threads" -> { }
                default -> throw new IllegalArgumentException("unsupported Java build option: " + arg);
            }
        }
        if (mainClass == null || !SourceVersion.isName(mainClass)) {
            throw new IllegalArgumentException("--main-class requires a Java binary name");
        }
        if (output == null || !output.toString().endsWith(".wasm") || sources.isEmpty()) {
            throw new IllegalArgumentException("provide Java sources and -o OUTPUT.wasm");
        }
    }

    private static String classpath(List<Path> paths) {
        for (Path path : paths) {
            if (path.toString().contains(File.pathSeparator)) {
                throw new IllegalArgumentException("a class path entry contains the path separator: " + path);
            }
        }
        return paths.stream().map(Path::toString).collect(Collectors.joining(File.pathSeparator));
    }

    private void compile(Path work) throws Exception {
        Path classes = Files.createDirectory(work.resolve("classes"));
        Path generated = Files.createDirectory(work.resolve("generated"));
        List<Path> inputs = new ArrayList<>();
        inputs.add(toolchain.resolve("runtime"));
        inputs.add(classes);
        for (String name : Files.readAllLines(toolchain.resolve("jars.list"))) {
            inputs.add(toolchain.resolve("jars").resolve(name));
        }
        var javac = ToolProvider.getSystemJavaCompiler();
        if (javac == null || Runtime.version().feature() != 21) {
            throw new IOException("the selected JDK must contain the Java 21 compiler module");
        }
        var flags = new ArrayList<>(List.of("-source", "21", "-target", "21", "-g", "-proc:none",
                "-encoding", "UTF-8", "-classpath", classpath(inputs), "-d", classes.toString()));
        try (var manager = javac.getStandardFileManager(null, java.util.Locale.ROOT, java.nio.charset.StandardCharsets.UTF_8)) {
            var units = manager.getJavaFileObjectsFromPaths(sources);
            if (!javac.getTask(null, manager, null, flags, null, units).call()) throw new IOException("javac failed");
        }
        if (!Files.isRegularFile(classes.resolve(mainClass.replace('.', '/') + ".class"))) {
            throw new IOException("javac did not emit the requested entry: " + mainClass);
        }
        Translate.main(new String[]{"C", generated.toString(), classpath(inputs), mainClass});
        Path entry = generated.resolve("wros_entry.c");
        Files.copy(sdk.resolve("src/compilers/jvm/driver/entry.c"), entry);
        Path linked = work.resolve("linked.wasm");
        var command = new ArrayList<>(List.of(sdk.resolve("libexec/java-c/bin/wrc").toString(), "--target", "wasm32",
                "--core", "3.0", "--memory64", "--eh", "--mte", "--no-threads", "--reactor", "--export", "_start",
                optimize, "-D", "__WASM_MEMTAG__=1"));
        if (debug) command.add("-g");
        command.addAll(List.of(entry.toString(), "-o", linked.toString()));
        var builder = new ProcessBuilder(command).inheritIO();
        builder.environment().put("TMPDIR", work.toString());
        if (builder.start().waitFor() != 0) throw new IOException("WROS C link failed");
        try (var wasm = Files.newInputStream(linked)) {
            if (!Arrays.equals(wasm.readNBytes(8), new byte[]{0,'a','s','m',1,0,0,0})) {
                throw new IOException("the linker did not produce a Core WebAssembly module");
            }
        }
        Path pending = Files.createTempFile(output.getParent(), ".wrjava-", ".wasm");
        try {
            Files.copy(linked, pending, StandardCopyOption.REPLACE_EXISTING);
            Files.move(pending, output, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } finally { Files.deleteIfExists(pending); }
    }

    private void run() throws Exception {
        sourceRoot(sdk.resolve("include/u2rosv2/universal/java/src"));
        if (!platform.equals("generic")) sourceRoot(sdk.resolve("include/u2rosv2/platform").resolve(platform).resolve("java/src"));
        Files.createDirectories(output.getParent());
        Path work = keep != null ? Files.createDirectory(keep)
                : Files.createTempDirectory(output.getParent(), ".wrjava-build-");
        try {
            compile(work);
        } finally {
            if (keep == null) {
                try (var entries = Files.walk(work)) {
                    for (Path file : entries.sorted(Comparator.reverseOrder()).toList()) Files.delete(file);
                }
            }
        }
    }

    public static void main(String[] args) {
        try {
            var driver = new WrosJava(Path.of(args[0]));
            driver.parse(args);
            driver.run();
        } catch (Exception error) {
            System.err.println("wrjava: " + error);
            System.exit(1);
        }
    }
}
