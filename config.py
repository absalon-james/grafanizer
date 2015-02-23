import json
import logging
import os
import yaml

CONFIG_FILE = '.grafanizerrc'
CONFIG_PATH = os.path.expanduser(os.path.join('~', CONFIG_FILE))

logger = logging.getLogger('grafanizer.config')


def get_yaml(data):
    """
    Attempts to load yaml from data.

    @param data - String containing yaml
    @return Dictionary|None

    """
    try:
        return yaml.load(data)
    except yaml.parser.Error:
        return None


def get_json(data):
    """
    Attempts to load json from data.

    @param data - String containing json
    @return - Dictionary|None

    """
    try:
        return json.loads(data)
    except ValueError:
        return None


def config_from_env(config, map_):
    """
    Updates config with environment variables described by map_

    @param config - Dictionary config to update
    @param map_ - Dictionary keyed by config key names whose values are the
        names of environment variables.

    """
    for key, name in map_.items():
        value = os.getenv(name)
        if value:
            config[key] = value


def config_from_args(config, map_, args):
    """
    Updates config with values from args provided by an argparser.

    @param config - Dictionary config to update
    @param map - Dictionary keyed by config key names whose values are the
        names of attributes of an argparser namespace object.
    @param args - Namespace object created by argparse

    """
    for key, name in map_.items():
        value = getattr(args, name)
        if value:
            config[key] = value


def get_config(args=None):
    """
    Loads config from a file.
    Updates the config with environment variables.
    Updates the config with values from an argparser

    """
    # Use file specified in environment for configuration or the default
    config_file = os.getenv('G_CONFIG_FILE') or CONFIG_PATH

    # Use file specified in arguments or the above
    config_file = args.g_config_file or config_file

    logger.debug("Loading config from %s" % config_file)

    try:
        config = None
        with open(config_file, 'r') as f:
            contents = f.read()
        # Try yaml then json
        config = get_yaml(contents)
        if not config:
            config = get_json(contents)
    except IOError:
        logger.exception("Unable to load config from %s." % config_file)

    # Init config in case file not present
    if not config:
        config = {}
    if not config.get('datasource'):
        config['datasource'] = {}

    # Config from environment
    config_from_env(config, {
        'pool_size': 'G_POOL_SIZE',
        'template_dir': 'G_TEMPLATE_DIR'
    })
    config_from_env(config['datasource'], {
        'username': 'G_DATASOURCE_USERNAME',
        'api_key': 'G_DATASOURCE_API_KEY',
        'url': 'G_DATASOURCE_URL'
    })

    # Config from args
    config_from_args(config, {
        'pool_size': 'g_pool_size',
        'template_dir': 'g_template_dir'
    }, args)
    config_from_args(config['datasource'], {
        'username': 'g_datasource_username',
        'api_key': 'g_datasource_api_key',
        'url': 'g_datasource_url'
    }, args)

    if config.get('pool_size'):
        config['pool_size'] = int(config['pool_size'])
    if config.get('template_dir'):
        config['template_dir'] = os.path.expanduser(config['template_dir'])
    return config
