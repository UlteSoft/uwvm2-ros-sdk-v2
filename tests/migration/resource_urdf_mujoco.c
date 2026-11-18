/* Headless replay of an unmodified package resource using the official MuJoCo C API. */
#include <math.h>
#include <mujoco/mujoco.h>
#include <stdio.h>
#include <string.h>
#include <wros/package_resources.h>

static unsigned char pack[64 * 1024 * 1024];

int main(int argc, char **argv) {
    if (argc < 3 || (argc - 3) % 2) return 1;
    FILE *file = fopen(argv[1], "rb");
    if (!file) return 2;
    size_t size = fread(pack, 1, sizeof pack, file);
    int extra = fgetc(file);
    int invalid = ferror(file) || extra != EOF;
    fclose(file);
    if (invalid) return 3;
    wros_package_index index;
    wros_package_view view;
    if (!wros_package_open(pack, size, &index) ||
        !wros_package_find(&index, argv[2], strlen(argv[2]), &view) || !view.size) return 4;

    mjVFS vfs;
    mj_defaultVFS(&vfs);
    if (mj_addBufferVFS(&vfs, "robot.urdf", view.bytes, (int)view.size)) {
        mj_deleteVFS(&vfs);
        return 5;
    }
    for (int i = 3; i < argc; i += 2) {
        if (!wros_package_find(&index, argv[i + 1], strlen(argv[i + 1]), &view) ||
            mj_addBufferVFS(&vfs, argv[i], view.bytes, (int)view.size)) {
            mj_deleteVFS(&vfs);
            return 5;
        }
    }
    char error[1024] = {0};
    mjModel *model = mj_loadXML("robot.urdf", &vfs, error, sizeof error);
    mj_deleteVFS(&vfs);
    if (!model) {
        fprintf(stderr, "%s\n", error);
        return 6;
    }
    mjData *a = mj_makeData(model);
    mjData *b = mj_makeData(model);
    int failed = !a || !b;
    if (!failed) {
        for (int axis = 0; axis < model->nv; ++axis)
            a->qvel[axis] = b->qvel[axis] = 0.01 / (1 + axis);
        for (int step = 0; !failed && step < 128; ++step) {
            mj_step(model, a);
            mj_step(model, b);
            failed = !isfinite(a->time) || a->time != b->time;
            for (int j = 0; j < model->nq; ++j)
                if (!isfinite(a->qpos[j]) || a->qpos[j] != b->qpos[j]) failed = 1;
            for (int j = 0; j < model->nv; ++j)
                if (!isfinite(a->qvel[j]) || a->qvel[j] != b->qvel[j]) failed = 1;
            for (int j = 0; j < mjNWARNING; ++j)
                if (a->warning[j].number || b->warning[j].number) failed = 1;
        }
        printf("version=%s nq=%d nv=%d bodies=%d time=%.17g\n",
               mj_versionString(), model->nq, model->nv, model->nbody, a->time);
    }
    if (b) mj_deleteData(b);
    if (a) mj_deleteData(a);
    mj_deleteModel(model);
    return failed ? 7 : 0;
}
