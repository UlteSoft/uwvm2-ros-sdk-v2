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

## Browse projects by platform

Browse all platforms in the source checkout. A selective installation includes projects for the selected platform and language.

[abb](../../examples/platform/abb/README.en.md) · [agibot](../../examples/platform/agibot/README.en.md) · [agilex](../../examples/platform/agilex/README.en.md) · [booster](../../examples/platform/booster/README.en.md) · [boston_dynamics](../../examples/platform/boston_dynamics/README.en.md) · [clearpath](../../examples/platform/clearpath/README.en.md) · [deep_robotics](../../examples/platform/deep_robotics/README.en.md) · [dobot](../../examples/platform/dobot/README.en.md) · [doosan](../../examples/platform/doosan/README.en.md) · [elephant](../../examples/platform/elephant/README.en.md) · [fanuc](../../examples/platform/fanuc/README.en.md) · [flexiv](../../examples/platform/flexiv/README.en.md) · [fourier](../../examples/platform/fourier/README.en.md) · [franka](../../examples/platform/franka/README.en.md) · [hello_robot](../../examples/platform/hello_robot/README.en.md) · [kinova](../../examples/platform/kinova/README.en.md) · [kuka](../../examples/platform/kuka/README.en.md) · [leju](../../examples/platform/leju/README.en.md) · [limx](../../examples/platform/limx/README.en.md) · [nvidia](../../examples/platform/nvidia/README.en.md) · [nvidia-groot](../../examples/platform/nvidia-groot/README.en.md) · [nvidia-isaac-ros](../../examples/platform/nvidia-isaac-ros/README.en.md) · [nvidia-isaac-sim](../../examples/platform/nvidia-isaac-sim/README.en.md) · [pal](../../examples/platform/pal/README.en.md) · [realman](../../examples/platform/realman/README.en.md) · [robotis](../../examples/platform/robotis/README.en.md) · [trossen](../../examples/platform/trossen/README.en.md) · [ubtech](../../examples/platform/ubtech/README.en.md) · [ufactory](../../examples/platform/ufactory/README.en.md) · [unitree](../../examples/platform/unitree/README.en.md) · [universal_robots](../../examples/platform/universal_robots/README.en.md) · [yaskawa](../../examples/platform/yaskawa/README.en.md)
