# Build and test a platform example

Choose the platform, the class of work and the language under the examples/platform directory. Each leaf contains a standalone xmake project and editable guest sources. For example, examples/platform/unitree/common/c builds two independently runnable Wasm modules. The common module checks the ROS ABI. The sensor module exercises a median filter with a tied measurement and an outlier. Both targets register interpreter and AOT tests.

~~~sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language c --site-profile "$C_SITE" --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT="$PWD/sdk/$SDK_COMMIT/unitree/c/development"
export WROS_VM=/absolute/path/to/uwvm2-ros
cp -r "$UWVM_ROS_SDK_ROOT/examples/platform/unitree/common/c" ./samples
cd samples
xmake f -p wasm-wasip1 -a wasm32 -y
xmake build
xmake test -j1
~~~

Use the **directory** reported by the installer if your prefix differs. Select the language's approved site and profile as described in its guide. A selection downloads example sources for its own platform and language. Run xmake build from the project directory to build all its modules, or name one target. The Wasm binaries are under build. Run xmake test -j1 to run each guest assertion in a separate VM process. A host error, hidden import or guest trap fails the case. The tests in these examples use the read-only permissions declared in the xmake project. Deployment permissions are reviewed separately.

| Directory | What the project demonstrates |
| --- | --- |
| common | A portable computation or ROSv2 call, such as querying the ABI or filtering range data. |
| extension | A deployment-scoped platform policy, exercised at the common authenticated driver boundary. |
| migration | A port of an identified ROS behavior or resource contract. |

## Driver permission exercise

A Linux test fixture opens a private SOCK_SEQPACKET pair, creates a temporary sealed Ed25519 identity and provisions an inert driver session. The guest opens its assigned arm capability and requests driver.connect. In the first run the parent authorizes connection and the platform child is disabled. In the second run the child is enabled while the parent authorizes only disconnection. Both runs require EACCES and an empty peer socket. The fixture checks the session deadline on completion. No actuator is attached. The host fixture uses Python 3 with cryptography. This exercise validates the permission boundary; vendor protocol, physics and hardware-stop tests require separate evidence.

## Source migration

The grid examples implement the unsigned row-major cell index used by Noetic Costmap2D. They check known coordinates against expected cell indices in a real guest. The accompanying project-specific sources identify the algorithm and the applicable input domain. Other migrations use named ROS message and resource fixtures. [ROS Noetic Costmap2D source](https://github.com/ros-planning/navigation/blob/noetic-devel/costmap_2d/include/costmap_2d/costmap_2d.h)

## API source reference

From the full source checkout run doxygen document/source/Doxyfile. The generated C reference contains one entry per operation in share/abi/ros.json. Each entry describes its wire format, ordered request and result fields, applicable resource purpose, address operands and return contract. The output is under .tmp/doxygen/html. [ROSv2 source reference](../source/ros-abi.dox) · [xmake controls](xmake.md)

## Browse examples by platform

The source checkout contains an English and Chinese index under examples/platform for each platform, with links to the available projects and explicit gaps. A selective installation downloads projects for the chosen platform and language. [Browse examples by platform](https://github.com/UlteSoft/uwvm2-ros-sdk-v2/tree/main/examples/platform/README.en.md)
