/* The Wasm VM invokes this entry point for a standalone Nim application. */
void NimMain(void);
void _start(void) { NimMain(); }
