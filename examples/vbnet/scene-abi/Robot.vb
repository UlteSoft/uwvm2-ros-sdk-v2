Public NotInheritable Class Robot
    Public Shared Function Start() As Integer
        Return Policy(Wros.Scene.Abi())
    End Function

    Public Shared Function Policy(ByVal value As Integer) As Integer
        Return If(value = 2, 0, 1)
    End Function
End Class
