"""Derive bounded private capability substitution from the installed ROS wire catalogue."""
import re


def is_capability(name):
    return name == "capability" or name.endswith(("_capability", "_capabilities"))


class ReferenceSchemas:
    def __init__(self, schemas):
        self.schemas = schemas
        self.helpers = {}

    def uses_references(self, fields):
        for name, field in fields:
            while field.startswith(("optional<", "array<")):
                field = field[field.index("<")+1:-1]
            if is_capability(name) or self.uses_references(self.schemas.get(field, {}).get("fields", ())):
                return True
        return False

    def visit(self, name, field, depth=0):
        if field.startswith("optional<") and field.endswith(">"):
            return "if(c.present()){"+self.visit(name,field[9:-1],depth+1)+"}"
        if field.startswith("array<") and field.endswith(">"):
            counter="i"+str(depth)
            return "for(int "+counter+"=c.elements();"+counter+">0 && c.status==0;--"+counter+"){" + self.visit(name,field[6:-1],depth+1)+"}"
        if is_capability(name):
            if field!="u64": raise ValueError("unsupported capability encoding: "+name)
            return "c.bind();"
        if field in ("u64","i64","f64"):
            return "c.skip(8);"
        if field=="bool":
            return "c.present();"
        if field in ("text","bytes"):
            return "c.blob();"
        if not re.fullmatch(r"[a-z][a-z0-9_]*",field) or "fields" not in self.schemas.get(field,{}):
            raise ValueError("unsupported referenced message layout: "+field)
        if field not in self.helpers:
            self.helpers[field]=""
            code=self.walk(self.schemas[field]["fields"])
            self.helpers[field]="private static void layout_"+field+"(CapabilityCursor c){"+code+"}"
        return "layout_"+field+"(c);"

    def walk(self, fields):
        return "\n".join(self.visit(name,field) for name,field in fields)
