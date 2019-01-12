import yaml, logging, os, shutil
from subprocess import call as _call
import re
from pprint import pformat

# Set this to avoid accidentally issuing docker commands
NO_CALL = False

def call(cmd):
    logging.info(cmd)
    if NO_CALL:
        return
    _call(cmd)


def docker_retag_image(old, new):
    cmd = ['docker', 'tag', old, new]
    call(cmd)


def docker_push_image(image):
    cmd = ['docker', 'push', image]
    call(cmd)


def docker_push_manifest(manifest):
    cmd = ['docker', 'manifest', 'push', manifest]
    call(cmd)

def docker_manifest_create(namespace, manifest, aliases):
    # There is no "manifest remove" function, only "amend", so clean manually
    fp = os.path.expandvars( "$HOME/.docker/manifests/docker.io_{namespace}_{manifest}".format(
        namespace=namespace,
        manifest=manifest
    ))
    if os.path.exists(fp):
        logging.debug("Removing existing manifests at {}".format(fp))
        if not NO_CALL:
            shutil.rmtree(fp)
    cmd = ['docker', 'manifest', 'create', manifest, *aliases]
    call(cmd)


def docker_manifest_annotate(manifest, item):
    cmd = ['docker', 'manifest', 'annotate',
           manifest, item['image'],
           '--arch', item['arch'],
           '--os', item['os'] ]
    if item.get('variant'):
        cmd = cmd + ['--variant', item["variant"]]
    call(cmd)

import click

@click.command(help="Create and push Docker manifests for multi-architecture images from docker-compose service definitions")
@click.argument("namespace", type=click.STRING)
@click.option("--file", "-f", default="docker-compose.yml",
                type=click.File(),
                show_default=True)
@click.option("--services", "-s", default="all",
                type=click.STRING,
                help="List services to manifest (comma sep)",
                show_default=True)
@click.option("--archs", "-a", default='all',
                type=click.STRING,
                help="List architectures to manifest (comma sep)",
                show_default=True)
@click.option("--tag", "-t", default="latest",
                type=click.STRING,
                help="Base tag for images",
                show_default=True)
@click.option("--dryrun", "-d", default=False, is_flag=True,
              help="Show commands and exit")
@click.option("--verbose", "-v", default=False, is_flag=True)
def cli(namespace, file, services, archs, tag, dryrun, verbose):

    if verbose or dryrun:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    global NO_CALL
    if dryrun:
        NO_CALL = True

    data = yaml.safe_load(file)
    images = data.get('services')

    logging.debug(pformat(images))

    _services = {}
    m = re.compile(r"(?P<service>.*)-(?P<arch>(amd64)|(arm32v7)|(arm64v8))")
    for k,v in images.items():
        mm = m.match(k)
        s = mm.group('service')
        a = mm.group('arch')

        v['service'] = s
        v['arch'] = a

        # arch = v.get('build', {}).get('args', {}).get("DOCKER_ARCH", "amd64")

        if (services == 'all' or s in services) and \
           (archs == 'all' or a in archs):
            if not _services.get(s):
                _services[s] = []
            _services[s].append(v)

    logging.debug(pformat(_services))

    for service, images in _services.items():
        aliases = []
        annotations = []
        for image in images:

            current_name = image.get('image')
            new_name = "{namespace}/{service}:{tag}-{arch}".format(
                namespace=namespace,
                service=service,
                tag=tag,
                arch=image['arch'])

            docker_retag_image(current_name, new_name)
            docker_push_image(new_name)

            aliases.append(new_name)

            def get_arch_str(arch):
                if arch == "amd64" or arch == "x86_64":
                    return "amd64", None
                elif arch == "arm32v7" or arch == "arm7hf":
                    return "arm", "v7"
                elif arch == "arm64v8" or arch == "aarch64":
                    return "arm64", "v8"
                else:
                    raise ValueError

            annotations.append({
                'image': new_name,
                'arch': get_arch_str(image['arch'])[0],
                'variant': get_arch_str(image['arch'])[1],
                'os': 'linux'
            })

        manifest = "{namespace}/{service}:{tag}".format(
            namespace=namespace,
            service=service,
            tag=tag
        )

        docker_manifest_create(namespace, manifest, aliases)

        for annotation in annotations:
            docker_manifest_annotate(manifest, annotation)

        docker_push_manifest(manifest)


# def parse_args():
#
#     p = ArgumentParser(description = "Create Docker manifests for multi-architecture images from docker-compose service definitions")
#     p.add_argument("-f", "--file", default="docker-compose.yml",
#                    help="docker-compose file with service definitions (default: %(default)s)")
#     p.add_argument("-d", "--domain",
#                    help="docker domain name")
#     p.add_argument("-t", "--tag", default="latest",
#                    help="docker image tag (default: %(default)s)")
#     p.add_argument('--dryrun', action="store_true",
#                    help="retag and push images, but do not push manifest")
#     p.add_argument("services", nargs="+",
#                    help="service base names")
#
#     opts = p.parse_args()
#     return opts
#
#
# def main():
#
#     logging.basicConfig(level=logging.DEBUG)
#     opts = parse_args()
#
#     with open(opts.file) as f:
#         data = yaml.safe_load(f)
#         images = data.get('services')
#
#     for service in opts.services:
#
#         aliases = []
#         annotations = {}
#
#         for k, v in images.items():
#
#             arch = v.get('build', {}).get('args', {}).get("DOCKER_ARCH", "amd64")
#             logging.debug("Found {} for {}".format(arch, k))
#
#             if k == "{}-{}".format(service, arch):
#
#                 # Retag and include this one in the manifest
#                 current_name = v.get('image')
#                 new_name = "{domain}/{service}:{tag}-{arch}".format(
#                     domain=opts.domain,
#                     service=service,
#                     tag=opts.tag,
#                     arch=arch)
#
#                 docker_retag_image( current_name, new_name )
#                 docker_push_image( new_name )
#
#                 aliases.append( new_name )
#
#                 def get_arch_str(arch):
#                     if arch == "amd64" or arch == "x86_64":
#                         return "amd64", None
#                     elif arch == "arm32v7" or arch == "arm7hf":
#                         return "arm", "v7"
#                     elif arch == "arm64v8" or arch == "aarch64":
#                         return "arm64", "v8"
#                     else:
#                         raise ValueError
#
#                 annotations[k] = {
#                     'image':   new_name,
#                     'arch':    get_arch_str(arch)[0],
#                     'variant': get_arch_str(arch)[1],
#                     'os':      'linux'
#                 }
#
#         manifest = "{domain}/{service}:{tag}".format(
#             domain=opts.domain,
#             service=service,
#             tag=opts.tag
#         )
#
#         docker_manifest_create(manifest, aliases, service)
#
#         for annotation in annotations.values():
#             docker_manifest_annotate(manifest, annotation)
#
#         if not opts.dryrun:
#             docker_push_manifest(manifest)

if __name__ == "__main__":
    cli()