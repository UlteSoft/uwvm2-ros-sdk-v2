# Lua interpreter source

The SDK builds the interpreter from the retained upstream Lua 5.4.9 source distribution. Its SHA-256 is `2335b6c582a52654f94612bf10d2f4672805d05329aa6568b1d8cd9e5c6fb8e6`. The upstream license is reproduced in `LICENSE` and in the archive's `src/lua.h`. [Upstream distribution](https://www.lua.org/ftp/lua-5.4.9.tar.gz)

The Python frontend `bin/wrlua` selects the interpreter sources and configures the embedded libraries at build time. The upstream archive stays intact.
