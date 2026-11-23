# GNUmakefile supplies the release's complete list of LLVM, Clang and LLD targets.
.PHONY: sdk-frontend-llvm
sdk-frontend-llvm: $(LLVM_BUILDDIR)/build.ninja
	ninja -C "$(LLVM_BUILDDIR)" -j "$(SDK_JOBS)" $(NINJA_BUILD_TARGETS)
