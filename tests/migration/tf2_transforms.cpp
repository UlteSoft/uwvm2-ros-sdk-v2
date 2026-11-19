// Evaluate original tf2 kernels with runtime-loaded operands in all builds.
#include "adapter.h"
#include "expected.h"

struct Scenario {
    double parent_q[4], parent_t[3], child_q[4], child_t[3], point[3];
    double expected_world[3], expected_relative[3], expected_origin[3];
};
#include "vectors.h"

static Vector3 position(const volatile double* p) {
    const double x = p[0], y = p[1], z = p[2];
    return Vector3(x, y, z);
}

static Transform pose(const volatile double* q, const volatile double* t) {
    const double x = q[0], y = q[1], z = q[2], w = q[3];
    return Transform(Quaternion(x, y, z, w), position(t));
}

static bool same(const Vector3& actual, const volatile double* expected, double x_offset = 0.0) {
    // Groovy and later headers may select different scalar precision.
    const double tol = sizeof(actual.x()) == sizeof(float) ? 3e-5 : 2e-11;
    for (int i = 0; i < 3; ++i) {
        const double target = expected[i] + (i == 0 ? x_offset : 0);
        const double error = actual[i] - target;
        if (!(error <= tol && error >= -tol)) return false;
    }
    return true;
}

static int probe() {
    for (const volatile Scenario& s : scenarios) {
        const Transform a = pose(s.parent_q, s.parent_t), b = pose(s.child_q, s.child_t);
        const Vector3 p = position(s.point);
        const Transform joint = a * b;
        const Vector3 world = joint * p;
        if (!same(world, s.expected_world, ALTER_EXPECTATION ? 1.0 : 0.0) ||
            !same(a * (b * p), s.expected_world) ||
            !same(joint.getOrigin(), s.expected_origin) ||
            !same(joint.inverse() * world, s.point) ||
            !same(joint.invXform(world), s.point) ||
            !same(a.inverseTimes(b) * p, s.expected_relative)) return 17;
        const Transform reconstructed(joint.getRotation(), joint.getOrigin());
        if (!same(reconstructed * p, s.expected_world)) return 17;
    }
    return 0;
}

#if defined(__wasm__)
extern "C" void _start() { if (probe() != 0) __builtin_trap(); }
#else
int main() { return probe(); }
#endif
