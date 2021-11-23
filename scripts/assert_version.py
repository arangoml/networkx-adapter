# -*- coding: utf-8 -*-
import sys
from packaging.version import Version

if __name__ == "__main__":
    old = Version(sys.argv[1])
    current = Version(sys.argv[2])
    if current > old:
        print("true")
        sys.exit(0)
