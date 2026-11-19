# Embedded mruby source

This directory contains the official mruby 4.0.0 source archive
([upstream tag](https://github.com/mruby/mruby/releases/tag/4.0.0),
commit 831da26b9021de0369d17b71b5667e2941a1a32d) and its MIT license.

The SDK builds the core interpreter and parser in the guest. WROS keeps GC
objects and parser allocations in independent tagged allocations and uses the
parser's heap stack. Application source and the upstream Ruby core classes
are loaded in the VM.
