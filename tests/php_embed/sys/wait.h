#ifndef WROS_PHP_SYS_WAIT_H
#define WROS_PHP_SYS_WAIT_H
#include <sys/types.h>
#define WIFEXITED(status) (((unsigned)(status) & 127u) == 0u)
#define WEXITSTATUS(status) (((unsigned)(status) >> 8) & 255u)
#define WIFSIGNALED(status) (((unsigned)(status) & 127u) > 0u && ((unsigned)(status) & 127u) < 127u)
#define WTERMSIG(status) ((unsigned)(status) & 127u)
pid_t wait(int *);
pid_t waitpid(pid_t, int *, int);
#endif
