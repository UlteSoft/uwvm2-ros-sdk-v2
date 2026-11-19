' @file GoalStatus.vb
' @brief Interpret ROS 1 actionlib wire statuses using Visual Basic in Wasm.
Public NotInheritable Class GoalStatus
    ''' @brief Check all ten wire values against the client terminal-state mask.
    Public Shared Function Check(abi As Integer) As Integer
        Dim bit As Integer = 1 << (abi And 7)
        Dim visited As Integer = 0
        Dim mask As Integer = 0
        While (visited And bit) = 0
            visited = visited Or bit
            If (bit >= (1 << 2) AndAlso bit <= (1 << 5)) OrElse bit = (1 << 8) OrElse bit = (1 << 9) Then
                mask = mask Or bit
            End If
            bit = If(bit = (1 << 9), 1, bit << 1)
        End While
        Return If(abi = 2 AndAlso mask = 828, 0, 1)
    End Function

    ''' @brief Seed traversal with the operator-granted scene ABI.
    Public Shared Function Start() As Integer
        Return Check(Wros.Scene.Abi())
    End Function
End Class
