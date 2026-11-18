/** @file entry.c
 * @brief Enter a freestanding Flang PROGRAM with the module's own memory.
 * @details Firmware-style programs call ROSv2 through declared imports.
 * Operations requiring Flang-RT must resolve through a matching target
 * library. Link failure preserves the previous published Wasm module.
 */
extern void _QQmain(void);
void _start(void) { _QQmain(); }
