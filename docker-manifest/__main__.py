#! python3

import yaml, logging, os, shutil
from subprocess import call
from argparse import ArgumentParser


def docker_rename_image(old, new):
    cmd = ['docker', 'tag', old, new]
    logging.debug(cmd)
    call(cmd)


def docker_push_image(image):
    cmd = ['docker', 'push', image]
    logging.debug(cmd)
    call(cmd)


def docker_push_manifest(manifest):
    cmd = ['docker', 'manifest', 'push', manifest]
    logging.debug(cmd)
    call(cmd)

def docker_manifest_create(manifest, aliases, service):
    # There is no "manifest remove" function, only "amend", so clean manually
    fp = os.path.expandvars( "$HOME/.docker/manifests/docker.io_{domain}_{service}-{tag}".format(
        domain=opts.domain,
        service=service,
        tag=opts.tag
    ))
    if os.path.exists(fp):
        logging.debug("Removing existing manifests at {}".format(fp))
        shutil.rmtree(fp)
    cmd = ['docker', 'manifest', 'create', manifest, *aliases]
    logging.debug(cmd)
    call(cmd)


def docker_manifest_annotate(manifest, item):
    cmd = ['docker', 'manifest', 'annotate',
           manifest, item['image'],
           '--arch', item['arch'],
           '--os', item['os'] ]
    if item.get('variant'):
        cmd = cmd + ['--variant', item["variant"]]
    logging.debug(cmd)
    call(cmd)


def parse_args():

    p = ArgumentParser(description = "docker-manifest creates Docker manifests for multi-architecture images from docker-compose service definitions")
    p.add_argument("-f", "--file", default="docker-compose.yml",
                   help="docker-compose file with service definitions (default: %(default)s)")
    p.add_argument("-d", "--domain",
                   help="docker domain name")
    p.add_argument("-t", "--tag", default="latest",
                   help="docker image tag (default: %(default)s)")
    p.add_argument('--dryrun', action="store_true",
                   help="Retag and push images, but do not push manifest")
    p.add_argument("services", nargs="+",
                   help="service base names")

    opts = p.parse_args()
    return opts


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    opts = parse_args()

    with open(opts.file) as f:
        data = yaml.safe_load(f)
        images = data.get('services')

    for service in opts.services:

        aliases = []
        annotations = {}

        for k, v in images.items():

            arch = v.get('build', {}).get('args', {}).get("DOCKER_ARCH", "amd64")
            logging.debug("Found {} for {}".format(arch, k))

            if k == "{}-{}".format(service, arch):

                # Retag and include this one in the manifest
                current_name = v.get('image')
                new_name = "{domain}/{service}:{tag}-{arch}".format(
                    domain=opts.domain,
                    service=service,
                    tag=opts.tag,
                    arch=arch)

                docker_rename_image( current_name, new_name )
                docker_push_image( new_name )

                aliases.append( new_name )

                def get_arch_str(arch):
                    if arch == "amd64" or arch == "x86_64":
                        return "amd64", None
                    elif arch == "arm32v7" or arch == "arm7hf":
                        return "arm", "v7"
                    elif arch == "arm64v8" or arch == "aarch64":
                        return "arm64", "v8"
                    else:
                        raise ValueError

                annotations[k] = {
                    'image':   new_name,
                    'arch':    get_arch_str(arch)[0],
                    'variant': get_arch_str(arch)[1],
                    'os':      'linux'
                }

        manifest = "{domain}/{service}:{tag}".format(
            domain=opts.domain,
            service=service,
            tag=opts.tag
        )

        docker_manifest_create(manifest, aliases, service)

        for annotation in annotations.values():
            docker_manifest_annotate(manifest, annotation)

        if not opts.dryrun:
            docker_push_manifest(manifest)
