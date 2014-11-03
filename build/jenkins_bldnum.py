#!/usr/bin/env python

import sys
import json
from argparse import ArgumentParser, FileType

def process(json_file, key):
    data = json.load(json_file)
    json_file.close()
    if key not in data:
        sys.exit(1)
    else:
        print data[key]
        sys.exit(0)

if __name__ == '__main__':
    parser = ArgumentParser(
            description="Simple JSON reader"
            )
    parser.add_argument('json_file', type=FileType('r'))
    parser.add_argument('key', help='Key to lookup in dict')
    args = parser.parse_args()
    process(**vars(args))
