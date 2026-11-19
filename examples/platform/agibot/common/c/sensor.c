/** @file sensor.c
 * @brief Validate a range sample window using fixed-point millimetres.
 */
static unsigned median3(unsigned a, unsigned b, unsigned c) {
    if (a > b) { unsigned tmp = a; a = b; b = tmp; }
    return c < a ? a : (c < b ? c : b);
}
/** @brief Fail the guest test on an incorrect median for an outlier or a tied reading. */
void _start(void) {
    if (median3(407, 399, 2000) != 407 || median3(300, 2000, 300) != 300) __builtin_trap();
}
