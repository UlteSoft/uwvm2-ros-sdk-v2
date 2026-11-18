package wros.scene;
import org.teavm.interop.Import;
/** Read the ROSv2 ABI identifier of the current VM scene. */
public final class Scene {
    private Scene() {}
    @Import(name="wr_abi") public static native int abi();
}
