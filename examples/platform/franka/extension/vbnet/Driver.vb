' @file Driver.vb
' @brief Check the selected platform driver permissions with the managed Wasm binding.
Public NotInheritable Class Driver
    ''' @brief Require the stable ROSv2 permission-denied result.
    Public Shared Function Check(status As Integer) As Integer
        Return If(status = 13, 0, 1)
    End Function
    ''' @brief Open the configured arm alias and check one bounded connection attempt.
    Public Shared Function Start() As Integer
        Return Check(Wros.Scene.DriverConnectionStatus("arm"))
    End Function
End Class
