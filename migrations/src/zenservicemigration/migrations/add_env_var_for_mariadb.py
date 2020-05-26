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
Add ZODB_DB env var for mariadb services
'''

version = "6.5.0"


def migrate(ctx, *args, **kw):
    updated = False
    zodb_env_entry = "MARIADB_DB=zodb"
    zep_env_entry = "MARIADB_DB=zep"

    mariadbservices = filter(lambda s: "mariadb" in s.name, ctx.services)
    print("Found {0} services with 'mariadb' in their service path".format(len(mariadbservices)))

    for mariaDBservice in mariadbservices:
        if mariaDBservice.name == 'mariadb-model' and zodb_env_entry not in mariaDBservice.environment:
            mariaDBservice.environment.append(zodb_env_entry)
            updated = True
            print("Added env variable for %s service" % mariaDBservice.name)
        if mariaDBservice.name == 'mariadb-events' and zep_env_entry not in mariaDBservice.environment:
            mariaDBservice.environment.append(zep_env_entry)
            updated = True
            print("Added env variable for %s service" %  mariaDBservice.name)
    return updated
