##############################################################################
#
# Copyright (C) Zenoss, Inc. 2020, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from __future__ import print_function

import json
import os
import sys

version = "6.6.0"

dependencies = (
    "update_zenjobs_for_celery31",
)


def migrate(ctx, *args, **kw):

    # Make sure the zenjobs scheduler service hasn't already been deployed
    count = sum((1 for s in ctx.services if s.name == "zenjobs scheduler"), 0)
    if count > 0:
        print("zenjobs scheduler is already deployed.  Skipping this step.")
        return False

    zj = next((s for s in ctx.services if s.name == "zenjobs"), None)
    if zj is None:
        print("zenjobs service not found.", file=sys.stderr)
        return False

    # Load zenjobs scheduler service template
    template_content = _loadfile("zenjobs_scheduler.json")
    template = json.loads(template_content)

    # Get root service for its ImageID value
    zproxy = ctx.getTopService()
    template["ImageID"] = zproxy.imageID

    # Load log_level config
    loglevel_content = _loadfile("zenjobs_scheduler_log_levels.conf")
    configFileName = "/opt/zenoss/etc/zenjobs_log_levels.conf"
    template["ConfigFiles"][configFileName]["Content"] = loglevel_content

    # Load schedules config
    schedules_content = _loadfile("zenjobs_schedules.yaml")
    configFileName = "/opt/zenoss/etc/zenjobs_schedules.yaml"
    template["ConfigFiles"][configFileName]["Content"] = schedules_content

    # Put the zenjobs scheduler into the same folder with zenjobs.
    folder = ctx.getServiceParent(zj)
    ctx.deployService(json.dumps(template), folder)

    return True  # True for changes were made.


def _loadfile(filename):
    cwd = os.path.dirname(__file__)
    config_file = os.path.join(
        cwd, "data", filename,
    )
    with open(config_file) as f:
        return f.read()
