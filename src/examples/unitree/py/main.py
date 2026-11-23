"""Compare all Go2/HG LowState fields against four independent Fast-CDR transfers."""
from unitree_go.msg import LowState as Go2State
from unitree_hg.msg import LowState as HGState
from unitree_api.msg import Response
from uwrosv2 import Buffer
from uwrosv2.capability import wr_abi, wr_capability_open
from uwrosv2.status import DENIED
from vectors import CDR

assert wr_abi() == 2
alias = Buffer(b"ungranted")
slot = Buffer(b"abcdefgh")
assert wr_capability_open(0, alias.address, len(alias.view), slot.address) == DENIED
assert bytes(slot.view) == b"abcdefgh"

for family, state in (("go2", Go2State), ("hg", HGState)):
    little, big = CDR[family + "-le"], CDR[family + "-be"]
    for source in (little, big):
        sample = state.from_cdr(source)
        assert sample.to_cdr("little") == little
        assert sample.to_cdr("big") == big
    print(f"{family} LowState: {len(little)} bytes, little and big endian")

response = Response(data="sensor ready", binary=[-128, 0, 127])
assert Response.from_cdr(response.to_cdr("big")).binary == response.binary
print("CPython Unitree Fast-CDR and denied capability verified")
