/* Guest-only compatibility for PHP code with C POSIX references.
 * These operations have no host implementation in the embed probe. */
#include <errno.h>
#include <netdb.h>
#include <stdbool.h>
#include <stdlib.h>
#include "wros_posix.h"
#include "ucontext.h"

static int denied(void)
{
    errno = ENOSYS;
    return -1;
}

int getcontext(ucontext_t *context) { return denied(); }
void makecontext(ucontext_t *context, void (*entry)(void), int count, ...) { __builtin_trap(); }
int swapcontext(ucontext_t *out, const ucontext_t *in) { __builtin_trap(); }

uid_t getuid(void) { return 65534; }
uid_t geteuid(void) { return 65534; }
gid_t getgid(void) { return 65534; }
gid_t getegid(void) { return 65534; }
pid_t getppid(void) { return 0; }
int getgroups(int count, gid_t *groups) { return denied(); }
int getdtablesize(void) { return 0; }

struct passwd *getpwnam(const char *name) { denied(); return NULL; }
struct passwd *getpwuid(uid_t user) { denied(); return NULL; }
struct group *getgrnam(const char *name) { denied(); return NULL; }
struct group *getgrgid(gid_t group) { denied(); return NULL; }

int mkstemp(char *path) { return denied(); }
char *mktemp(char *path) { denied(); *path = '\0'; return path; }
pid_t fork(void) { return denied(); }
pid_t wait(int *status) { return denied(); }
pid_t waitpid(pid_t pid, int *status, int options) { return denied(); }
int kill(pid_t pid, int signal) { return denied(); }
int setuid(uid_t uid) { return denied(); }
int setgid(gid_t gid) { return denied(); }
int chown(const char *path, uid_t user, gid_t group) { return denied(); }
int lchown(const char *path, uid_t user, gid_t group) { return denied(); }
int fchown(int fd, uid_t user, gid_t group) { return denied(); }
mode_t umask(mode_t value)
{
    static mode_t current = 077;
    const mode_t previous = current;
    current = value & 0777;
    return previous;
}

FILE *popen(const char *command, const char *mode) { denied(); return NULL; }
int pclose(FILE *file) { return denied(); }
void openlog(const char *source, int options, int facility) {}
void closelog(void) {}
void syslog(int level, const char *format, ...) {}

int socket(int domain, int type, int protocol) { return denied(); }
int connect(int fd, const struct sockaddr *address, socklen_t length) { return denied(); }
int bind(int fd, const struct sockaddr *address, socklen_t length) { return denied(); }
int listen(int fd, int backlog) { return denied(); }
int shutdown(int fd, int how) { return denied(); }
int accept(int fd, struct sockaddr *address, socklen_t *length) { return denied(); }
int getpeername(int fd, struct sockaddr *address, socklen_t *length) { return denied(); }
int getsockname(int fd, struct sockaddr *address, socklen_t *length) { return denied(); }
int setsockopt(int fd, int level, int opt, const void *value, socklen_t size) { return denied(); }
int getsockopt(int fd, int level, int opt, void *value, socklen_t *size) { return denied(); }
ssize_t recv(int fd, void *buffer, size_t size, int flags) { return denied(); }
ssize_t send(int fd, const void *buffer, size_t size, int flags) { return denied(); }
ssize_t sendto(int fd, const void *buffer, size_t size, int flags, const struct sockaddr *address, socklen_t length) { return denied(); }
ssize_t recvfrom(int fd, void *buffer, size_t size, int flags, struct sockaddr *address, socklen_t *length) { return denied(); }

int getaddrinfo(const char *name, const char *service, const struct addrinfo *hints, struct addrinfo **answer)
{
    if (answer) *answer = NULL;
    return EAI_FAIL;
}
void freeaddrinfo(struct addrinfo *answer) {}
const char *gai_strerror(int status) { return "Name resolution unavailable"; }
int getnameinfo(const struct sockaddr *address, socklen_t size, char *hostname, socklen_t hostsize,
                char *service, socklen_t servicesize, int flags) { return EAI_FAIL; }
struct hostent *gethostbyname(const char *name) { return NULL; }
int gethostbyname_r(const char *name, struct hostent *entry, char *storage, size_t size,
                   struct hostent **answer, int *lookup_error)
{
    *answer = NULL;
    *lookup_error = NO_RECOVERY;
    errno = ENOSYS;
    return ENOSYS;
}
struct hostent *gethostbyaddr(const void *address, socklen_t size, int type) { return NULL; }
struct protoent *getprotobyname(const char *name) { return NULL; }
struct protoent *getprotobynumber(int protocol) { return NULL; }
struct servent *getservbyname(const char *name, const char *transport) { return NULL; }
struct servent *getservbyport(int port, const char *transport) { return NULL; }

int madvise(void *address, size_t length, int advice) { return denied(); }
int initgroups(const char *name, gid_t group) { return denied(); }
int getpwnam_r(const char *name, struct passwd *value, char *buffer, size_t size, struct passwd **answer)
{
    *answer = NULL;
    return ENOSYS;
}
int getpwuid_r(uid_t user, struct passwd *value, char *buffer, size_t size, struct passwd **answer)
{
    *answer = NULL;
    return ENOSYS;
}

void *dlopen(const char *path, int options) { denied(); return NULL; }
void *dlsym(void *handle, const char *symbol) { denied(); return NULL; }
int dlclose(void *handle) { return denied(); }
char *dlerror(void) { return "Dynamic loading unavailable"; }
