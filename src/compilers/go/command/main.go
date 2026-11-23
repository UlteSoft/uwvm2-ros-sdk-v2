// wrgo and wrtg compile an application module with the selected native toolchain.
package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
)

// Set when building each independent command.
var language = "go"

const moduleRoot = "github.com/UlteSoft/uwvm2-ros-sdk-v2/"

type options struct {
	project, out, platform, target, core, opt string
	wordBits                                  int
	mte, eh, memory64, threads, debug, show   bool
}

func parse(args []string) (options, error) {
	o := options{target: "wasm32", core: "3.0", mte: true, eh: true, memory64: true}
	for i := 0; i < len(args); i++ {
		key := args[i]
		switch key {
		case "-o", "--output", "--platform", "--target", "--core", "--go-word-bits":
			i++
			if i == len(args) {
				return o, fmt.Errorf("%s requires a value", key)
			}
			value := args[i]
			switch key {
			case "-o", "--output":
				o.out = value
			case "--platform":
				o.platform = value
			case "--target":
				o.target = value
			case "--core":
				o.core = value
			case "--go-word-bits":
				if value != "32" && value != "64" {
					return o, errors.New("--go-word-bits expects 32 or 64")
				}
				o.wordBits, _ = strconv.Atoi(value)
			}
		case "--mte", "--no-mte":
			o.mte = key == "--mte"
		case "--eh", "--no-eh":
			o.eh = key == "--eh"
		case "--memory64", "--no-memory64":
			o.memory64 = key == "--memory64"
		case "--threads", "--no-threads":
			o.threads = key == "--threads"
		case "-O0", "-O1", "-O2", "-O3", "-Os", "-Oz":
			o.opt = key[2:]
		case "-g":
			o.debug = true
		case "--print-target":
			o.show = true
		default:
			if strings.HasPrefix(key, "-") || o.project != "" {
				return o, fmt.Errorf("unexpected argument %q", key)
			}
			o.project = key
		}
	}
	return o, nil
}

func command(env []string, dir, program string, args ...string) *exec.Cmd {
	cmd := exec.Command(program, args...)
	cmd.Dir, cmd.Env, cmd.Stderr = dir, env, os.Stderr
	return cmd
}

func run(env []string, dir, program string, args ...string) error {
	cmd := command(env, dir, program, args...)
	cmd.Stdout = os.Stdout
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("%s: %w", filepath.Base(program), err)
	}
	return nil
}

type modVersion struct{ Path, Version string }
type workfile struct {
	Go      string
	Use     []struct{ DiskPath string }
	Replace []struct{ Old, New modVersion }
}

func rooted(root, path string) string {
	if filepath.IsAbs(path) {
		return path
	}
	return filepath.Join(root, path)
}

// Preserve the user's local workspace modules and dependency replacements.
// SDK module paths always refer to this installation's public packages.
func workspace(env []string, root, project, scratch, platform string) (string, error) {
	goexe := filepath.Join(root, "libexec/go/bin/go")
	work, err := command(env, project, goexe, "env", "GOWORK").Output()
	if err != nil {
		return "", err
	}
	w := workfile{}
	active := strings.TrimSpace(string(work))
	if active != "" && active != "off" {
		data, err := command(env, project, goexe, "work", "edit", "-json", active).Output()
		if err != nil {
			return "", err
		}
		if err := json.Unmarshal(data, &w); err != nil {
			return "", err
		}
	}
	var output strings.Builder
	output.WriteString("go 1.24.2\n\nuse (\n")
	seen := make(map[string]bool)
	use := func(p string) {
		if !seen[p] {
			fmt.Fprintln(&output, "\t"+strconv.Quote(p))
			seen[p] = true
		}
	}
	use(project)
	for _, u := range w.Use {
		use(rooted(filepath.Dir(active), u.DiskPath))
	}
	output.WriteString(")\n\n")
	modules := []string{moduleRoot + "u2rosv2"}
	locals := map[string]string{modules[0]: filepath.Join(root, "include/u2rosv2/universal/go")}
	if platform != "generic" {
		if platform == "" || strings.Trim(platform, "abcdefghijklmnopqrstuvwxyz0123456789_-") != "" {
			return "", fmt.Errorf("invalid installed platform %q", platform)
		}
		mod := moduleRoot + platform
		modules = append(modules, mod)
		locals[mod] = filepath.Join(root, "include/u2rosv2/platform", platform, "go")
	}
	for _, replace := range w.Replace {
		if _, installed := locals[replace.Old.Path]; installed {
			continue
		}
		dst := replace.New.Path
		if replace.New.Version == "" {
			dst = rooted(filepath.Dir(active), dst)
		}
		fmt.Fprintf(&output, "replace %s %s => %s %s\n", strconv.Quote(replace.Old.Path), replace.Old.Version,
			strconv.Quote(dst), replace.New.Version)
	}
	for _, mod := range modules {
		dir := locals[mod]
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err != nil {
			return "", err
		}
		// A membership in the user's workspace already gives the identical
		// module main-module status. Avoid an illegal wildcard replacement.
		if !seen[dir] {
			fmt.Fprintf(&output, "replace %s => %s\n", mod, strconv.Quote(dir))
		}
	}
	path := filepath.Join(scratch, "go.work")
	return path, os.WriteFile(path, []byte(output.String()), 0600)
}

func buildStandard(env []string, root, project, output string, o options) error {
	tags := []string{"u2ros"}
	if o.mte {
		tags = append(tags, "u2ros_mte")
	}
	if o.eh {
		tags = append(tags, "u2ros_eh")
	}
	ldflags := "-buildid="
	if !o.debug {
		ldflags += " -s -w"
	}
	flags := []string{"build", "-trimpath", "-buildvcs=false", "-tags", strings.Join(tags, ","), "-ldflags", ldflags}
	switch o.opt {
	case "0":
		flags = append(flags, "-gcflags=all=-N -l")
	case "", "2":
	default:
		return errors.New("standard Go accepts -O0 or its normal optimization profile -O2")
	}
	return run(env, project, filepath.Join(root, "libexec/go/bin/go"), append(flags, "-o", output, ".")...)
}

func buildTiny(env []string, root, project, work, output string, o options) error {
	tiny := filepath.Join(root, "libexec/tinygo")
	back := filepath.Join(root, "share/toolchains/tinygo-llvm")
	input, ir := filepath.Join(work, "app.bc"), filepath.Join(work, "lower.bc")
	opt := o.opt
	if opt == "" {
		opt = "2"
	}
	flags := []string{"build", "-target=wasip1", "-scheduler=none", "-gc=conservative", "-buildmode=wasi-legacy", "-opt=" + opt}
	tags := []string{"custommalloc", "u2ros"}
	if o.eh {
		tags = append(tags, "u2ros_eh")
		flags = append(flags, "-panic=print")
	} else {
		flags = append(flags, "-panic=trap")
	}
	mode := "--no-mte"
	if o.mte {
		tags = append(tags, "u2ros_mte")
		mode = "--mte"
	}
	flags = append(flags, "-tags="+strings.Join(tags, ","), "-o", input, ".")
	if err := run(env, project, filepath.Join(tiny, "bin/tinygo"), flags...); err != nil {
		return err
	}
	if err := run(env, work, filepath.Join(back, "prepare-ir"), mode, input, ir); err != nil {
		return err
	}
	common := []string{"--no-default-config", "--target=wasm32-unknown-wasip1", "-mcpu=mvp", "-mbulk-memory", "-mbulk-memory-opt",
		"-mmultivalue", "-mmutable-globals", "-mnontrapping-fptoint", "-mreference-types", "-msign-ext", "-msimd128",
		"-mextended-const", "-mtail-call", "-mmultimemory", "-mgc", "-mrelaxed-simd", "-mno-atomics", "-O" + opt}
	if o.opt == "" {
		common[len(common)-1] = "-O3"
	}
	if o.eh {
		common = append(common, "-fwasm-exceptions", "-mllvm", "-wasm-use-legacy-eh=false")
	} else {
		common = append(common, "-fno-exceptions")
	}
	if o.mte {
		common = append(common, "-fsanitize=memtag")
	} else {
		common = append(common, "-fno-sanitize=memtag")
	}
	if o.debug {
		common = append(common, "-g")
	}
	sources := []string{ir, filepath.Join(tiny, "src/runtime/asm_tinygowasm.S"), filepath.Join(back, "runtime/memory.S"), filepath.Join(back, "runtime/support.c")}
	if o.mte {
		sources = append(sources, filepath.Join(back, "runtime/gc.c"))
	}
	if o.eh {
		sources = append(sources, filepath.Join(back, "runtime/panic.S"))
	}
	link := []string{"--fatal-warnings", "--gc-sections", "--no-entry", "--export=_start", "--stack-first", "-z", "stack-size=65536"}
	if o.mte {
		link = append(link, "--max-memory=268435456")
	}
	if !o.debug {
		link = append(link, "--strip-debug")
	}
	for i, src := range sources {
		obj := filepath.Join(work, fmt.Sprintf("%d.o", i))
		cmd := append([]string{}, common...)
		if o.eh && filepath.Ext(src) == ".S" {
			// The integrated assembler needs the target feature for Wasm throw.
			cmd = append(cmd, "-mexception-handling")
		}
		if filepath.Ext(src) == ".c" {
			cmd = append(cmd, "-ffreestanding", "-fno-builtin", "-nostdinc")
		}
		cmd = append(cmd, "-c", src, "-o", obj)
		if err := run(env, work, filepath.Join(back, "clang"), cmd...); err != nil {
			return err
		}
		link = append(link, obj)
	}
	return run(env, work, filepath.Join(back, "wasm-ld"), append(link, "-o", output)...)
}

func execute(o options) error {
	bits := 64
	if language == "tinygo" {
		bits = 32
		if o.opt == "3" {
			return errors.New("TinyGo accepts -O0, -O1, -O2, -Os or -Oz")
		}
	}
	if o.core != "3.0" || o.target != "wasm32" || o.threads {
		return errors.New("this compiler targets single-threaded Core 3.0 modules with a 32-bit linear memory")
	}
	if o.wordBits != 0 && o.wordBits != bits {
		return fmt.Errorf("%s has %d-bit Go int, pointer and uintptr on this target", language, bits)
	}
	if o.show {
		return json.NewEncoder(os.Stdout).Encode(map[string]any{"language": language, "wasm_index_bits": 32, "go_word_bits": bits, "go_pointer_bits": bits,
			"core": o.core, "mte": o.mte, "eh": o.eh, "threads": false, "memory64_feature": o.memory64})
	}
	if o.project == "" || filepath.Ext(o.out) != ".wasm" {
		return errors.New("supply a Go module directory and -o FILE.wasm")
	}
	project, err := filepath.Abs(o.project)
	if err != nil {
		return err
	}
	if _, err := os.Stat(filepath.Join(project, "go.mod")); err != nil {
		return err
	}
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	exe, err = filepath.EvalSymlinks(exe)
	if err != nil {
		return err
	}
	root := filepath.Dir(filepath.Dir(exe))
	var selection struct{ Language, Platform string }
	info, err := os.ReadFile(filepath.Join(root, "selection.json"))
	if err != nil {
		return err
	}
	if err := json.Unmarshal(info, &selection); err != nil {
		return err
	}
	if selection.Language != language || (o.platform != "" && selection.Platform != o.platform) {
		return errors.New("requested target differs from the installed language/platform selection")
	}
	out, err := filepath.Abs(o.out)
	if err != nil {
		return err
	}
	parent := filepath.Dir(out)
	if err := os.MkdirAll(parent, 0755); err != nil {
		return err
	}
	work, err := os.MkdirTemp(parent, ".u2ros-go-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(work)
	goroot := filepath.Join(root, "libexec/go")
	env := append(os.Environ(), "GOENV=off", "GOTOOLCHAIN=local", "GOFLAGS=", "GOOS=wasip1", "GOARCH=wasm", "CGO_ENABLED=0",
		"GOWASM=satconv,signext", "GOROOT="+goroot, "TMPDIR="+work, "GOTMPDIR="+work, "XDG_CACHE_HOME="+filepath.Join(work, "cache"),
		"PATH="+filepath.Join(goroot, "bin")+string(os.PathListSeparator)+os.Getenv("PATH"))
	if os.Getenv("GOPROXY") == "" {
		env = append(env, "GOPROXY=off")
	}
	if os.Getenv("GOCACHE") == "" {
		env = append(env, "GOCACHE="+filepath.Join(work, "gocache"))
	}
	ws, err := workspace(env, root, project, work, selection.Platform)
	if err != nil {
		return err
	}
	env = append(env, "GOWORK="+ws)
	result := filepath.Join(work, "application.wasm")
	if language == "go" {
		err = buildStandard(env, root, project, result, o)
	} else {
		env = append(env, "TINYGOROOT="+filepath.Join(root, "libexec/tinygo"))
		err = buildTiny(env, root, project, work, result, o)
	}
	if err != nil {
		return err
	}
	return os.Rename(result, out)
}

func main() {
	if len(os.Args) == 2 {
		switch os.Args[1] {
		case "-h", "--help":
			fmt.Println(filepath.Base(os.Args[0]), "PROJECT -o FILE.wasm [--platform NAME] [--target wasm32] [--core 3.0] [--go-word-bits N] [--[no-]mte] [--[no-]eh] [--[no-]memory64] [--[no-]threads] [-Olevel] [-g] [--print-target]")
			return
		case "--version":
			fmt.Println(filepath.Base(os.Args[0]), map[string]string{"go": "Go 1.24.2", "tinygo": "TinyGo 0.38.0 / Go 1.24.2"}[language])
			return
		}
	}
	o, err := parse(os.Args[1:])
	if err == nil {
		err = execute(o)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, filepath.Base(os.Args[0])+":", err)
		os.Exit(1)
	}
}
