import base.docker
import invoke
import jinja2
import os
import yaml


@invoke.task()
def docker_console():
    base.docker.machine_console()


@invoke.task()
def docker_ip():
    print(base.docker.machine_ip())


@invoke.task()
def docker_localize(file_in=None, file_out=None):
    if file_in is not None and file_out is not None:
        # If files are specified, do just those
        entries = [
            {
                'in': file_in,
                'out': file_out
            }
        ]
    else:
        # Parse our config
        with open('_base_config.yml') as f:
            config_yaml = yaml.safe_load(f)

        entries = config_yaml['compile_docker_localize']['entries']

    # Compile files that need their docker-related information localized
    for entry in entries:
        jinja2_environment = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath='.'),
            undefined=jinja2.StrictUndefined
        )
        template = jinja2_environment.get_template(entry['in'])
        with open(entry['out'], 'w') as f:
            f.write(template.render({
                'DOCKER_LOCALIZE_CWD': os.path.normpath(os.getcwd()).replace('\\', '/'),
                'DOCKER_LOCALIZE_IP': base.docker.machine_ip()
            }))


@invoke.task()
def docker_machine_ensure():
    base.docker.machine_ensure()


@invoke.task(pre=[docker_localize])
def docker_start():
    base.docker.compose_run('tests/full/docker/test_compose.localized.yml', 'build')
    base.docker.compose_run('tests/full/docker/test_compose.localized.yml', 'up -d')


@invoke.task(pre=[docker_localize])
def docker_stop():
    base.docker.compose_run('tests/full/docker/test_compose.localized.yml', 'stop')
