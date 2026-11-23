# Replace Clang's generated process entry point while retaining its complete driver and cc1.
function(wros_clang_entry)
  get_target_property(driver_dir clang BINARY_DIR)
  get_target_property(sources clang SOURCES)
  list(REMOVE_ITEM sources "${driver_dir}/clang-driver.cpp" "clang-driver.cpp")
  set_property(TARGET clang PROPERTY SOURCES "${sources}")
  target_sources(clang PRIVATE "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/clang_driver.cpp")
endfunction()
cmake_language(DEFER CALL wros_clang_entry)
