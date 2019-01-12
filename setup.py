import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

metadata = {
    'name': "docker-manifest",
    'version': "1.2",
    'author': "Derek Merck",
    'author_email': "derek_merck@brown.edu"
}

setuptools.setup(
    name=metadata.get("name"),
    version=metadata.get("version"),
    author=metadata.get("author"),
    author_email=metadata.get("author_email"),
    description="",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/derekmerck/docker-manifest",
    py_modules=['DockerManifest'],
    classifiers=(
        'Development Status :: 4 - Beta',
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    license='MIT',
    install_requires=['pyyaml', 'click'],
    entry_points='''
        [console_scripts]
        docker-manifest=DockerManifest:cli
    ''',
)