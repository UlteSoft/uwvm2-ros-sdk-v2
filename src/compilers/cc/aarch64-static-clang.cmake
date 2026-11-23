# glibc's small-model GOT loads must fit within the first 32 KiB measured
# from the page containing _GLOBAL_OFFSET_TABLE_. Put the host runtime group
# before the LLVM archives in both statically linked executables.
function(wros_link_aarch64_host_runtime)
  foreach(tool IN ITEMS clang lld)
    if(TARGET ${tool})
      get_target_property(tool_libraries ${tool} LINK_LIBRARIES)
      set_property(TARGET ${tool} PROPERTY LINK_LIBRARIES
        "-Wl,--start-group,-lstdc++,-lm,-lc,-lgcc,-lgcc_eh,--end-group"
        ${tool_libraries})
    endif()
  endforeach()
endfunction()

cmake_language(DEFER CALL wros_link_aarch64_host_runtime)
