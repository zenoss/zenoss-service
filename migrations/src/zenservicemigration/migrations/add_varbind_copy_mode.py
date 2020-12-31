##############################################################################
#
# Copyright (C) Zenoss, Inc. 2020, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
from __future__ import print_function


version = "6.6.0"


def migrate(ctx, *args, **kw):
    updated = False

    update_string = """# Varbind copy mode. 
# Assume we have the following varbinds:
#    someVar.0  Data0
#    someVar.1  Data1
# Possible copy modes:
# 0 - the varbinds are copied into event as one
#     field. Expected event fields:
#         someVar:         Data0,Data1
#         someVar.ifIndex: 0,1
# 1 - the varbinds are copied into event as several
#     fields and sequence field is added. 
#     Expected event fields:
#         someVar.0:        Data0
#         someVar.1:        Data1
#         someVar.sequence: 0,1
# 2 - the mixed mode. Uses varbindCopyMode=0 behaviour
#     if there is only one occurrence of the varbind, 
#     otherwise uses varbindCopyMode=1 behaviour
#varbindCopyMode 2
#
"""
    zentraps = filter(lambda z: z.name == "zentrap", ctx.services)

    for zentrap in zentraps:
        configfiles = zentrap.originalConfigs + zentrap.configFiles
        current_config = "/opt/zenoss/etc/{}.conf".format(zentrap.name)
        for configfile in filter(lambda f: f.name == current_config, configfiles):
            if 'varbindCopyMode' in configfile.content:
                print("varbindCopyMode option already exists in {}".format(current_config))
                continue
            print("Appending varbindCopyMode option to {} for '{}' service.".format(current_config, zentrap.name))
            configfile.content += update_string
            updated = True

    return updated
