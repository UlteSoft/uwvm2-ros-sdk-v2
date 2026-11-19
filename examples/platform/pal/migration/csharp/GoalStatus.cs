/** @file GoalStatus.cs
 * @brief Interpret ROS 1 actionlib wire statuses inside a managed Wasm guest.
 */
public static class GoalStatus
{
    /// @brief Check all ten wire values against the client terminal-state mask.
    public static int Check(int abi)
    {
        int first = abi & 7, state = first, count = 0, mask = 0;
        while (count == 0 || state != first)
        {
            if ((state >= 2 && state <= 5) || state == 8 || state == 9)
                mask |= 1 << state;
            state = state == 9 ? 0 : state + 1;
            count++;
        }
        return abi == 2 && mask == 828 ? 0 : 1;
    }

    /// @brief Seed traversal with the host scene ABI and trap through startup on mismatch.
    public static int Start() => Check(Wros.Scene.Abi());
}
