Docker-Manifest
==========================

Derek Merck  
<derek_merck@brown.edu>  
Rhode Island Hospital and Brown University  
Providence, RI  

Create manifest files for multi-arch images from docker-compose service definitions.

Platform Dependencies:  Docker
Pip Dependencies:  pyyaml

`docker-compose.yml` services name keys should be formatted as "{service}-{arch}", and arch should be
included in a "DOCKER_ARCH" build arg.  For example:

```yaml
services:
  my_service-amd64:
    build:
      args:
        DOCKER_ARCH: amd64
    image: my_image
```

This would register as a service definition with basename "my_service" and architecture "amd64".
Architectures may be any one of `amd64`, `arm32v7`, or `arm64v8`.

`$ docker-manifest -d domain my_service` would retag the output image `my_image` as
`domain/my_service:tag-amd64` and link it to `domain/my_service:tag` on docker.io.

Acceptable architecture definitions are listed here:
https://raw.githubusercontent.com/docker-library/official-images/a7ad3081aa5f51584653073424217e461b72670a/bashbrew/go/vendor/src/github.com/docker-library/go-dockerlibrary/architecture/oci-platform.go

A good reference for manipulating docker manifest lists:
https://lobradov.github.io/Building-docker-multiarch-images/#building-a-multi-arch-manifest

All images should be present in docker.io/my_namespace (not just locally) when the manifest is
created, or the script will report failures and no manifest will be created.  Any locally available
images will be retagged and pushed as part of this script when possible.