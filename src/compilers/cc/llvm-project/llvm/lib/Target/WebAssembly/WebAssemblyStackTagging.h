//===- WebAssemblyStackTagging.h - Managed linear stack owners ----*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
#ifndef LLVM_LIB_TARGET_WEBASSEMBLY_WEBASSEMBLYSTACKTAGGING_H
#define LLVM_LIB_TARGET_WEBASSEMBLY_WEBASSEMBLYSTACKTAGGING_H
namespace llvm {
class FunctionPass;
class PassRegistry;
FunctionPass *createWebAssemblyStackTaggingPass();
void initializeWebAssemblyStackTaggingPass(PassRegistry &);
}
#endif
