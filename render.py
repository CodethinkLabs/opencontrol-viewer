#!/usr/bin/env python

import bottle
import os
import shutil
import subprocess
import sys
import tempfile
import yaml

from retrieval import load_yaml_recursive
from stylesheet import style

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

def html_repr(v, dict_kind = None):
    if type(v) is dict:
        return html_dict(v, dict_kind)
    elif type(v) is list:
        return html_list(v, dict_kind)
    else:
        return repr(v)

key_translation = {
    "control_key": "Control key: <a href=\"#control_{0}\">{0}</a>",
    "standard_key": "Standard key: <a href=\"#standard_{0}\">{0}</a>",
    }

def html_list(data, default_kind = None):
    # Type: (Sequence[Any]) => str
    if len(data) == 0: return "[]"
    if len(data) == 1: return html_repr(data[0])
    r = "<ul>\n"
    for v in data:
        r += "<li>%s</li>\n"%html_repr(v, default_kind)
    r += "</ul>\n"
    return r

def make_human_readable(s):
    # Type: (str) -> str
    s = s.replace("_", " ")
    return s.capitalize()

def html_dict(data, default_kind = None):
    # Type: (Dict[str, Any]) => str
    if len(data) == 0: return ""
    r = "<ul>\n"
    dict_kind = default_kind
    if 'kind' in data: dict_kind = data['kind']
    for (k,v) in data.items():
        if k == "narrative":
            r += "<p><span>%s</span>"%(data[k][0]['text'].replace("\\n", "\n"))
        elif k in key_translation:
            print("debug: translating key type %s with data %s"%(k,repr(v)))
            r += "<li>" + key_translation[k].format(v)+"</li>\n"
        else:
            # Make it an anchor
            link_target = k if dict_kind is None else "%s_%s"%(dict_kind, k)
            r += "<li id=\"%s\">%s: "%(link_target, make_human_readable(k))
            r += html_repr(v, dict_kind)+"</li>\n" # html_repr is where the recursion happens
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
    r = "<html>"
    r += "<head>"
    r += style
    r += "</head><body>"
    r += "<h1>%s</h1>\n"%(data['name'])
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
