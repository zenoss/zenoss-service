##############################################################################
#
# Copyright (C) Zenoss, Inc. 2020, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from __future__ import print_function

import os
import servicemigration as sm
import sys

version = "7.0.16"


def migrate(ctx, *args, **kw):
    service = next((s for s in ctx.services if s.name == "zenjobs"), None)
    if service is None:
        print("zenjobs service not found.", file=sys.stderr)
        return False

    changes = []

    changes.append(_updateStartup(service))
    changes.append(_updateRunAs(service))
    changes.append(_deleteActions(service))
    changes.append(_updateInstances(service))

    for configName in ("configFiles", "originalConfigs"):
        configFiles = getattr(service, configName)
        changes.append(_addConfig(
            configFiles,
            configName,
            migrationData.loglevels_config_filename,
            migrationData.loglevels_config,
        ))
        changes.append(_addConfig(
            configFiles,
            configName,
            migrationData.zodb_config_filename,
            migrationData.zodb_config,
        ))
        changes.append(_replaceZenJobsConfig(configFiles, configName))
    changes.append(_updateRunningHealthCheck(service))

    return any(changes)


class _MigrationData(object):

    startup_command = (
        "/opt/zenoss/bin/zenjobs worker "
        "-n \"zenjobs-$CONTROLPLANE_INSTANCE_ID@%h\""
    )

    loglevels_config_filename = "/opt/zenoss/etc/zenjobs_log_levels.conf"
    loglevels_config = {
        "Filename": loglevels_config_filename,
        "Owner": "zenoss:zenoss",
        "Permissions": "0664",
        "Content": "\n".join([
            "STDOUT          INFO",
            "zen             INFO",
            "zen.zenjobs     INFO",
            "zen.zenjobs.job INFO",
            "celery          WARN",
        ]) + "\n",
    }

    zodb_config_filename = "/opt/zenoss/etc/zodb.conf"
    _zodb_config = {
        "Filename": zodb_config_filename,
        "Owner": "zenoss:zenoss",
        "Permissions": "0660",
        "Content": None,
    }

    running_healthcheck = "pgrep -fu zenoss zenjobs > /dev/null"

    @property
    def zodb_config(self):
        content = self._loadfile("zenjobs-celery3126upgrade_zodb.conf")
        self._zodb_config["Content"] = content
        return self._zodb_config

    @property
    def zenjobs_config_content(self):
        return self._loadfile("zenjobs-celery3126upgrade_zenjobs.conf")

    @staticmethod
    def _loadfile(filename):
        cwd = os.path.dirname(__file__)
        config_file = os.path.join(
            cwd, "data", filename,
        )
        with open(config_file) as f:
            return "".join(f.readlines())


migrationData = _MigrationData()


def _updateStartup(service):
    if service.startup != migrationData.startup_command:
        service.startup = migrationData.startup_command
        print("Updated zenjobs startup command")
        return True
    return False


def _updateRunAs(service):
    if service.runAs != "zenoss":
        service.runAs = "zenoss"
        print("Updated zenjobs RunAs field")
        return True
    return False


def _deleteActions(service):
    if service._Service__data["Actions"]:
        # Delete Actions as they're now obsolete
        service._Service__data["Actions"] = None
        print("Deleted zenjobs actions")
        return True
    return False


def _updateInstances(service):
    service.instanceLimits.default = 2
    service.instanceLimits.minimum = 1
    service.instanceLimits.maximum = 0
    return True


def _addConfig(configfiles, configname, filename, config):
    configFile = next((
        cf for cf in configfiles if cf.name == filename
    ), None)
    if configFile is not None:
        print("Config file %s already added to %s." % (filename, configname))
        return False
    configFile = sm.ConfigFile(
        name=filename,
        filename=config.get("Filename"),
        owner=config.get("Owner"),
        permissions=config.get("Permissions"),
        content=config.get("Content"),
    )
    configfiles.append(configFile)
    print("Added %s config file to %s." % (filename, configname))
    return True


def _replaceZenJobsConfig(configfiles, configname):
    filename = "/opt/zenoss/etc/zenjobs.conf"
    configFile = next((
        cf for cf in configfiles
        if cf.name == filename
    ), None)
    if configFile is None:
        configFile = sm.ConfigFile(
            name=filename,
            filename=filename,
            owner="zenoss:zenoss",
            permissions="0664",
        )
        configfiles.append(configFile)
        print("Added missing config file %s" % (filename,))
    if configFile.content != migrationData.zenjobs_config_content:
        configFile.content = migrationData.zenjobs_config_content
        print(
            "Replaced content of %s config file in %s."
            % (configFile.filename, configname)
        )
        return True
    return False


def _updateRunningHealthCheck(service):
    running = next(
        (hc for hc in service.healthChecks if hc.name == "running"),
        None,
    )
    if running is None:
        print("Adding missing 'running' healthcheck")
        running = sm.HealthCheck(
            name="running",
            script=migrationData.running_healthcheck,
            interval=5.0,
        )
        return True
    if running.script != migrationData.running_healthcheck:
        running.script = migrationData.running_healthcheck
        print("Updated 'running' healthcheck script.")
        return True
    return False
