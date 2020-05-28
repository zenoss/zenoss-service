from __future__ import print_function

import re


version = "6.5.0"


def migrate(ctx, *args, **kw):
    changed = False

    services = (
        svc
        for svc in ctx.services
        if svc.name in ("mariadb-model", "mariadb-events", "mariadb")
    )
    for service in services:
        updated = False

        if update_config(service.name, service.originalConfigs):
            updated = True

        if update_config(service.name, service.configFiles):
            updated = True

        if updated:
            changed = True
            print("Updated service '%s'" % (service.name,))

    return changed


skip_external_locking = re.compile(
    r"skip_external_locking\s*\n", re.MULTILINE,
)
log_error = re.compile(r"log_error=(\S+)\s*$", re.MULTILINE)
innodb_additional_mem_pool_size = re.compile(
    r"innodb_additional_mem_pool_size\s*=.*\n", re.MULTILINE,
)
innodb_file_format = re.compile(
    r"\s*\n"
    r"#\s*Use the Barracuda file format which enables support for dynamic "
    r"and\s*\n"
    r"#\s*compressed row formats.\s*\n"
    r"innodb_file_format\s*=.*",
    re.MULTILINE,
)
innodb_purge_threads = re.compile(r"innodb_purge_threads\s*=\s*(\d+)\s*")
purge_threads = 1
buffer_pool_instances = re.compile(
    r"\n\n(#\s*.*\n)*innodb_buffer_pool_instances\s*=.*\n",
    re.MULTILINE,
)


def update_config(name, configs):
    config = next(
        (cfg for cfg in configs if cfg.name.endswith("/my.cnf")),
        None,
    )
    if config is None:
        print("Service '%s' has no 'my.cnf' config file" % name)
        return False
    content = config.content
    content = reformat_log_error(log_error, content)
    content = deleteConfig(skip_external_locking, content)
    content = deleteConfig(innodb_additional_mem_pool_size, content)
    content = deleteConfig(innodb_file_format, content)
    content = update_purge_threads(innodb_purge_threads, content)
    content = update_buffer_pool_instances(buffer_pool_instances, content)
    if config.content != content:
        config.content = content
        return True


def reformat_log_error(matcher, config):
    result = matcher.search(config)
    if not result:
        return config
    start, end = result.span()
    captures = result.groups()
    try:
        path = captures[0]
    except IndexError:
        return config
    return ''.join((
        config[:start],
        "log_error = %s\n" % path,
        config[end:],
    ))


def update_purge_threads(matcher, config):
    result = matcher.search(config)
    if not result:
        return config
    start, end = result.span()
    captures = result.groups()
    try:
        count = int(captures[0])
    except ValueError:
        count = 0
    if count < purge_threads:
        return ''.join((
            config[:start],
            "innodb_purge_threads = %s\n\n" % (purge_threads,),
            config[end:],
        ))
    return config


_updated_buffer_pool_entry = """

# Setting innodb_buffer_pool_instances to 1 to avoid issue MDEV-21826.
# Additionally, this option was removed in MariaDB 10.5.1 because it offers
# little performance benefits.
innodb_buffer_pool_instances = 1
"""


def update_buffer_pool_instances(matcher, config):
    result = matcher.search(config)
    if not result:
        return config
    start, end = result.span()
    return ''.join((
        config[:start], _updated_buffer_pool_entry, config[end:]
    ))


def deleteConfig(matcher, config):
    """Returns a tuple containing the edited config and any data captured
    by the matcher.
    """
    result = matcher.search(config)
    if not result:
        return config
    start, end = result.span()
    return config[:start] + config[end:]
