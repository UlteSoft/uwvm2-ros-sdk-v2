/* SDK companion to Open POSIX sem_getvalue/1-1.c and sem_init/1-1.c. */
#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>
#include "posixtest.h"

static int check_value(sem_t *sem, int expected)
{
    int actual = -1;
    if (sem_getvalue(sem, &actual) != 0) {
        perror("sem_getvalue");
        return PTS_FAIL;
    }
    if (actual != expected) {
        fprintf(stderr, "sem_getvalue reported %d, expected %d\n", actual, expected);
        return PTS_FAIL;
    }
    return PTS_PASS;
}

static void *post_once(void *arg)
{
    if (sem_post(arg) != 0) {
        perror("sem_post");
        return NULL;
    }
    return arg;
}

int main(void)
{
    sem_t sem;
    pthread_t worker;
    void *result = NULL;

    if (sem_init(&sem, 0, 1) != 0) {
        perror("sem_init");
        return PTS_FAIL;
    }
    if (check_value(&sem, 1) != PTS_PASS)
        return PTS_FAIL;
    if (sem_trywait(&sem) != 0) {
        perror("sem_trywait after observing one token");
        return PTS_FAIL;
    }
    if (check_value(&sem, 0) != PTS_PASS)
        return PTS_FAIL;

    int err = pthread_create(&worker, NULL, post_once, &sem);
    if (err != 0) {
        fprintf(stderr, "pthread_create returned %d\n", err);
        return PTS_UNRESOLVED;
    }
    err = pthread_join(worker, &result);
    if (err != 0) {
        fprintf(stderr, "pthread_join returned %d\n", err);
        return PTS_UNRESOLVED;
    }
    if (result != &sem || check_value(&sem, 1) != PTS_PASS)
        return PTS_FAIL;
    if (sem_destroy(&sem) != 0) {
        perror("sem_destroy");
        return PTS_FAIL;
    }
    return PTS_PASS;
}
