/** @file Driver.cs
 * @brief Check operator-selected platform driver permissions in a managed Wasm guest.
 */
public static class Driver
{
    /// @brief Return zero only when the host rejects driver connection.
    public static int Check(int status) => status == 13 ? 0 : 1;
    /// @brief Open the configured arm alias and check one bounded connection attempt.
    public static int Start() => Check(Wros.Scene.DriverConnectionStatus("arm"));
}
