## @brief Check the platform child and its parent driver grant using the SDK bindings.
import wros_scene
var aliasName = ['a', 'r', 'm']
var handle: uint64
var reply = 0x4321'u64
var written = 0x1234'u64
doAssert wr_capability_open(0, wrAddress(addr aliasName[0]), 3, wrAddress(addr handle)) == 0
doAssert wr_driver_connect(handle, 0, 0, 0, wrAddress(addr reply), 8, wrAddress(addr written)) == 13
doAssert reply == 0x4321 and written == 0x1234
doAssert wr_capability_close(handle) == 0
