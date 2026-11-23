/* SDK companion to Open POSIX pthread_rwlock_init/1-1.c. */
#include <pthread.h>
#include <stdio.h>
#include "posixtest.h"

static void *read_once(void *arg)
{
    pthread_rwlock_t *lock = arg;
    int err = pthread_rwlock_rdlock(lock);
    if (err != 0) {
        fprintf(stderr, "pthread_rwlock_rdlock returned %d\n", err);
        return NULL;
    }
    err = pthread_rwlock_unlock(lock);
    if (err != 0) {
        fprintf(stderr, "reader unlock returned %d\n", err);
        return NULL;
    }
    return lock;
}

int main(void)
{
    pthread_rwlockattr_t attr;
    pthread_rwlock_t lock;
    pthread_t reader;
    void *result = NULL;

    int err = pthread_rwlockattr_init(&attr);
    if (err != 0) {
        fprintf(stderr, "pthread_rwlockattr_init returned %d\n", err);
        return PTS_UNRESOLVED;
    }
    err = pthread_rwlock_init(&lock, &attr);
    if (err != 0) {
        fprintf(stderr, "pthread_rwlock_init returned %d\n", err);
        return PTS_FAIL;
    }
    err = pthread_create(&reader, NULL, read_once, &lock);
    if (err != 0) {
        fprintf(stderr, "pthread_create returned %d\n", err);
        return PTS_UNRESOLVED;
    }
    err = pthread_join(reader, &result);
    if (err != 0) {
        fprintf(stderr, "pthread_join returned %d\n", err);
        return PTS_UNRESOLVED;
    }
    if (result != &lock)
        return PTS_FAIL;

    /* The reader completed. An unlocked lock must now admit a writer. */
    err = pthread_rwlock_trywrlock(&lock);
    if (err != 0) {
        fprintf(stderr, "pthread_rwlock_trywrlock returned %d\n", err);
        return PTS_FAIL;
    }
    err = pthread_rwlock_unlock(&lock);
    if (err != 0) {
        fprintf(stderr, "writer unlock returned %d\n", err);
        return PTS_FAIL;
    }
    err = pthread_rwlock_destroy(&lock);
    if (err != 0) {
        fprintf(stderr, "pthread_rwlock_destroy returned %d\n", err);
        return PTS_FAIL;
    }
    err = pthread_rwlockattr_destroy(&attr);
    if (err != 0) {
        fprintf(stderr, "pthread_rwlockattr_destroy returned %d\n", err);
        return PTS_UNRESOLVED;
    }
    return PTS_PASS;
}
