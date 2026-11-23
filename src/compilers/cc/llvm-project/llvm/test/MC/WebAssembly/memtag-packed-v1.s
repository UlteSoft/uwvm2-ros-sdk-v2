# RUN: llvm-mc -triple=wasm32-unknown-unknown -show-encoding %s | FileCheck %s
# RUN: llvm-mc -triple=wasm64-unknown-unknown -show-encoding %s | FileCheck %s
# RUN: llvm-mc -triple=wasm32-unknown-unknown -filetype=obj %s -o %t.o
# RUN: llvm-objdump -d %t.o | FileCheck %s --check-prefix=DIS
# RUN: llvm-mc -triple=wasm64-unknown-unknown -filetype=obj %s -o %t64.o
# RUN: llvm-objdump -d %t64.o | FileCheck %s --check-prefix=DIS

# This is a wire-format fixture, not an executable program. Unreachable makes
# the stack polymorphic, so every operation's own bytes can be inspected.
# Canonical word 0x010100XX is XX|0x80, 0x80, 0x84, 0x08; memidx remains u32.
test:
  .functype test () -> ()
  unreachable
  memtag.status 0
# CHECK: memtag.status 0{{.*}}encoding: [0xff,0xa0,0x80,0x84,0x08,0x00]
# DIS: memtag.status 0
  drop
  memtag.extract 0
# CHECK: memtag.extract 0{{.*}}encoding: [0xff,0xa1,0x80,0x84,0x08,0x00]
# DIS: memtag.extract 0
  drop
  memtag.insert 0
# CHECK: memtag.insert 0{{.*}}encoding: [0xff,0xa2,0x80,0x84,0x08,0x00]
# DIS: memtag.insert 0
  drop
  memtag.tagbits 0
# CHECK: memtag.tagbits 0{{.*}}encoding: [0xff,0xa3,0x80,0x84,0x08,0x00]
# DIS: memtag.tagbits 0
  drop
  memtag.startbit 0
# CHECK: memtag.startbit 0{{.*}}encoding: [0xff,0xa4,0x80,0x84,0x08,0x00]
# DIS: memtag.startbit 0
  drop
  memtag.copy 0
# CHECK: memtag.copy 0{{.*}}encoding: [0xff,0xa5,0x80,0x84,0x08,0x00]
# DIS: memtag.copy 0
  drop
  memtag.sub 0
# CHECK: memtag.sub 0{{.*}}encoding: [0xff,0xa6,0x80,0x84,0x08,0x00]
# DIS: memtag.sub 0
  drop
  memtag.load 0
# CHECK: memtag.load 0{{.*}}encoding: [0xff,0xa7,0x80,0x84,0x08,0x00]
# DIS: memtag.load 0
  drop
  memtag.untag 0
# CHECK: memtag.untag 0{{.*}}encoding: [0xff,0xa8,0x80,0x84,0x08,0x00]
# DIS: memtag.untag 0
  drop
  memtag.untagstore 0
# CHECK: memtag.untagstore 0{{.*}}encoding: [0xff,0xa9,0x80,0x84,0x08,0x00]
# DIS: memtag.untagstore 0
  drop
  memtag.untagstorez 0
# CHECK: memtag.untagstorez 0{{.*}}encoding: [0xff,0xaa,0x80,0x84,0x08,0x00]
# DIS: memtag.untagstorez 0
  drop
  memtag.store 0
# CHECK: memtag.store 0{{.*}}encoding: [0xff,0xab,0x80,0x84,0x08,0x00]
# DIS: memtag.store 0
  memtag.storez 0
# CHECK: memtag.storez 0{{.*}}encoding: [0xff,0xac,0x80,0x84,0x08,0x00]
# DIS: memtag.storez 0
  memtag.random 0
# CHECK: memtag.random 0{{.*}}encoding: [0xff,0xad,0x80,0x84,0x08,0x00]
# DIS: memtag.random 0
  drop
  memtag.randomstore 0
# CHECK: memtag.randomstore 0{{.*}}encoding: [0xff,0xae,0x80,0x84,0x08,0x00]
# DIS: memtag.randomstore 0
  drop
  memtag.randomstorez 0
# CHECK: memtag.randomstorez 0{{.*}}encoding: [0xff,0xaf,0x80,0x84,0x08,0x00]
# DIS: memtag.randomstorez 0
  drop
  memtag.hint 0
# CHECK: memtag.hint 0{{.*}}encoding: [0xff,0xb6,0x80,0x84,0x08,0x00]
# DIS: memtag.hint 0
  drop
  memtag.hintstore 0
# CHECK: memtag.hintstore 0{{.*}}encoding: [0xff,0xb7,0x80,0x84,0x08,0x00]
# DIS: memtag.hintstore 0
  drop
  memtag.hintstorez 0
# CHECK: memtag.hintstorez 0{{.*}}encoding: [0xff,0xb8,0x80,0x84,0x08,0x00]
# DIS: memtag.hintstorez 0
  drop
  memtag.status 300
# CHECK: memtag.status 300{{.*}}encoding: [0xff,0xa0,0x80,0x84,0x08,0xac,0x02]
# DIS: memtag.status 300
  drop
  memtag.status 4294967295
# CHECK: memtag.status 4294967295{{.*}}encoding: [0xff,0xa0,0x80,0x84,0x08,0xff,0xff,0xff,0xff,0x0f]
# DIS: memtag.status 4294967295
  drop
  end_function
