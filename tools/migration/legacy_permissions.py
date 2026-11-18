"""Review legacy ROS grant arguments before migrating their authority to ROSv2.

Input is a JSON argument vector containing full ROS1/ROS2 grant, set, target
and membership options. Nothing is executed. A paired observer always needs a
manual migration. An empty list of findings authorizes no operation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

OPTION = re.compile(r"--(ros[12])-(global|single|group)-(grant|set|enable|disable|create|add-module)\Z")
IDENTIFIER = re.compile(r"[A-Za-z0-9_.-]{1,255}\Z")
PAIRS = {"service.available": "service-source-alias", "event.observe": "event-source-alias"}
QOS = ("qos.reliability", "qos.durability", "qos.history", "qos.depth", "qos.deadline",
       "qos.lifespan", "qos.liveliness", "qos.liveliness-lease-duration")
EVENTS = ("topic-message", "service-request", "service-response", "action-feedback", "action-result",
          "resource-error", "resource-closed")
PAYLOAD = {"topic.subscribe": "topic-message", "service.advertise": "service-request",
           "service.call": "service-response", "action.receive-feedback": "action-feedback",
           "action.receive-result": "action-result", "action.advertise": "service-request",
           "param.subscribe-events": "topic-message"}
MAX_INPUT = 1024 * 1024


def identifier(value):
    return value not in (".", "..") and IDENTIFIER.fullmatch(value) is not None


def review(arguments):
    if not isinstance(arguments, list) or len(arguments) > 32768 or any(
            not isinstance(v, str) or not v or len(v) > 4096 or "\0" in v for v in arguments):
        raise ValueError("expected a bounded JSON array of nonempty argument strings")
    grants = {}
    i = 0
    while i < len(arguments):
        at = i
        match = OPTION.fullmatch(arguments[i])
        if not match:
            raise ValueError(f"unsupported policy option at argument {at}")
        backend, scope, op = match.groups()
        if (op == "create" and scope == "global") or (op == "add-module" and scope != "group"):
            raise ValueError(f"invalid target operation at argument {at}")
        count = (scope != "global") + {"grant": 5, "set": 3, "add-module": 1}.get(op, 0)
        values = arguments[i + 1:i + 1 + count]
        if len(values) != count or any(x.startswith("--") for x in values):
            raise ValueError(f"missing policy argument after argument {at}")
        i += 1 + count
        target = values.pop(0) if scope != "global" else None
        if target is not None and not identifier(target):
            raise ValueError(f"invalid target name at argument {at}")
        if op == "add-module" and not identifier(values[0]):
            raise ValueError(f"invalid module name at argument {at}")
        if op not in ("grant", "set"):
            continue
        alias, *rest = values
        if not identifier(alias):
            raise ValueError(f"invalid capability alias at argument {at}")
        key = backend, scope, target, alias
        if op == "grant":
            if key in grants:
                raise ValueError(f"duplicate capability declaration at argument {at}")
            action, resource, ros_type, identity = rest
            grants[key] = dict(index=at, action=action, resource=resource, ros_type=ros_type,
                               identity=identity, fields={})
        else:
            if key not in grants:
                raise ValueError(f"setting precedes its exact capability declaration at argument {at}")
            field, value = rest
            if field in grants[key]["fields"]:
                raise ValueError(f"duplicate capability field at argument {at}")
            grants[key]["fields"][field] = value

    findings = []
    for (backend, scope, target, alias), grant in grants.items():
        fields = grant["fields"]
        expected = PAIRS.get(grant["action"])
        for field in PAIRS.values():
            if expected != field and field not in fields:
                continue
            source_alias = fields.get(field)
            if source_alias is not None and not identifier(source_alias):
                raise ValueError(f"invalid paired source identifier for grant at argument {grant['index']}")
            source = grants.get((backend, scope, target, source_alias))
            reasons = []
            if expected != field:
                reasons.append("field-on-wrong-operation")
            if source_alias is None:
                reasons.append("missing-source-alias")
            elif source_alias == alias:
                reasons.append("source-is-observer")
            elif not source:
                reasons.append("missing-source-in-same-backend-and-target")
            else:
                if source["resource"] != grant["resource"]:
                    reasons.append("resource-mismatch")
                if field == "service-source-alias":
                    if source["action"] != "service.call":
                        reasons.append("source-is-not-service-call")
                    if (source["ros_type"], source["identity"]) != (grant["ros_type"], grant["identity"]):
                        reasons.append("service-type-or-identity-mismatch")
                    if source["fields"].get("adapter-codec-identity") != fields.get("adapter-codec-identity"):
                        reasons.append("codec-identity-mismatch")
                    if backend == "ros2":
                        for qos in QOS:
                            if qos == "qos.depth" and fields.get("qos.history") == "keep-all":
                                continue
                            if qos not in fields or fields[qos] != source["fields"].get(qos):
                                reasons.append("missing-or-mismatched-" + qos)
                else:
                    if source["action"] == "event.observe":
                        reasons.append("observer-cannot-be-event-source")
                    events = fields.get("event-kinds", "").split(",")
                    if [e for e in EVENTS if e in events] != events:
                        reasons.append("missing-or-invalid-ordered-event-kinds")
                    elif set(events) - {"resource-error", "resource-closed", PAYLOAD.get(source["action"])}:
                        reasons.append("event-payload-exceeds-source-operation")
            reasons.append("independent-service-query-and-call-authority-required" if field == "service-source-alias"
                           else "independent-event-observer-and-source-authority-required")
            findings.append(dict(argument=grant["index"], backend=backend, scope=scope, target=target,
                                 observer=alias, field=field, source=source_alias, reasons=reasons))
    return dict(result="manual-review-required" if findings else "no-paired-observer-declarations",
                examined_declarations=len(grants), findings=findings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("argv", type=Path, help="JSON array of legacy policy arguments in original order")
    args = parser.parse_args()
    try:
        with args.argv.open("rb") as stream:
            data = stream.read(MAX_INPUT + 1)
        if len(data) > MAX_INPUT:
            raise ValueError("policy review input exceeds 1 MiB")
        result = review(json.loads(data.decode("utf-8")))
    except (OSError, ValueError, RecursionError) as error:
        print(f"legacy permission review refused: {error}", file=sys.stderr)
        return 3
    result["input_sha256"] = hashlib.sha256(data).hexdigest()
    print(json.dumps(result, indent=2))
    return 2 if result["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
