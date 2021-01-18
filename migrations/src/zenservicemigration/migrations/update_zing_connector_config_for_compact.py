##############################################################################
#
# Copyright (C) Zenoss, Inc. 2021, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""
Update zing-connector config to support compact-metrics.
"""

from __future__ import print_function

import sys

version = "7.0.17"

new_configs = """metrics:
  enabled: false
jwt:
  skip: true
auth:
  disabled: true
gcloud:
  project_id: {{getContext . "cse.project"}}
streaming:
  api_key: ""
"""

http2_config = """http2:
  listen_addr: 9237
"""


def migrate(ctx, *args, **kw):
    services = [s for s in ctx.services if s.name == "zing-connector"]
    if not services:
        print("No zing-connector services found.", file=sys.stderr)
        return False

    changed = False
    for service in services:
        configfiles = service.originalConfigs + service.configFiles
        for configfile in filter(lambda f: f.name == '/opt/zenoss/etc/zing-connector/zing-connector.yml', configfiles):
            if "stackdriver" not in configfile.content:
                configfile.content = add_to_section(
                    configfile.content, "log:", "  stackdriver: 0")
                changed = True
            if "compact-topic" not in configfile.content:
                configfile.content = add_to_section(
                    configfile.content, "pubsub:", "  compact-topic: metric-in-compact")
                changed = True
            if "metrics" not in configfile.content or "gcloud" not in configfile.content:
                configfile.content = configfile.content + new_configs
                changed = True
            if "http2" not in configfile.content:
                configfile.content = update_svc_port(configfile.content)
                changed = True

    return changed


def add_to_section(content, section_line, config_line):
    """
    add config line to an existing section
    if the section is missing it will be created at the end of the file
    """
    if section_line not in content:
        insert_config = section_line + "\n" + config_line + "\n"
        content = content + insert_config
    else:
        lines = content.split('\n')
        newLines = []
        for line in lines:
            newLines.append(line)
            if section_line in line:
                newLines.append(config_line)
        content = '\n'.join(newLines)
    return content


def update_svc_port(content):
    """
    update the old zing-connector port config to a new form
    if no port config after http section just add the http2 config in the end
    """
    lines = content.split('\n')
    newLines = []
    i = 0
    port_updated = False
    while i < len(lines):
        if "http:" in lines[i]:
            if "port:" in lines[i+1]:
                port_updated = True
                newLines.append("http2:")
                port_line = lines[i+1]
                newLines.append(port_line.replace(
                    "port", "listen_addr"))
                i += 1
        else:
            newLines.append(lines[i])
        i += 1
    content = '\n'.join(newLines)
    if not port_updated:
        content = content + http2_config
    return content
