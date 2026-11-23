// Native Linux entry points for the SDK's Wasm-only LLVM Clang.
// Public entry points retain the compiler in this executable. A separate admission process
// checks the inputs and publishes the result after Clang returns.
#include "llvm/Support/InitLLVM.h"
#include "llvm/Support/LLVMDriver.h"
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <string>
#include <vector>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <unistd.h>

int clang_main(int, char **, const llvm::ToolContext &);
namespace fs = std::filesystem;
using Strings = std::vector<std::string>;

static int error(const char *message) {
  std::fprintf(stderr, "WROS Clang: %s\n", message);
  return 1;
}

static std::vector<char *> pointers(Strings &strings) {
  std::vector<char *> result;
  for (auto &s : strings)
    result.push_back(s.data());
  result.push_back(nullptr);
  return result;
}

static int status(pid_t child) {
  if (child < 0) return error(std::strerror(errno));
  int result;
  while (waitpid(child, &result, 0) < 0)
    if (errno != EINTR) return error(std::strerror(errno));
  return WIFEXITED(result) ? WEXITSTATUS(result) : 128 + WTERMSIG(result);
}

static bool receive(int fd, void *buffer, size_t bytes, bool *eof = nullptr) {
  auto *p = static_cast<char *>(buffer);
  while (bytes) {
    ssize_t n = read(fd, p, bytes);
    if (n < 0 && errno == EINTR) continue;
    if (n <= 0) {
      if (eof) *eof = n == 0 && p == buffer;
      return false;
    }
    p += n;
    bytes -= size_t(n);
  }
  return true;
}

static void compile(Strings &args, bool embedded) {
  // The compiler and linker accept environment overrides. Pass only the
  // documented temporary directory and reproducible-build epoch to the tools.
  Strings env = {"LC_ALL=C", "TZ=UTC", "PATH=" + fs::path(args[0]).parent_path().string() + ":/bin:/usr/bin"};
  for (auto key : {"TMPDIR", "SOURCE_DATE_EPOCH"})
    if (auto value = std::getenv(key)) env.emplace_back(std::string(key) + "=" + value);
  auto environment = pointers(env);
  // Ordinary clang can spawn /proc/self/exe with -cc1. Here that path is
  // named wrcc, so run its linked cc1 directly in this compiler process.
  if (embedded) args.insert(args.begin() + 1, "-fintegrated-cc1");
  auto argv = pointers(args);
  if (embedded) {
    environ = environment.data();
    int count = int(args.size());
    char **raw = argv.data();
    llvm::InitLLVM init(count, raw, true, true);
    int code = clang_main(count, raw, {raw[0], nullptr, false});
    std::fflush(nullptr);
    _exit(code);
  }
  // An explicit operator toolchain may have a different qualified compiler.
  execve(argv[0], argv.data(), environment.data());
  _exit(error(std::strerror(errno)));
}

static int sdk_compile(const fs::path &sdk, const std::string &name, int argc, char **argv) {
  int sockets[2];
  if (socketpair(AF_UNIX, SOCK_STREAM, 0, sockets)) return error(std::strerror(errno));
  pid_t policy = fork();
  if (!policy) {
    close(sockets[0]);
    bool objc = name == "wroc" || name == "wrocxx";
    auto helper = sdk / (objc ? "src/compilers/objc/driver/policy.py" : "install/cc_policy.py");
    const char *language = objc ? (name == "wrocxx" ? "objcpp" : "objc")
                                : (name == "wrcc" ? "cpp" : "c");
    Strings args = {"python3", "-I", "-B", helper.string(), language, std::to_string(sockets[1])};
    args.insert(args.end(), argv + 1, argv + argc);
    auto raw = pointers(args);
    execvp(raw[0], raw.data());
    _exit(error("Python 3 is required to check the SDK qualification and Wasm imports"));
  }
  close(sockets[1]);
  if (policy < 0) { close(sockets[0]); return error(std::strerror(errno)); }
  bool valid = true;
  while (valid) {
    uint32_t length;
    bool eof = false;
    if (!receive(sockets[0], &length, sizeof(length), &eof)) {
      valid = eof;
      break;
    }
    length = ntohl(length);
    valid = length > 0 && length <= 8 * 1024 * 1024;
    std::string packet(valid ? length : 0, '\0');
    valid = valid && receive(sockets[0], packet.data(), packet.size()) && packet.back() == '\0';
    Strings words;
    if (valid) {
      for (size_t pos = 0; pos < packet.size();) {
        size_t end = packet.find('\0', pos);
        words.emplace_back(packet, pos, end - pos);
        pos = end + 1;
      }
      valid = words.size() >= 3 && (words[0] == "embedded" || words[0] == "external")
              && fs::path(words[1]).is_absolute();
    }
    if (valid) {
      bool embedded = words[0] == "embedded";
      words.erase(words.begin());
      pid_t compiler = fork();
      if (!compiler) { close(sockets[0]); compile(words, embedded); }
      uint32_t code = htonl(uint32_t(status(compiler)));
      valid = send(sockets[0], &code, sizeof(code), MSG_NOSIGNAL) == sizeof(code);
    }
  }
  close(sockets[0]);
  int result = status(policy);
  return valid ? result : error("incomplete compilation request from qualification helper");
}

int main(int argc, char **argv) {
  std::string name = fs::path(argv[0]).filename().string();
  if (name == "wrc" || name == "wrcc" || name == "wroc" || name == "wrocxx") {
    std::error_code ec;
    auto exe = fs::read_symlink("/proc/self/exe", ec);
    if (ec) return error("cannot locate installed native compiler");
    auto sdk = exe.parent_path().parent_path();
    if (argc == 2) {
      std::string option = argv[1];
      const std::string prefix = "--print-prog-name=";
      if (option.compare(0, prefix.size(), prefix) == 0) {
        auto tool = option.substr(prefix.size());
        if (tool != "clang" && tool != "clang++" && tool != "wasm-ld" && tool != "llvm-ar")
          return error("expected clang, clang++, wasm-ld or llvm-ar");
        auto file = sdk / "share/toolchains/portable/bin" / tool;
        if (!fs::is_regular_file(file, ec)) return error("requested native tool is absent from this installation");
        std::puts(file.c_str());
        return 0;
      }
      if (option == "--version" || option == "--print-targets") {
        llvm::InitLLVM init(argc, argv, true, true);
        return clang_main(argc, argv, {argv[0], nullptr, false});
      }
    }
    return sdk_compile(sdk, name, argc, argv);
  }
  llvm::InitLLVM init(argc, argv, true, true);
  return clang_main(argc, argv, {argv[0], nullptr, false});
}
