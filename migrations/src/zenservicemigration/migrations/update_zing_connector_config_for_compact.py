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

import servicemigration as sm

version = "7.0.19"

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
  listen_addr: ":9237"
"""

new_script="test \"$(/opt/zenoss/bin/healthchecks/zing_connector_answering 9237)\" = \"PONG\""

other_services = (
        "zenhubiworker",
        "zenhubworker (adm)",
        "zenhubworker (default)",
        "zenhubworker (user)",
        "zenhub",
        "MetricConsumer",
        "Zope",
        "zenapi",
        "zendebug",
        "zenjobs",
        )


def migrate(ctx, *args, **kw):
    service = next((s for s in ctx.services if s.name == "zing-connector"), None)
    if service is None:
        print("No zing-connector service found.", file=sys.stderr)
        return False

    changed = False

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
        if "admin" in configfile.content:
            configfile.content = remove_admin_port(configfile.content)
            changed = True

    initialLength = len(service.endpoints)
    service.endpoints = [ep for ep in service.endpoints[:] if ep.application != "zing-connector-admin"]

    changed = changed or len(service.endpoints) < initialLength

    answering = next((hc for hc in service.healthChecks if hc.name == "answering"), None)

    if answering is None:
        print("Adding missing 'answering' healthcheck", file=sys.stderr)
        answering = sm.HealthCheck(
            name="answering",
            script=new_script,
            interval=5.0,
        )
        service.healthChecks = [answering]
        changed = True

    if answering.script != new_script:
        answering.script = new_script
        print("Updated 'answering' healthcheck script.", file=sys.stderr)
        service.healthChecks = [answering]
        changed = True

    for svc in other_services:
        other_svc_changed = remove_endpoint_and_fix_hc(ctx, svc)
        changed = changed or other_svc_changed

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
                simple_port = port_line.replace("port:", "").strip()
                newLines.append("  listen_addr: \":" + simple_port + "\"")
                i += 1
        else:
            newLines.append(lines[i])
        i += 1
    content = '\n'.join(newLines)
    if not port_updated:
        content = content + http2_config
    return content


def remove_admin_port(content):
    """
    remove the old zing-connector admin port config
    """
    lines = content.split('\n')
    newLines = []
    i = 0
    admin_removed = False
    while i < len(lines):
        if "admin:" in lines[i]:
            if "port:" in lines[i+1]:
                admin_removed = True
                i += 1
        else:
            newLines.append(lines[i])
        i += 1
    content = '\n'.join(newLines)
    if admin_removed:
        print("Removed 'admin' section.")
    return content


def remove_endpoint_and_fix_hc(ctx, svc):
    """
    remove the zing-connector-admin endpoint and maybe update the zing-connector-answering healthcheck script
    """
    service = next((s for s in ctx.services if s.name == svc), None)
    if service is None:
        print("No {} service found, so did not remove endpoint.".format(svc), file=sys.stderr)
        return False

    initialLength = len(service.endpoints)
    service.endpoints = [ep for ep in service.endpoints[:] if ep.application != "zing-connector-admin"]

    changed = len(service.endpoints) < initialLength
    print("{} zing-connector-admin endpoint from {} service".format("Removed" if changed else "Did NOT remove", svc), file=sys.stderr)

    answering = next((hc for hc in service.healthChecks if hc.name == "zing-connector-answering"), None)

    # not all these services have the healthcheck
    if answering and answering.script != new_script:
        answering.script = new_script
        print("Updated 'zing-connector-answering' healthcheck script for {} service.".format(svc), file=sys.stderr)
        service.healthChecks = [answering]
        changed = True

    return changed
