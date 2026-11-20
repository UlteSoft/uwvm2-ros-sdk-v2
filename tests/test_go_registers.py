"""@brief Exercise the Go encoder's control-flow and authority invariants."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "language/go"))
from registers import lower


def diamond():
    """@brief Make a scalar diamond whose edge ordinals differ from traversal order."""
    return dict(name="Choose", params=["bool"], result="uint32", entry=0, blocks=[
        dict(id=0, kind="If", control=2, predecessors=0,
             succs=[dict(block=1, index=0), dict(block=2, index=0)], values=[
                 dict(id=1, op="InitMem", type="mem"),
                 dict(id=2, op="Arg", type="bool")]),
        dict(id=1, kind="Plain", predecessors=1, succs=[dict(block=3, index=1)],
             values=[dict(id=3, op="Const32", type="uint32", literal=42)]),
        dict(id=2, kind="Plain", predecessors=1, succs=[dict(block=3, index=0)],
             values=[dict(id=4, op="Const32", type="uint32", literal=17)]),
        dict(id=3, kind="Ret", control=6, predecessors=2, values=[
            dict(id=5, op="Phi", type="uint32", args=[4, 3]),
            dict(id=6, op="MakeResult", type="uint32,mem", args=[5, 1])]),
    ])


class GoRegisters(unittest.TestCase):
    """@brief Ensure each return and phi uses its actual scalar inputs."""

    def test_edge_order(self):
        self.assertEqual(lower(diamond())[0], b"\x60\x01\x7f\x01\x7f")

    def test_phi_operand_must_be_available_on_the_selected_edge(self):
        graph = diamond()
        graph["blocks"][3]["values"][0]["args"].reverse()
        with self.assertRaisesRegex(ValueError, "unavailable on its predecessor edge"):
            lower(graph)

    def test_normal_operands_must_dominate_their_use(self):
        graph = diamond()
        graph["blocks"][3]["values"].insert(1, dict(id=7, op="Add32", type="uint32", args=[3, 5]))
        with self.assertRaisesRegex(ValueError, "does not dominate"):
            lower(graph)

    def test_return_cannot_substitute_another_memory_token(self):
        graph = diamond()
        graph["blocks"][3]["values"][1]["args"][1] = 4
        with self.assertRaisesRegex(ValueError, "changes the memory token"):
            lower(graph)

    def test_division_requires_nonzero_in_operand_width(self):
        for divisor in (dict(op="Arg", type="uint32"),
                        dict(op="Const32", type="uint32", literal=0),
                        dict(op="Const32", type="uint32", literal=1 << 32)):
            graph = dict(name="Divide", params=["uint32", "uint32"], result="uint32", entry=0,
                         blocks=[dict(id=0, kind="Ret", control=5, predecessors=0, values=[
                             dict(id=1, op="InitMem", type="mem"),
                             dict(id=2, op="Arg", type="uint32"),
                             dict(id=3, **divisor),
                             dict(id=4, op="Div32u", type="uint32", literal=1, args=[2, 3]),
                             dict(id=5, op="MakeResult", type="uint32,mem", args=[4, 1]),
                         ])])
            with self.subTest(divisor=divisor), self.assertRaisesRegex(ValueError, "divisor proven nonzero"):
                lower(graph)

    def test_branch_proof_applies_to_only_the_selected_edge(self):
        graph = dict(name="Divide", params=["uint32", "uint32"], result="uint32", entry=0, blocks=[
            dict(id=0, kind="If", control=5, predecessors=0,
                 succs=[dict(block=1, index=0), dict(block=2, index=0)], values=[
                     dict(id=1, op="InitMem", type="mem"),
                     dict(id=2, op="Arg", type="uint32"),
                     dict(id=3, op="Arg", type="uint32", index=1),
                     dict(id=4, op="Const32", type="uint32"),
                     dict(id=5, op="Eq32", type="bool", args=[4, 3]),
                 ]),
            dict(id=1, kind="Ret", control=6, predecessors=1, values=[
                dict(id=6, op="MakeResult", type="uint32,mem", args=[2, 1]),
            ]),
            dict(id=2, kind="Ret", control=8, predecessors=1, values=[
                dict(id=7, op="Div32u", type="uint32", args=[2, 3]),
                dict(id=8, op="MakeResult", type="uint32,mem", args=[7, 1]),
            ]),
        ])
        self.assertEqual(lower(graph)[0], b"\x60\x02\x7f\x7f\x01\x7f")
        graph["blocks"][0]["succs"].reverse()
        with self.assertRaisesRegex(ValueError, "divisor proven nonzero"):
            lower(graph)
        graph["blocks"][0]["succs"] = [dict(block=2, index=0), dict(block=2, index=1)]
        graph["blocks"].pop(1)
        graph["blocks"][1]["predecessors"] = 2
        with self.assertRaisesRegex(ValueError, "divisor proven nonzero"):
            lower(graph)
        graph["blocks"][1]["values"].insert(0, dict(id=9, op="Phi", type="uint32", args=[2, 3]))
        graph["blocks"][1]["values"][1]["args"][1] = 9
        with self.assertRaisesRegex(ValueError, "divisor proven nonzero"):
            lower(graph)
        graph["blocks"][0]["values"].append(dict(id=10, op="Const32", type="uint32", literal=1))
        graph["blocks"][1]["values"][0]["args"][0] = 10
        self.assertEqual(lower(graph)[0], b"\x60\x02\x7f\x7f\x01\x7f")

    def test_duplicate_predecessor_ordinal(self):
        graph = diamond()
        graph["blocks"][1]["succs"][0]["index"] = 0
        with self.assertRaisesRegex(ValueError, "duplicate Go predecessor"):
            lower(graph)

    def test_cycle(self):
        graph = diamond()
        loop = dict(block=2, index=1)
        graph["blocks"][2].update(predecessors=2, succs=[loop])
        graph["blocks"][1]["succs"][0]["index"] = 0
        graph["blocks"][3]["predecessors"] = 1
        with self.assertRaisesRegex(ValueError, "cycle"):
            lower(graph)
