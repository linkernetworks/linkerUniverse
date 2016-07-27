# Linker Universe

The Linker Universe package repository, originally from [mesosphere/universe](http://mesosphere.github.io/universe/), tested by Linker(Mingdong).


## Linker DC/OS

currently supported frameworks/packages:

|package|version|
|---|---|
|cassandra| 2.2.5|
|kafka|0.9.0.1|
|spark|1.6.0|


## Usage


Please refer to [mesosphere/universe](https://github.com/mesosphere/universe) for details.

### tools

#### package_util.py

tiny script for listing/updating package configuration, which only compatible with a group of limited scenarios.

```
./scripts/config/package_util.py -h


usage: package_util.py [-h] [-l] [-p PACKAGE] [-u] [-f FILE]

This script is able to list package info and update uri/docker/command/cli for
specific package

optional arguments:
  -h, --help            show this help message and exit
  -l, --list            list package info
  -p PACKAGE, --package PACKAGE
                        packages to list, e.g. cassandra,kafka,spark
  -u, --update          update the repo configuration via YAML, default file
                        is `config.yml`.
  -f FILE, --file FILE  input YAML config file
```

listing all package available

```
./scripts/config/package_util.py -l
```

listing specified packages info

```
./scripts/config/package_util.py -l -p 'package1,package2,...'
```

updating **uri/docker/command/cli** in `repo/package/{A...Z}/package/version(:digits:)` via the default config file `scripts/config/config.yml`, checkout `scripts/config/config.yml.template`

```
./scripts/config/package_util.py -u
```

with option `-f`, the following provided *YAML* file will be used.

```yaml
package_1:
  version:
  create: (None|true|false)
  uri:
    uri_name_1:
    uri_name_2:
    all:
  docker:
    image_name_1:
    image_name_2:
  cli:
    darwin:
    linux:
    windows:
  command:

package_2:
```

#### generate-config-reference.py

```
Usage:  ./scripts/generate-config-reference.py [/path/to/universe/repo/packages]
```

by *mesosphere*, 


| Property | Type | Description | Default Value |
|----------|------|-------------|---------------|
|	|	|	|	

such format table will be generated via items belong to *properties* in `package/version/config.json`


#### build.sh

```
./scripts/build.sh
```

by mesosphere, this script will utilize `scripts/gen-universe.py` to generate *zipfile*  in `target` dir with version info controlled by `minDcosReleaseVersion` listed in `package.json`. Those *zipfiles* are backwards compatible with [cosmos](https://github.com/dcos/cosmos).

adding the customized repo(*zip*) to DC/OS

```
dcos package repo add [--index=<index>] <repo-name> <repo-url>

<repo-url> points to somewhere the zip-file stay...
```

