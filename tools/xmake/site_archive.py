"""Create a C or C++ archive with the archiver bound to the installed site release."""
import argparse
import os
from pathlib import Path
import sys

sdk = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(sdk / 'install'))
import local_release
from qualification import check_site

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('language', choices=('c', 'cpp'))
    parser.add_argument('-o', '--output', required=True)
    parser.add_argument('objects', nargs='+')
    args = parser.parse_args()
    data = local_release.read_file(sdk / local_release.SITE, 32768)
    check_site(data, sdk, args.language)
    toolchain = local_release.parse_site(data)['toolchain']
    os.execv(sys.executable, [sys.executable, '-I', '-B', str(sdk / 'bin/wrar'),
                              '--toolchain', toolchain, '-o', args.output, '--', *args.objects])
