module Robot

let Policy (version: int) =
    if version = 2 then 0 else 1

let Start () =
    Policy (Wros.Scene.Abi())
