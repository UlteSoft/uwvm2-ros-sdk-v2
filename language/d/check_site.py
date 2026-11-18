"""Verify the selected D site in the freshly installed SDK tree."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from release import authorized, canon, local_release

if __name__ == "__main__":
    print(canon(authorized(local_release.parse_site(sys.stdin.buffer.read(32769)))))
