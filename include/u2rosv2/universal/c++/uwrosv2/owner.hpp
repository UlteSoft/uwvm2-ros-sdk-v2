/** @file Exclusive ownership of VM-issued handles, without allocation. */
#pragma once
#include "capability.hpp"
#include "resource.hpp"

namespace uwrosv2 {

class capability_owner {
    capability_handle handle_;
    capability_owner(const capability_owner&) UWROSV2_CPP_NOEXCEPT;
    capability_owner& operator=(const capability_owner&) UWROSV2_CPP_NOEXCEPT;
public:
    capability_owner() UWROSV2_CPP_NOEXCEPT : handle_() {}
    /** Consume a handle obtained from capability::open. */
    explicit capability_owner(capability_handle& handle) UWROSV2_CPP_NOEXCEPT : handle_(handle) { handle.id = 0; }
    ~capability_owner() UWROSV2_CPP_NOEXCEPT { (void)close(); }

    bool empty() const UWROSV2_CPP_NOEXCEPT { return handle_.id == 0; }
    capability_handle get() const UWROSV2_CPP_NOEXCEPT { return handle_; }
    /** Open into an empty owner. Existing ownership and failed opens are preserved. */
    UWROSV2_CPP_NODISCARD uint32_t open(text_view alias) UWROSV2_CPP_NOEXCEPT {
        if (!empty()) return static_cast<uint32_t>(status::conflict);
        const result<capability_handle> opened = capability::open(alias);
        if (opened) handle_ = opened.value;
        return opened.call.status;
    }
    /** Retire the capability once. A refused close retains ownership for retry. */
    UWROSV2_CPP_NODISCARD uint32_t close() UWROSV2_CPP_NOEXCEPT {
        return empty() ? 0 : capability::close(handle_);
    }
    UWROSV2_CPP_NODISCARD capability_handle release() UWROSV2_CPP_NOEXCEPT {
        const capability_handle old = handle_;
        handle_.id = 0;
        return old;
    }
    void swap(capability_owner& other) UWROSV2_CPP_NOEXCEPT {
        const capability_handle old = handle_;
        handle_ = other.handle_;
        other.handle_ = old;
    }
    /** Close the destination first. On failure, both owners retain their handles. */
    UWROSV2_CPP_NODISCARD uint32_t transfer_to(capability_owner& other) UWROSV2_CPP_NOEXCEPT {
        if (this == &other) return 0;
        const uint32_t code = other.close();
        if (!code) swap(other);
        return code;
    }
#if __cplusplus >= 201103L
    capability_owner(capability_owner&& other) noexcept : handle_(other.release()) {}
    capability_owner& operator=(capability_owner&& other) noexcept {
        (void)other.transfer_to(*this);
        return *this;
    }
#endif
};

/** Raw responsibilities returned by resource_owner::release. Close resource using
 *  capability first, then close capability if owns_capability is set. */
struct released_resource {
    capability_handle capability;
    resource_handle resource;
    bool owns_capability;
};

class resource_owner {
    released_resource held_;
    resource_owner(const resource_owner&) UWROSV2_CPP_NOEXCEPT;
    resource_owner& operator=(const resource_owner&) UWROSV2_CPP_NOEXCEPT;
    uint32_t close_resource() UWROSV2_CPP_NOEXCEPT {
        return held_.resource.id ? resource::close(held_.capability, held_.resource) : 0;
    }
public:
    resource_owner() UWROSV2_CPP_NOEXCEPT : held_() {}
    ~resource_owner() UWROSV2_CPP_NOEXCEPT { (void)close(); }
    bool empty() const UWROSV2_CPP_NOEXCEPT { return !held_.resource.id && !held_.owns_capability; }
    resource_handle get() const UWROSV2_CPP_NOEXCEPT { return held_.resource; }
    capability_handle capability() const UWROSV2_CPP_NOEXCEPT { return held_.capability; }

    /** Consume an issued resource, borrowing its grant until the resource is closed. */
    UWROSV2_CPP_NODISCARD uint32_t adopt(capability_handle grant, resource_handle& resource) UWROSV2_CPP_NOEXCEPT {
        if (!empty()) return static_cast<uint32_t>(status::conflict);
        if (!grant.id || !resource.id) return static_cast<uint32_t>(status::bad_handle);
        held_.capability = grant;
        held_.resource = resource;
        resource.id = 0;
        return 0;
    }
    /** Take responsibility for the issuing capability too. Finish other borrows before
     *  retiring this owner. The resource can now outlive the original capability_owner. */
    UWROSV2_CPP_NODISCARD uint32_t take_capability(capability_owner& grant) UWROSV2_CPP_NOEXCEPT {
        if (held_.owns_capability) return static_cast<uint32_t>(status::conflict);
        if (!held_.resource.id || grant.get().id != held_.capability.id)
            return static_cast<uint32_t>(status::bad_handle);
        held_.capability = grant.release();
        held_.owns_capability = true;
        return 0;
    }
    /** Retire resource first, then its optional owned capability. Retry resumes at the
     *  refused operation. Calling close on an empty owner succeeds without a VM call. */
    UWROSV2_CPP_NODISCARD uint32_t close() UWROSV2_CPP_NOEXCEPT {
        const uint32_t code = close_resource();
        if (code) return code;
        if (held_.owns_capability) {
            const uint32_t cap_code = uwrosv2::capability::close(held_.capability);
            if (cap_code) return cap_code;
        }
        held_ = released_resource();
        return 0;
    }
    UWROSV2_CPP_NODISCARD released_resource release() UWROSV2_CPP_NOEXCEPT {
        const released_resource old = held_;
        held_ = released_resource();
        return old;
    }
    /** Restore all remaining cleanup responsibilities from a release, including a
     *  capability whose resource already closed. */
    UWROSV2_CPP_NODISCARD uint32_t adopt(released_resource& released) UWROSV2_CPP_NOEXCEPT {
        if (!empty()) return static_cast<uint32_t>(status::conflict);
        if (!released.capability.id || (!released.resource.id && !released.owns_capability))
            return static_cast<uint32_t>(status::bad_handle);
        held_ = released;
        released = released_resource();
        return 0;
    }
    void swap(resource_owner& other) UWROSV2_CPP_NOEXCEPT {
        const released_resource old = held_;
        held_ = other.held_;
        other.held_ = old;
    }
    UWROSV2_CPP_NODISCARD uint32_t transfer_to(resource_owner& other) UWROSV2_CPP_NOEXCEPT {
        if (this == &other) return 0;
        // A destination that owns our borrowed capability must carry it forward.
        // Retire its old resource before committing either ownership change.
        const bool carry_capability = held_.resource.id && !held_.owns_capability && other.held_.owns_capability &&
                                      held_.capability.id == other.held_.capability.id;
        const uint32_t code = carry_capability ? other.close_resource() : other.close();
        if (code) return code;
        if (carry_capability) {
            held_.owns_capability = true;
            other.held_ = released_resource();
        }
        swap(other);
        return 0;
    }
#if __cplusplus >= 201103L
    resource_owner(resource_owner&& other) noexcept : held_(other.release()) {}
    resource_owner& operator=(resource_owner&& other) noexcept {
        (void)other.transfer_to(*this);
        return *this;
    }
#endif
};
}
