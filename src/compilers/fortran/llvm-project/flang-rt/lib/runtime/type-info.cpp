//===-- lib/runtime/type-info.cpp -------------------------------*- C++ -*-===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "flang-rt/runtime/type-info.h"
#include "flang-rt/runtime/descriptor.h"
#include "flang-rt/runtime/terminator.h"
#include "flang-rt/runtime/tools.h"
#include <cstdio>

namespace Fortran::runtime::typeInfo {

RT_OFFLOAD_API_GROUP_BEGIN

RT_API_ATTRS common::optional<TypeParameterValue> Value::GetValue(
    const Descriptor *descriptor) const {
  switch (genre_) {
  case Genre::Explicit:
    return value_;
  case Genre::LenParameter:
    if (descriptor) {
      if (const auto *addendum{descriptor->Addendum()}) {
        return addendum->LenParameterValue(value_);
      }
    }
    return common::nullopt;
  default:
    return common::nullopt;
  }
}

RT_API_ATTRS std::size_t Component::GetElementByteSize(
    const Descriptor &instance) const {
  switch (category()) {
  case TypeCategory::Integer:
  case TypeCategory::Unsigned:
  case TypeCategory::Logical:
    return kind_;
  case TypeCategory::Real:
  case TypeCategory::Complex:
    return Descriptor::BytesFor(category(), kind_);
  case TypeCategory::Character:
    if (auto value{characterLen_.GetValue(&instance)}) {
      return kind_ * *value;
    }
    break;
  case TypeCategory::Derived:
    if (const auto *type{derivedType()}) {
      return type->sizeInBytes();
    }
    break;
  }
  return 0;
}

RT_API_ATTRS std::size_t Component::GetElements(
    const Descriptor &instance) const {
  std::size_t elements{1};
  if (int rank{rank_}) {
    if (const Value * boundValues{bounds()}) {
      for (int j{0}; j < rank; ++j) {
        TypeParameterValue lb{
            boundValues[2 * j].GetValue(&instance).value_or(0)};
        TypeParameterValue ub{
            boundValues[2 * j + 1].GetValue(&instance).value_or(0)};
        if (ub >= lb) {
          elements *= ub - lb + 1;
        } else {
          return 0;
        }
      }
    } else {
      return 0;
    }
  }
  return elements;
}

RT_API_ATTRS std::size_t Component::SizeInBytes(
    const Descriptor &instance) const {
  if (genre() == Genre::Data) {
    return GetElementByteSize(instance) * GetElements(instance);
  } else if (category() == TypeCategory::Derived) {
    const DerivedType *type{derivedType()};
    return Descriptor::SizeInBytes(
         rank_, true, type ? type->LenParameters() : 0);
  } else {
    return Descriptor::SizeInBytes(rank_);
  }
}

RT_API_ATTRS void Component::EstablishDescriptor(Descriptor &descriptor,
    const Descriptor &container, Terminator &terminator) const {
  ISO::CFI_attribute_t attribute{static_cast<ISO::CFI_attribute_t>(
      genre_ == Genre::Allocatable   ? CFI_attribute_allocatable
          : genre_ == Genre::Pointer ? CFI_attribute_pointer
                                     : CFI_attribute_other)};
  TypeCategory cat{category()};
  unsigned allocatorIdx{kDefaultAllocator};
  if (memorySpace_ == MemorySpace::Device) {
    allocatorIdx = kDeviceAllocatorPos;
  } else if (memorySpace_ == MemorySpace::Managed) {
    allocatorIdx = kManagedAllocatorPos;
  } else if (memorySpace_ == MemorySpace::Unified) {
    allocatorIdx = kUnifiedAllocatorPos;
  }
  if (cat == TypeCategory::Character) {
    std::size_t lengthInChars{0};
    if (auto length{characterLen_.GetValue(&container)}) {
      lengthInChars = static_cast<std::size_t>(*length);
    } else {
      RUNTIME_CHECK(
          terminator, characterLen_.genre() == Value::Genre::Deferred);
    }
    descriptor.Establish(kind_, lengthInChars, nullptr, rank_, nullptr,
        attribute, false, allocatorIdx);
  } else if (cat == TypeCategory::Derived) {
    if (const DerivedType * type{derivedType()}) {
      descriptor.Establish(
          *type, nullptr, rank_, nullptr, attribute, allocatorIdx);
    } else { // unlimited polymorphic
      descriptor.Establish(TypeCode{TypeCategory::Derived, 0}, 0, nullptr,
          rank_, nullptr, attribute, true, allocatorIdx);
    }
  } else {
    descriptor.Establish(
        cat, kind_, nullptr, rank_, nullptr, attribute, false, allocatorIdx);
  }
  if (rank_ && genre_ != Genre::Allocatable && genre_ != Genre::Pointer) {
    const typeInfo::Value *boundValues{bounds()};
    RUNTIME_CHECK(terminator, boundValues != nullptr);
    auto byteStride{static_cast<SubscriptValue>(descriptor.ElementBytes())};
    for (int j{0}; j < rank_; ++j) {
      auto lb{boundValues++->GetValue(&container)};
      auto ub{boundValues++->GetValue(&container)};
      RUNTIME_CHECK(terminator, lb.has_value() && ub.has_value());
      Dimension &dim{descriptor.GetDimension(j)};
      dim.SetBounds(*lb, *ub);
      dim.SetByteStride(byteStride);
      byteStride *= dim.Extent();
    }
  }
}

RT_API_ATTRS void Component::CreatePointerDescriptor(Descriptor &descriptor,
    const Descriptor &container, Terminator &terminator,
    const SubscriptValue *subscripts) const {
  RUNTIME_CHECK(terminator, genre_ == Genre::Data);
  EstablishDescriptor(descriptor, container, terminator);
  std::size_t offset{static_cast<std::size_t>(offset_)};
  if (subscripts) {
    offset += container.SubscriptsToByteOffset(subscripts);
  }
  descriptor.set_base_addr(container.OffsetElement<char>() + offset);
  descriptor.raw().attribute = CFI_attribute_pointer;
}

RT_API_ATTRS const DerivedType *DerivedType::GetParentType() const {
  if (hasParent_) {
    const Descriptor &compDesc{component()};
    const Component &component{*compDesc.OffsetElement<const Component>()};
    return component.derivedType();
  } else {
    return nullptr;
  }
}

RT_API_ATTRS const Component *DerivedType::FindDataComponent(
    const char *compName, std::size_t compNameLen) const {
  const Descriptor &compDesc{component()};
  std::size_t n{compDesc.Elements()};
  SubscriptValue at[maxRank];
  compDesc.GetLowerBounds(at);
  for (std::size_t j{0}; j < n; ++j, compDesc.IncrementSubscripts(at)) {
    const Component *component{compDesc.Element<Component>(at)};
    INTERNAL_CHECK(component != nullptr);
    const Descriptor &nameDesc{component->name()};
    if (nameDesc.ElementBytes() == compNameLen &&
        Fortran::runtime::memcmp(
            compName, nameDesc.OffsetElement(), compNameLen) == 0) {
      return component;
    }
  }
  const DerivedType *parent{GetParentType()};
  return parent ? parent->FindDataComponent(compName, compNameLen) : nullptr;
}

RT_OFFLOAD_API_GROUP_END

// The guest compute runtime omits FILE-based diagnostic dumps.
} // namespace Fortran::runtime::typeInfo
