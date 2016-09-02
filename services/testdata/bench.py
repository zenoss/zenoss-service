#!/usr/bin/env python

# Copyright 2016 The Serviced Authors.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
import distutils.dir_util
import os
import sys
from subprocess import call

log = logging.getLogger("bench.py")


def fail(msg):
    """
    log message and exit
    """
    log.critical(msg)
    sys.exit(1)


def args():
    """
    --all (some subset that is useful for someone)
    --packages (maybe positional?)
    """
    parser = argparse.ArgumentParser(
        description="generate test services for serviced")

    parser.add_argument("-t", "--template", action="store_true",
                        help="generate template")
    parser.add_argument("-z", "--zendev", action="store_true",
                        help="generate template for zendev")

    parser.add_argument("--model", help="model path. Defaults to "
                                        "./model/Zenoss.core.test",
                        default="./model/Zenoss.core.test")
    parser.add_argument("--out", help="output path. Defaults to ./out",
                        default="./out")
    parser.add_argument("--collectorpath",
                        help="relative path of collector top-level"
                             " (from model path). Defaults to "
                             "Zenoss/Collection/localhost",
                        default="Zenoss/Collection/localhost")
    parser.add_argument("collectors",
                        help="number of collector instances to create",
                        type=int, default=1)

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="verbose logging")

    return parser.parse_args()


def main(opts):
    """
    The main routine
    """
    logging.basicConfig(level=logging.DEBUG if opts.verbose else logging.INFO)

    if not os.path.isdir(opts.model):
        fail("model path (%s) must be a directory." % opts.model)

    modelname = os.path.basename(os.path.normpath(opts.model))
    outpath = os.path.join(opts.out, modelname)

    log.debug("Copy %s to %s", opts.model, outpath)
    distutils.dir_util.copy_tree(opts.model, outpath)
    log.debug("directory to copy %d times: %s", opts.collectors,
              os.path.join(outpath, opts.collectorpath))
    sourcepath = os.path.join(outpath, opts.collectorpath)
    for n in range(1, opts.collectors):
        destpath = sourcepath + str(n)
        log.debug("copy %s to %s", sourcepath, destpath)
        distutils.dir_util.copy_tree(sourcepath, destpath)

    if opts.template or opts.zendev:
        templpath = outpath + ".json"
        log.debug("generating template %s from %s", templpath, outpath)
        with open(templpath, 'w') as outfile:
            command = ["serviced", "template", "compile"]
            if opts.zendev:
                command.extend(["--map",
                                "zenoss/zenoss5x,zendev/devimg:europa"])
            command.extend([outpath])
            call(command, stdout=outfile)
        log.info("generated template file: %s", templpath)


if __name__ == "__main__":
    options = args()
    main(options)
