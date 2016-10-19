#!/usr/bin/env python

import bottle
import os
import shutil
import subprocess
import sys
import tempfile
import yaml

gitcache = "/home/jimmacarthur/gitcache"
check_repos = False

def fetch_git_repo(url, checkout_dir):
    # Type: (OpenControlTree, str, str) -> None
    # Does this repo exist?
    if os.path.exists(checkout_dir):
        gitdir = os.path.join(checkout_dir, ".git")
        if os.path.exists(gitdir):
            if check_repos:
                print("fetch_git_repo: update %s,%s"%(url, checkout_dir))
                subprocess.check_call(["git", "--git-dir", gitdir, "fetch"])
                # TODO: You haven't checked that's actually a checkout of url!
            return
    print("fetch_git_repo: clone %s,%s"%(url, checkout_dir))

    subprocess.check_call(["git", "clone", url, checkout_dir])

def fetch_yaml_repo(repo_spec, extract = None):
    url = repo_spec['url']
    revision = repo_spec['revision']
    temporary_checkout = False
    if os.path.exists(gitcache):
        checkout_dir = os.path.join(gitcache, "%s:%s"%(repo_spec['url'], repo_spec['revision']))
    else:
        checkout_dir = tempfile.mkdtemp()
        temporary_checkout = True
    fetch_git_repo(url, checkout_dir)
    r = load_yaml_recursive(checkout_dir)
    if  temporary_checkout: shutil.rmtree(checkout_dir)
    if extract and extract in r:
        return r[extract]
    return r

def fetch_dependencies(data):
    # Type (Dict[str,Any]) => None
    print("About to fetch depenencies for data: %s"%data['dependencies'])
    for (k,v) in data['dependencies'].items():
        print("Fetching %s dependencies"% k)
        fetched_list = []
        for repo in v:
            if k == 'systems':
                extraction = 'components'
            else:
                extraction = k
            fetched_list.append(fetch_yaml_repo(repo, extract=extraction))
        print("Replacing data['dependencies'][%s] with fetched list"%k)
        data['dependencies'][k] = fetched_list

def load_local_yaml(base_path, file_list, default_filename = None):
    # Type (Sequence [str]) => Dict[str, Any]
    print("Directly loading standards from list: %s"%file_list)
    loaded_things = {}
    for s in file_list:
        subfile_path = os.path.join(base_path, s)
        if os.path.exists(subfile_path):
            if os.path.isdir(subfile_path):
                if default_filename:
                    subfile_path = os.path.join(subfile_path,default_filename)
                else:
                    print("%s is a directory and there is no default filename given." % subfile_path)
                    sys.exit(1)
                # TODO: As well as using the default filename, in the case of component
                # directories, it may be necessary to add in any yaml files in that
                # directory.

            with open(subfile_path, "rt") as f:
                y = f.read()
                data = yaml.load(y)
                loaded_things[data['name']] = data
                print("Loaded standard %s: %s"%(subfile_path, repr(data)))
        else:
            print("Can't find file_list file: %s"%subfile_path)
            sys.exit(1)
    return loaded_things

def load_yaml_recursive(sourcedir):
    # Type: (str) -> Dict[str,Any]
    project_file = os.path.join(sourcedir, "opencontrol.yaml")
    if os.path.exists(project_file):
        with open(project_file, "rt") as f:
            y = f.read()
            data = yaml.load(y)
            for (k,v) in data.items():
                if k.lower() == "dependencies":
                    fetch_dependencies(data)
                if k.lower() == "standards":
                    data[k] = load_local_yaml(sourcedir, v)
                if k.lower() == "certifications":
                    data[k] = load_local_yaml(sourcedir, v)
                if k.lower() == "components":
                    data[k] = load_local_yaml(sourcedir, v, "component.yaml")
    return data

data = None

def main():
    global data
    sourcedir = sys.argv[1] # Type: str
    data = load_yaml_recursive(sourcedir)
    print(yaml.dump(data))
    bottle.run(host='0.0.0.0', port=8080, debug=True)

@bottle.route('/hello')
def hello():
    return "Hello World!"

def html_repr(v):
    if type(v) is dict:
        return html_dict(v)
    elif type(v) is list:
        return html_list(v)
    else:
        return repr(v)

def html_list(data):
    # Type: (Sequence[Any]) => str
    if len(data) == 0: return "[]"
    if len(data) == 1: return html_repr(data[0])
    r = "<ul>\n"
    for v in data:
        r += "<li>%s</li>\n"%html_repr(v)
    r += "</ul>\n"
    return r

def make_human_readable(s):
    # Type: (str) -> str
    s = s.replace("_", " ")
    return s.capitalize()

def html_dict(data):
    # Type: (Dict[str, Any]) => str
    if len(data) == 0: return ""
    r = "<ul>\n"
    for (k,v) in data.items():
        r += "<li>%s: "%(make_human_readable(k))
        r += html_repr(v)
        r += "</li>\n"
    r += "</ul>\n"
    return r

def is_valid_data_path(path):
    pos = data
    for p in path:
        if p not in pos: return False
        pos = pos[p]
    return True

def data_path(path):
    pos = data
    for p in path:
        if p not in pos: return None
        pos = pos[p]
    return pos

@bottle.route('/')
def show_repo():
    r = "<h1>%s</h1>\n"%(data['name'])
    r += "<p>%s\n"%(data['metadata']['description'])

    headings = [
        (['components'], "Components specified in this repository"),
        (['dependencies', 'systems'], "External systems"),
        (['dependencies', 'standards'], "External standards"),
        (['dependencies', 'certification'], "External certification sets")
        ]

    for h in headings:
        if is_valid_data_path(h[0]):
            r += "<h2>%s</h2>\n"%(h[1])
            r += html_repr(data_path(h[0]))

    return r


if __name__=="__main__":
    main()
