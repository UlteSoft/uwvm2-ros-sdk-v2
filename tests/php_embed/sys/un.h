#ifndef WROS_PHP_SYS_UN_H
#define WROS_PHP_SYS_UN_H
#include <sys/socket.h>
struct sockaddr_un { sa_family_t sun_family; char sun_path[108]; };
#endif
