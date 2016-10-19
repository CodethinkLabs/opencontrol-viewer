#!/usr/bin/env python

import bottle
import os
import shutil
import subprocess
import sys
import tempfile
import yaml

from retrieval import load_yaml_recursive

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
