import argparse


def get_parser():
    version = 1.0
    description = "Create Grafana dashboards for Rackspace MAAS entities."

    parser = argparse.ArgumentParser(description=description)

    config_args = [
        ('--g-config-file', str, 'Config file location.'),
        ('--g-pool-size', int, 'Green thread pool size.'),
        ('--g-template-dir', str, 'Directory containing templates.'),
        ('--g-datasource-url', str, 'Url to pull data from.'),
        ('--g-datasource-username', str, 'username'),
        ('--g-datasource-api-key', str, 'apikey')
    ]

    for name, type_, help_ in config_args:
        parser.add_argument(name, type=type_, help=help_)

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + str(version))

    help_ = "Validate templates only. Do not generate dashboards."
    parser.add_argument(
        '--validate',
        action='store_true',
        default=False,
        help=help_
    )

    parser.add_argument(
        '--file',
        type=str,
        help="Only create dashboard(s) from this template."
    )

    return parser
