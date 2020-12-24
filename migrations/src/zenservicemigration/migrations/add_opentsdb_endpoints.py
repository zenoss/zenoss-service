##############################################################################
#
# Copyright (C) Zenoss, Inc. 2020, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
from __future__ import print_function

__doc__ = '''
Add OpenTSDB reader endpoints to necessary services. 
It's necessary for Capacity ZenPack
'''

import itertools

from servicemigration.endpoint import Endpoint

version = "7.0.16"


def migrate(ctx, *args, **kw):
    service_names = (
        "Zope",
        "zenreports",
        "zenapi",
        "zendebug",
    )

    services = [
        x for x in ctx.services
        if x.name in service_names]

    if not services:
        print("failed to find any services to migrate")
        return

    endpoint_map = {
        "opentsdb-reader": Endpoint(
            name="opentsdb-reader",
            purpose="import",
            application="opentsdb-reader",
            portnumber=4242,
            protocol="tcp"),
    }

    updated = False

    for service, endpoint_key in itertools.product(services, endpoint_map):
        matching_services = [
            x for x in service.endpoints
            if x.purpose == "import" and x.application == endpoint_key]

        if not matching_services:
            print("adding {} endpoint to {} service".format(endpoint_key, service.name))

            service.endpoints.append(endpoint_map[endpoint_key])
            updated = True

    return updated
