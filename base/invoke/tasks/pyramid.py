import configparser
import base.invoke.tasks.docker
import base.invoke.tasks.update
import invoke
import sys


def _config_combine(list_file_config, file_config_combined):
    # Combine the multiple config files
    config_combined = configparser.ConfigParser()
    for file_config_current in list_file_config:
        config_combined.read(file_config_current)

    with open(file_config_combined, 'w') as f:
        config_combined.write(f)


@invoke.task(pre=[base.invoke.tasks.update.update_dependencies])
def serve_test():
    _config_combine(
        [
            'pyramid_config.ini',
            'pyramid_config.test.ini'
        ],
        'pyramid_config.combined.ini'
    )
    base.invoke.tasks.docker.docker_localize(
        file_in='pyramid_config.combined.ini',
        file_out='pyramid_config.combined.localized.ini'
    )

    invoke.run(
        'python setup.py develop',
        encoding=sys.stdout.encoding
    )
    invoke.run(
        'pserve pyramid_config.combined.localized.ini',
        encoding=sys.stdout.encoding
    )


@invoke.task(pre=[base.invoke.tasks.update.update_dependencies])
def serve_production():
    _config_combine(
        [
            'pyramid_config.ini',
            'pyramid_config.production.ini'
        ],
        'pyramid_config.combined.ini'
    )

    invoke.run(
        'python setup.py develop',
        encoding=sys.stdout.encoding
    )
    invoke.run(
        'pserve pyramid_config.combined.ini',
        encoding=sys.stdout.encoding
    )
