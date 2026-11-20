#ifndef WROS_PHP_POSIX_H
#define WROS_PHP_POSIX_H

#include <grp.h>
#include <pwd.h>
#include <stdio.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <syslog.h>
#include <unistd.h>

#ifndef PF_UNIX
#define PF_UNIX AF_UNIX
#endif
#ifndef MSG_OOB
#define MSG_OOB 1
#endif

#ifndef SOMAXCONN
#define SOMAXCONN 128
#endif
#ifndef SOL_IP
#define SOL_IP IPPROTO_IP
#endif
#ifndef SO_REUSEADDR
#define SO_REUSEADDR 2
#endif
#ifndef SO_ERROR
#define SO_ERROR 4
#endif
int socket(int, int, int);
int bind(int, const struct sockaddr *, socklen_t);
int connect(int, const struct sockaddr *, socklen_t);
int listen(int, int);
int getpeername(int, struct sockaddr *, socklen_t *);
int getsockname(int, struct sockaddr *, socklen_t *);
int setsockopt(int, int, int, const void *, socklen_t);
ssize_t sendto(int, const void *, size_t, int, const struct sockaddr *, socklen_t);
ssize_t recvfrom(int, void *, size_t, int, struct sockaddr *, socklen_t *);
FILE *popen(const char *, const char *);
int pclose(FILE *);
int mkstemp(char *);
char *mktemp(char *);
pid_t fork(void);
int kill(pid_t, int);
int setgid(gid_t);
int setuid(uid_t);
uid_t getuid(void);
uid_t geteuid(void);
gid_t getgid(void);
gid_t getegid(void);
pid_t getppid(void);
int chown(const char *, uid_t, gid_t);
int fchown(int, uid_t, gid_t);
int lchown(const char *, uid_t, gid_t);
int getgroups(int, gid_t *);
int getdtablesize(void);
mode_t umask(mode_t);

#endif
