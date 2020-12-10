##############################################################################
#
# Copyright (C) Zenoss, Inc. 2020, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""
Adding zcml-enable-cz-dashboard global property to the service context for disabling/enabling dashboard
"""


version = "7.0.16"


def migrate(ctx, *args, **kw):
    topContext = ctx.getTopService().context
    print("Adding zcml-enable-cz-dashboard global property to the service context")
    topContext["global.conf.zcml-enable-cz-dashboard"] = "Feature"
    return True
