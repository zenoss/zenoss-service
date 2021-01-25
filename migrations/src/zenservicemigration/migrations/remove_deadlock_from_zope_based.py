##############################################################################
#
# Copyright (C) Zenoss, Inc. 2021, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from __future__ import print_function

version = "6.6.0"


def migrate(ctx, *args, **kw):
    svc_names = ("zope", "zauth", "zendebug", "zenapi", "zenreports")
    zope_based_services = [s for s in ctx.services if s.name.lower() in svc_names]
    changes = map(lambda svc: _delete_deadlock_check(svc), zope_based_services)
    return any(changes)


def _delete_deadlock_check(service):
    old_len = len(service.healthChecks)
    service.healthChecks = [hc for hc in service.healthChecks if hc.name != "deadlock_check"]
    if old_len > len(service.healthChecks):
        print("Deleted %s deadlock_check" % service.name)
        return True
    return False
