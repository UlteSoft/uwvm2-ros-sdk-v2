"""@brief Compare a Python guest fixture to real ROS 1 genpy and ROS 2 ROSIDL Fast RTPS serialization."""
import argparse
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys


def main():
    """@brief Write the native reference encodings and check the shared guest fixture's fixed byte contract."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("genpy", "genmsg", "geometry-msgs", "ros2", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir()
    sys.path[:0] = [str(args.genpy.resolve()), str(args.genmsg.resolve())]
    from genpy.dynamic import generate_dynamic
    definition = ((args.geometry_msgs / "Twist.msg").read_text() + "\n" + "=" * 80 + "\nMSG: geometry_msgs/Vector3\n" +
                  (args.geometry_msgs / "Vector3.msg").read_text())
    t = generate_dynamic("geometry_msgs/Twist", definition)["geometry_msgs/Twist"]()
    t.linear.x, t.linear.y, t.linear.z = 1., -2., 3.5
    t.angular.x, t.angular.y, t.angular.z = .5, 0., -2.5
    output = io.BytesIO()
    t.serialize(output)
    ros1 = output.getvalue()
    prefix = args.ros2.resolve()
    lib = prefix / "lib"
    program = args.output / "twist"
    subprocess.run(["/usr/bin/c++", "-O3", "-g", "-std=c++17",
        *["-I" + str(p) for p in sorted((prefix / "include").iterdir()) if p.is_dir()],
        Path(__file__).with_name("twist.cpp"), "-L" + str(lib), "-Wl,-rpath-link," + str(lib),
        "-lgeometry_msgs__rosidl_typesupport_fastrtps_cpp", "-lfastcdr", "-o", program], check=True)
    ros2 = subprocess.check_output([program], env=dict(os.environ, LD_LIBRARY_PATH=str(lib)))
    expected = bytes.fromhex("000000000000f03f00000000000000c00000000000000c40"
                             "000000000000e03f000000000000000000000000000004c0")
    if ros1 != expected or ros2 != b"\0\1\0\0" + expected:
        raise SystemExit("native ROS1 / ROS2 Twist encoding differs")
    for name, data in (("ros1", ros1), ("ros2", ros2)):
        (args.output / (name + ".bin")).write_bytes(data)
        print(name, len(data), hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
