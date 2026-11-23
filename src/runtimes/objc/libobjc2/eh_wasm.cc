// GNUstep 2 exceptions for the SDK's LLVM WebAssembly / libc++abi target.
#include <cxxabi.h>
#include <typeinfo>
#include "objc/runtime.h"
#include "objc/hooks.h"
#include "objc/objc-exception.h"

namespace __cxxabiv1 {
class __shim_type_info;
}

namespace gnustep::libobjc {

// LLVM's libc++abi __shim_type_info has two reserved virtual slots between
// the std::type_info destructors and can_catch. Wasm checks the complete
// indirect-call signature, including the number of arguments.
class __objc_type_info : public std::type_info {
protected:
	explicit __objc_type_info(const char *name) : std::type_info(name) {}
	virtual void noop1() const {}
	virtual void noop2() const {}
	virtual bool can_catch(const __cxxabiv1::__shim_type_info *, void *&) const = 0;
};

class __objc_id_type_info final : public __objc_type_info {
public:
	__objc_id_type_info() : __objc_type_info("@id") {}
	bool can_catch(const __cxxabiv1::__shim_type_info *type, void *&adjusted) const override;
};

// Clang emits a two-word descriptor with this vtable and the class name at
// each typed handler. The vtable name is part of the GNUstep compiler ABI.
class __objc_class_type_info final : public __objc_type_info {
public:
	bool can_catch(const __cxxabiv1::__shim_type_info *type, void *&adjusted) const override;
};

} // namespace gnustep::libobjc

extern "C" {
OBJC_PUBLIC gnustep::libobjc::__objc_id_type_info __objc_id_type_info;
}

bool gnustep::libobjc::__objc_id_type_info::can_catch(
		const __cxxabiv1::__shim_type_info *type, void *&adjusted) const
{
	if (static_cast<const void *>(type) != &::__objc_id_type_info)
		return false;
	adjusted = *static_cast<id *>(adjusted);
	return true;
}

bool gnustep::libobjc::__objc_class_type_info::can_catch(
		const __cxxabiv1::__shim_type_info *type, void *&adjusted) const
{
	if (static_cast<const void *>(type) != &::__objc_id_type_info)
		return false;
	id object = *static_cast<id *>(adjusted);
	Class wanted = reinterpret_cast<Class>(objc_getClass(name()));
	for (Class cls = object_getClass(object); cls; cls = class_getSuperclass(cls)) {
		if (cls == wanted) {
			adjusted = object;
			return true;
		}
	}
	return false;
}

extern "C" void objc_exception_throw(id object)
{
	// The GNUstep manual-reference-counting ABI leaves the object's lifetime
	// with its owner. libc++abi owns and frees the copy of the pointer.
	id *payload = static_cast<id *>(__cxxabiv1::__cxa_allocate_exception(sizeof(id)));
	*payload = object;
	__cxxabiv1::__cxa_throw(payload, &__objc_id_type_info, nullptr);
}

extern "C" objc_uncaught_exception_handler objc_setUncaughtExceptionHandler(
		objc_uncaught_exception_handler handler)
{
	return __atomic_exchange_n(&_objc_unexpected_exception, handler, __ATOMIC_SEQ_CST);
}
