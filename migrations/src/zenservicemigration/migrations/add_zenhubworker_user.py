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
import servicemigration as sm

version = "7.0.16"


def migrate(ctx, *args, **kw):

    changed = False

    # Make sure the "zenhubworker (user)" service hasn't already been deployed
    count = sum((1 for s in ctx.services if s.name == "zenhubworker (user)"), 0)
    if count > 0:
        print("zenhubworker (user) is already deployed.  Skipping this step.")

    else:
        changed = _deploy_zenhub_worker_user(ctx)


    # Add config for service call routing
    changed = _add_conf_for_service_calls(ctx)

    return changed


def _deploy_zenhub_worker_user(ctx):
    """
    deploy zenhubworker (user) service
    """

    changed = False
    hubs = [s for s in ctx.services if s.name == "zenhub"]
    if not hubs:
        print("zenhub service not found.", file=sys.stderr)
        return False

    # Load zenhubworker service template
    template_content = _loadfile("zenhubworker_user.json")
    template = json.loads(template_content)

    # Get root service for its ImageID value
    zproxy = ctx.getTopService()
    template["ImageID"] = zproxy.imageID

    # Add zenhubworker for each zenhub.
    for hub in hubs:
        folder = ctx.getServiceParent(hub)
        ctx.deployService(json.dumps(template), folder)
        print("zenhubworker (user) service successfully added")
        changed = True

    return changed


def _add_conf_for_service_calls(ctx):
    """
    add configuration file to zenhub service in order to make
    make configurable routing for zenhub service calls
    """
    changed = False
    configContent = _loadfile("zenhub-server.yaml")
    configFileName = "/opt/zenoss/etc/zenhub-server.yaml"

    confFile = sm.ConfigFile(
        name=configFileName,
        filename=configFileName,
        owner="zenoss:zenoss",
        permissions="660",
        content=configContent
    )
    services = [s for s in ctx.services if s.name == "zenhub"]    

    for service in services:
        if not [config for config in service.configFiles 
            if config.name == configFileName]:
            service.configFiles.append(confFile)
            print("add zenhub-server.yaml to {} service configuration".format(service.name))
            changed = True

    return changed

def _loadfile(filename):
    cwd = os.path.dirname(__file__)
    config_file = os.path.join(
        cwd, "data/zenhubworker_user", filename,
    )
    with open(config_file) as f:
        return f.read()
