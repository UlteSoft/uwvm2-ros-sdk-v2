# @brief Verify that each platform driver permission gate can deny a handshake.
status, joint = WROS.open("arm")
raise "missing parent capability" unless status == 0
status, reply, length = WROS.call("driver.connect", joint, "", 8)
raise "unapproved driver connection" unless status == 13 && reply.nil? && length == 0
raise "unable to close the local capability" unless WROS.close(joint) == 0
