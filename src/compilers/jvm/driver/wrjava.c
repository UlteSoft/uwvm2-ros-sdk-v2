/* Linux host entry for the OpenJDK / TeaVM guest compiler. */
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static char *join(const char *a, const char *b) {
    size_t n = strlen(a), m = strlen(b);
    char *result = malloc(n + m + 1);
    if (!result) { perror("wrjava"); exit(1); }
    memcpy(result, a, n);
    memcpy(result + n, b, m + 1);
    return result;
}

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--version") == 0) {
        puts("wrjava 1 (OpenJDK 21 / TeaVM 0.13.1 / WROS wasm32 Core 3.0, EH, MTE)");
        return 0;
    }
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        puts("wrjava --main-class PACKAGE.Main [-o OUTPUT.wasm] [--source-root DIR] [--keep-work NEW_DIR] [-O0..3|-Os|-Oz] [-g] [--] FILE.java ...\n"
             "Pass source files or one or more source directories. Output is required.\n"
             "The selected SDK supplies the platform, compiler, bindings and runtime.");
        return 0;
    }
    char executable[PATH_MAX];
    ssize_t n = readlink("/proc/self/exe", executable, sizeof(executable));
    if (n < 0 || (size_t)n >= sizeof(executable)) {
        fputs("wrjava: unable to resolve the installed executable path\n", stderr);
        return 1;
    }
    executable[n] = '\0';
    char *file = strrchr(executable, '/');
    if (!file) return 1;
    *file = '\0';
    char *bin = strrchr(executable, '/');
    if (!bin || strcmp(bin, "/bin") != 0) {
        fputs("wrjava: expected the installed SDK bin directory\n", stderr);
        return 1;
    }
    *bin = '\0';
    const char *tmp = getenv("TMPDIR");
    if (!tmp || !*tmp) tmp = ".";
    char *java = join(executable, "/share/toolchains/jdk/bin/java");
    /* The host class path is locked in install order, with WROS classes and
       C templates before upstream JARs. Relative paths keep the SDK movable. */
    char *classpath_file = join(executable, "/share/toolchains/teavm/classpath");
    FILE *in = fopen(classpath_file, "r");
    if (!in) { perror(classpath_file); return 1; }
    char *line = NULL;
    size_t capacity = 0;
    char *cp = NULL;
    while ((n = getline(&line, &capacity, in)) > 0) {
        if (line[n - 1] == '\n') line[--n] = '\0';
        if (!n) continue;
        char *entry = join(executable, line);
        if (cp) {
            char *prefix = join(cp, ":");
            free(cp);
            cp = join(prefix, entry);
            free(prefix);
            free(entry);
        } else cp = entry;
    }
    if (ferror(in) || !cp) { fputs("wrjava: invalid installed classpath\n", stderr); return 1; }
    fclose(in);
    char **args = calloc((size_t)argc + 10, sizeof(*args));
    if (!args) { perror("wrjava"); return 1; }
    size_t i = 0;
    args[i++] = java;
    args[i++] = "-XX:-UsePerfData";
    args[i++] = join("-Djava.io.tmpdir=", tmp);
    args[i++] = "-cp";
    args[i++] = cp;
    args[i++] = "WrosJava";
    args[i++] = executable;
    for (int j = 1; j < argc; ++j) args[i++] = argv[j];
    execv(java, args);
    perror(java);
    return 1;
}
