"""Check a signed standalone Zig site during selective SDK installation."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release import authorized, local_release, qualification

if __name__ == "__main__":
    row, _, _, _ = authorized(local_release.parse_site(sys.stdin.buffer.read(32769)))
    print(qualification.canonical(row))
