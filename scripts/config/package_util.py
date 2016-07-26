#!/usr/bin/env python

from __future__ import print_function
import json
import yaml
import os
import sys
import pathlib
import posixpath
import shutil
import argparse
from collections import OrderedDict
from pprint import pprint


def main():
    parser = argparse.ArgumentParser(
        description='This script is able to list package info '
        'and update uri/docker/command/cli for specific package')
    parser.add_argument(
        '-l', '--list',
        default=False,
        action='store_true',
        help='list package info')
    parser.add_argument(
        '-p', '--package',
        default='',
        help='packages to list, e.g. cassandra,kafka,spark')
    parser.add_argument(
        '-u', '--update',
        default=False,
        action='store_true',
        help='update the repo configuration via YAML, '
        'default file is `config.yml`.')
    parser.add_argument(
        '-f', '--file',
        default='',
        help='input YAML config file')

    args = parser.parse_args()

    current_dir = pathlib.Path(
        os.path.dirname(os.path.abspath(__file__)))
    up = str(current_dir / '..' / '..')

    if args.update:
        if args.file is '':
            update_package(up)
        else:
            update_package(up, args.file)

    if args.list:
        if args.package is '':
            pe = retrieve_package(up)
        else:
            package_names = [n for n in args.package.split(',')]
            pe = retrieve_package(up, package_names)


def read_json(json_file):
    with open(json_file) as jf:
        return json.load(jf)


def read_yaml(yaml_file):
    with open(yaml_file, 'r') as yf:
        try:
            return yaml.load(yf)
        except yaml.YAMLError as exc:
            print(exc)


def write_pretty_json(path, data):
    with open(path, 'w') as fd:
        fd.write(json.dumps(data,
                            sort_keys=True,
                            separators=(',', ': '),
                            indent=2) + '\n')
        fd.flush()
        os.fsync(fd)


def package_exist(package_name, packages_path):
    """Checking the package existence

    Args:
    package_name : A string indicating which package
    packages_path: A PosixPath indicating the overall packages path
    """

    d = (packages_path / package_name[0].upper() / package_name)
    return d.is_dir() and list(d.iterdir())


def package_version_exist(package_name, packages_path, version):
    """checking the version existence,
    if multiple dir has same version, take the largest id

    Args:
    package_name : A string indicating which package
    packages_path: A PosixPath indicating the overall packages path
    version: A string indicating specific version

    Returns:
    match_list: A list representing match dir w.r.t `version`
    copy_source: A PosixPath representing copy source dir if needed subsequently
      (default is the largest id)
    """

    d = (packages_path / package_name[0].upper() / package_name)
    version_dict = dict(map(lambda ver: (ver, read_json(str(ver / 'package.json')).get('version')),
                            d.iterdir()))
    match_list = [ k for k, v in version_dict.iteritems() if v==version ]
    copy_source = max(match_list, key=lambda i: int(i.name))
    return match_list, copy_source


def list_package_version_dir(package_name, packages_path):
    """Listing all package dirs and return the copy source/dest dir
    on the premise that package dir exists

    Args:
    package_name: A string indicating which package
    packages_path: A PosixPath indicating the overall packages path

    Returns:
    package_list: A list that contains all version dir(in PosixPath)
    copy_source: A PosixPath representing copy source dir if needed subsequently
      (default is the largest id)
    copy_dest: A PosixPath representing copy dest if needed subsequently
    """

    if package_exist(package_name, packages_path):
        d = (packages_path / package_name[0].upper() / package_name)
        list_all = [ ver for ver in d.iterdir() ]
        copy_source = max(list_all, key=lambda i: int(i.name))
        copy_dest = (copy_source.parent / str(int(copy_source.name) + 1))
        return list_all, copy_dest, copy_source


def config_uri(working_path, package_config_data):
    """Configuration of `uri` in `resource.json`

    Args:
    working_path: A PosixPath representing working dir for further configuration
    package_config_data: A dictionary contains all the configuration data for a specific package
    """

    if package_config_data.has_key('uri'):
        uri_config = package_config_data['uri']
        resource_file = str(working_path / 'resource.json')
        data = read_json(resource_file)
        if uri_config.has_key('all'):
            for k, v in data['assets']['uris'].iteritems():
                data['assets']['uris'][k] = posixpath.join(
                    uri_config['all'], posixpath.basename(v))
        for k, v in uri_config.iteritems():
            if data['assets']['uris'].has_key(k):
                data['assets']['uris'][k] = v
        write_pretty_json(resource_file, data)


def config_docker(working_path, package_config_data):
    """Configuration of `docker` in `resource.json`

    Args:
    working_path: A PosixPath representing working dir for further configuration
    package_config_data: A dictionary contains all the configuration data for a specific package
    """
    if package_config_data.has_key('docker'):
        docker_config = package_config_data['docker']
        resource_file = str(working_path / 'resource.json')
        data = read_json(resource_file)
        for k, v in docker_config.iteritems():
            if data['assets']['container']['docker'].has_key(k):
                data['assets']['container']['docker'][k] = v
        write_pretty_json(resource_file, data)


def config_cli(working_path, package_config_data):
    """Configuration of `cli` in `resource.json`

    Args:
    working_path: A PosixPath representing working dir for further configuration
    package_config_data: A dictionary contains all the configuration data for a specific package
    """
    if package_config_data.has_key('cli'):
        cli_config = package_config_data['cli']
        resource_file = str(working_path / 'resource.json')
        data = read_json(resource_file)
        if cli_config.has_key('all'):
            platform = ['darwin', 'linux', 'windows']
            for p in platform:
                v = data['cli']['binaries'][p]['x86-64']['url']
                data['cli']['binaries'][p]['x86-64']['url'] = posixpath.join(
                    cli_config['all'], posixpath.basename(v))
        for k, v in cli_config.iteritems():
            if data['cli']['binaries'].has_key(k):
                data['cli']['binaries'][k]['x86-64']['url'] = v
        write_pretty_json(resource_file, data)


def config_command(working_path, package_config_data):
    """Configuration of `command` in `command.json`

    Args:
    working_path: A PosixPath representing working dir for further configuration
    package_config_data: A dictionary contains all the configuration data for a specific package
    """
    if package_config_data.has_key('command') and (working_path / 'command.json').is_file():
        command_config = package_config_data['command']
        command_file = str(working_path / 'command.json')
        data = read_json(command_file)
        data['pip'] = [command_config]
        write_pretty_json(command_file, data)


config_lookup = {
    'uri': config_uri,
    'docker': config_docker,
    'cli': config_cli,
    'command': config_command
}


def retrieve_package(universe_path, packages=[], json_dest=None):
    """Retrieving package info via traversing `repo/packages/` dir
    fetch all accessible packages, save the fetched info into a json
    file(`json_dest`), default dest is `None` which dumps to stdout.
    info includes package, version, package uri

    Args:
    universe_path: A string representing the universe path
    package: A list representing a group of specific packages to be fetched
    `default => []`: all packages in the repo
    json_dest: A string representing destination of the package info, which
    is expected to be a json. `default => None`: dump to stdout

    Returns:
    package_entry: A dictionary contains certain package information.


    package path looks like:
    `universe/repo/packages/'capital letter'{A,B,C,D,...,Z}/'package'/{cassandra,spark,...}/{0,1,2,...}`
    largest dir-name as integer in the package sub-dir would be selected as the
    default/current version in DC/OS
    """

    package_entry = OrderedDict()
    packages_path = pathlib.Path(
        os.path.join(universe_path, 'repo', 'packages'))
    # all the packages exist in repo
    all_packages = [ p.name for l in packages_path.iterdir() for p in l.iterdir() ]
    if packages == []:
        packages = all_packages
    # 'A/B/C/D...Y/Z'
    for letter_path in packages_path.iterdir():
        assert len(letter_path.name) == 1 and letter_path.name.isupper()
        # 'packages in each upper letter dir'
        for package_path in letter_path.iterdir():
            if package_path.name not in packages:
                continue
            package_entry[package_path.name] = OrderedDict()
            # get the default/current version
            default_version_dir = max(
                package_path.iterdir(),
                key=lambda c: int(c.name))
            package_entry[package_path.name]['default_version'] = {
                default_version_dir.name : read_json(
                    str(default_version_dir / 'package.json')).get('version')}
            # traverse all the sub-dir in each package
            for ver in package_path.iterdir():
                package_entry[package_path.name][ver.name] = OrderedDict()
                package_dict = read_json(str(ver / 'package.json'))
                resource_dict = read_json(str(ver / 'resource.json'))
                resource_list = []
                resource_list.append({"uris":
                                      resource_dict.get('assets', {}).get('uris', {}).items()})
                resource_list.append({"docker":
                                      resource_dict.get('assets', {}).get('container', {}).get('docker', {}).items()})
                resource_list.append({"cli":
                                      resource_dict.get('cli', {}).get('binaries', {}).items()})
                package_entry[package_path.name][ver.name].update({
                    'version': package_dict['version'],
                    'description': package_dict['description'],
                    'framework': package_dict.get('framework', False),
                    'tags': package_dict['tags'],
                    'selected': package_dict.get('selected', False)})
                package_entry[package_path.name][ver.name].update({
                    'resource': resource_list})
                if (ver / 'command.json').is_file():
                    command_dict = read_json(str(ver / 'command.json'))
                    package_entry[package_path.name][ver.name].update({
                        'command': command_dict.items()})

    if json_dest == None:
        print(json.dumps(package_entry,
                         separators=(',', ': '),
                         indent=2) + '\n')
    else:
        write_pretty_json(json_dest, package_entry)

    p_set = set(packages)
    p_uset = p_set.union(set(all_packages))
    p_dset = p_uset.difference(set(all_packages))
    if p_dset: print('{} do(es) not exist'.format(list(p_dset)))
    return package_entry


def update_package(universe_path, config_file='config.yml'):
    """Update package, mainly focus on the uri/command

    Args:
    universe_path: A string representing the universe path
    config_file: A YAML file config all uri/command(s) need to be substituted
    """

    packages_path = pathlib.Path(
        os.path.join(universe_path, 'repo', 'packages'))
    config_data = read_yaml(config_file)
    target_packages = config_data.keys()
    update_list = ['uri', 'docker', 'cli', 'command']
    for tp in target_packages:
        pe = package_exist(tp, packages_path)
        if not pe:
            print('{} does not exist'.format(tp))
            continue
        pv = True
        ml, cp_dest, cp_source = list_package_version_dir(tp, packages_path)
        if config_data[tp].has_key('version'):
            v = config_data[tp]['version']
            ml, cp_source = package_version_exist(tp, packages_path, v)
            if not ml:
                pv = False
                print('{}:{} does not exist'.format(tp, v))
                continue
        if pe and pv:
            working_version = cp_source
            if config_data[tp].has_key('create') and config_data[tp]['create']:
                shutil.copytree(str(cp_source), str(cp_dest))
                working_version = cp_dest
            for ul in update_list:
                if config_data[tp].has_key(ul):
                    config_lookup[ul](working_version, config_data[tp])
    return config_data


if __name__ == "__main__":
    sys.exit(main())
