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
Add new configs to configuration.yaml of MetricConsumer and change value of
minTimeBetweenBroadcast from 200 to 100
'''

version = "6.6.0"

new_configs = [
    "lowCollisionMark: 1000000", 
    "perClientMaxBacklogSize: -1", 
    "perClientMaxPercentOfFairBacklogSize: 100", 
    "minTimeBetweenNotification: 100"
]


def migrate(ctx, *args, **kw):
    changed = False

    services = filter(lambda s: s.name == "MetricConsumer", ctx.services)
    for service in services:
        updated = False

        if update_config(service.name, service.originalConfigs):
            updated = True

        if update_config(service.name, service.configFiles):
            updated = True

        if updated:
            changed = True
            print("Updated service '{}'".format(service.name))

    return changed


def update_config(name, configs):
    config = next(
        (cfg for cfg in configs if cfg.name.endswith("/configuration.yaml")),
        None,
    )
    if config is None:
        print("Service '{}' has no 'configuration.yaml' config file".format(name))
        return False
    
    content = config.content
    content = content.replace("minTimeBetweenBroadcast: 200", 
                              "minTimeBetweenBroadcast: 100")
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "metricService:" in line:
            # new configs must have the same indentations as the existing ones
            spaces_count = len(lines[i+1]) - len(lines[i+1].lstrip())
            spaces = " " * spaces_count
            configs_to_insert = [spaces + cfg for cfg in new_configs if cfg not in content]
            lines[i+1:i+1] = configs_to_insert
            break

    content = '\n'.join(lines)
    if config.content != content:
        config.content = content
        return True
