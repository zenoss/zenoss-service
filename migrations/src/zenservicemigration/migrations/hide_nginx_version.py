##############################################################################
#
# Copyright (C) Zenoss, Inc. 2020, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################
from __future__ import print_function

import re

__doc__ = '''
Update nginx config to hide version in http response
'''

version = "7.0.16"


def migrate(ctx, *args, **kw):
    changed = False

    zproxy = ctx.getTopService()
    configfiles = zproxy.originalConfigs + zproxy.configFiles
    directive = "    server_tokens off;"

    for configfile in filter(lambda f: f.name == '/opt/zenoss/zproxy/conf/zproxy-nginx.conf', configfiles):
        config_text = configfile.content
        
        if directive in config_text:
            continue

        insert_point = re.search('http \{', config_text)
        if not insert_point:
            log.info("Couldn't update zproxy configuration, skipping.")
            continue

        insert_point = insert_point.end()
        config_text = config_text[:insert_point] + "\n" + directive + config_text[insert_point:]
        log.info("Adding 'server_tokens off' to '%s' for '%s'", configfile.name, zproxy.name)
        configfile.content = config_text
        changed = True

    return changed
