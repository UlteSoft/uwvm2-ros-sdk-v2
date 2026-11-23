"""Generate the public Java readers for the pinned ABB ROS 1 observation interfaces."""
from collections import defaultdict
import html
import textwrap

from generate_ros1 import PUBLIC, license_notice, minimum_sizes
from ros1_schema import fingerprints, load


DESTINATION = PUBLIC / "java/src/u2rosv2/abb/ros1"
DOMAINS = {
    "std_msgs": ("StdMsgs", "Sequence number, timestamp and reference frame of a ROS 1 report.",
                 {"Header"}),
    "abb_egm_msgs": ("Egm", "Externally Guided Motion channel feedback and stamped channel reports.",
                     {"EGMChannelState", "EGMState"}),
    "abb_rapid_msgs": ("Rapid", "RAPID Cartesian position, quaternion orientation and coordinate transformation.",
                       {"Pos", "Orient", "Pose"}),
    "abb_rapid_sm_addin_msgs": (
        "StateMachine", "RobotWare StateMachine Add-In state and the reported EGM action of each RAPID task.",
        {"RuntimeState", "StateMachineState"}),
    "abb_robot_msgs": (
        "Robot", "Controller, RAPID task and mechanical-unit status and the GetRAPIDNum service bodies.",
        {"SystemState", "RAPIDTaskState", "MechanicalUnitState", "RAPIDSymbolPath",
         "GetRAPIDNumRequest", "GetRAPIDNumResponse"}),
}
PRIMITIVES = {
    "bool": ("boolean", "bool"), "uint8": ("int", "uint8"), "uint16": ("int", "uint16"),
    "uint32": ("long", "uint32"), "float32": ("float", "float32"), "float64": ("double", "float64"),
    "time": ("RosTime", "time"), "string": ("byte[]", "stringBytes"),
}


def name(field):
    first, *rest = field.split("_")
    return first + "".join(word.capitalize() for word in rest)


def java_type(type_name, domain):
    if type_name in PRIMITIVES:
        return PRIMITIVES[type_name][0]
    package, cls = type_name.split("/")
    if cls not in DOMAINS[package][2]:
        raise ValueError(f"missing Java reader for {type_name}")
    return cls if package == domain else DOMAINS[package][0] + "." + cls


def doc(text, indent):
    paragraphs = []
    for paragraph in text.split("\n\n"):
        paragraphs.append(textwrap.wrap(html.escape(paragraph, quote=False), width=96 - len(indent),
                                        break_long_words=False, break_on_hyphens=False))
    lines = []
    for paragraph in paragraphs:
        if lines:
            lines.append("<p>")
        lines.extend(paragraph)
    if len(lines) == 1:
        return [f"{indent}/** {lines[0]} */"]
    return [indent + "/**", *[indent + " * " + line for line in lines], indent + " */"]


def record_source(record, hashes, minimum):
    cls = record.name
    identity = record.package + "/" + (record.service or cls)
    role = " message." if not record.service else (
        " request body." if cls.endswith("Request") else " response body after the transport success byte.")
    lines = doc(identity + role + "\n\n" + record.description, "    ")
    lines += [f"    public static final class {cls} {{",
              "        /** ROS 1 connection-header datatype. */",
              f'        public static final String TYPE = "{identity}";',
              "        /** ROS 1 connection-header MD5 of the message or complete service. */",
              f'        public static final String MD5 = "{hashes[identity]}";',
              "        /** Encoded byte count with empty strings and sequences. */",
              f"        public static final int MIN_BYTES = {minimum[record.qualified]};", ""]
    for constant in record.constants:
        if constant.type != "uint8":
            raise ValueError("unexpected observation constant " + constant.name)
        lines.extend(doc(constant.description + " " + constant.name + ".", "        "))
        lines.extend([f"        public static final int {constant.name} = {constant.value};", ""])
    for field in record.fields:
        typ = java_type(field.type, record.package) + ("[]" if field.array else "")
        desc = f"ROS field {field.name}. " + field.description
        if field.type == "string":
            desc += " Contains the original string bytes, including embedded NULs."
        lines.extend(doc(desc, "        "))
        lines += [f"        public final {typ} {name(field.name)};", ""]

    lines.append(f"        {cls}(Wire wire) {{")
    for field in record.fields:
        member = name(field.name)
        typ = java_type(field.type, record.package)
        if field.array:
            if field.type in PRIMITIVES or minimum[field.type] == 0:
                raise ValueError(f"unexpected sequence element {field.type}")
            lines += [f"            {member} = new {typ}[wire.count({typ}.MIN_BYTES)];",
                      f"            for (int i = 0; i < {member}.length && wire.valid(); ++i) {{",
                      f"                {member}[i] = new {typ}(wire);", "            }"]
        else:
            value = (f"wire.{PRIMITIVES[field.type][1]}()" if field.type in PRIMITIVES
                     else f"new {typ}(wire)")
            lines.append(f"            {member} = {value};")
    lines += ["        }", "",
              "        /**",
              "         * Reads one complete ROS 1 body and copies strings and arrays into the result.",
              "         * @param data bytes beginning with the first field",
              "         * @return decoded fields, or null for absent, malformed, truncated or trailing data",
              "         */",
              f"        public static {cls} decode(byte[] data) {{",
              "            return decode(data, 0, data == null ? 0 : data.length);", "        }", "",
              "        /**",
              "         * Reads exactly the body contained in a slice of a transport buffer.",
              "         * @param data buffer containing the serialized fields",
              "         * @param offset byte index of the first field",
              "         * @param length number of body bytes",
              "         * @return decoded fields, or null for an invalid slice or body",
              "         */",
              f"        public static {cls} decode(byte[] data, int offset, int length) {{",
              "            Wire wire = new Wire(data, offset, length);",
              "            if (!wire.require(MIN_BYTES)) return null;",
              f"            {cls} value = new {cls}(wire);",
              "            return wire.finished() ? value : null;", "        }", "    }", ""]
    return lines


def main():
    records = load()
    hashes, minimum = fingerprints(records), minimum_sizes(records)
    groups = defaultdict(list)
    for record in records:
        if record.name in DOMAINS[record.package][2]:
            groups[record.package].append(record)
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for domain, (cls, summary, names) in DOMAINS.items():
        if names != {record.name for record in groups[domain]}:
            raise ValueError("incomplete upstream domain " + domain)
        lines = ["// Generated by src/platform/abb/generate_java.py from the pinned ROS 1 definitions.",
                 license_notice(), "", "package u2rosv2.abb.ros1;", "", *doc(summary, ""),
                 f"public final class {cls} {{", f"    private {cls}() {{}}", ""]
        for record in groups[domain]:
            lines += record_source(record, hashes, minimum)
        data = "\n".join([*lines[:-1], "}", ""])
        path = DESTINATION / (cls + ".java")
        if not path.is_file() or path.read_text() != data:
            path.write_text(data)


if __name__ == "__main__":
    main()
