#!/usr/bin/env python

import bottle
import os
import shutil
import subprocess
import sys
import tempfile
import yaml
import cgi

from retrieval import load_yaml_recursive
from stylesheet import style, header, footer

data = None

def main():
    global data
    sourcedir = sys.argv[1] # Type: str
    data = load_yaml_recursive(sourcedir)
    print(yaml.dump(data))
    bottle.run(host='0.0.0.0', port=8080, debug=True)

def html_repr(v, dict_kind = None):
    # Type: (Any, str) => str
    if type(v) is dict:
        return html_dict(v, dict_kind)
    elif type(v) is list:
        return html_list(v, dict_kind)
    elif type(v) is str:
        return cgi.escape(v)
    else:
        return cgi.escape(repr(v))

key_translation = {
    "control_key": "Control key: <a href=\"#control_{0}\">{0}</a>",
    "standard_key": "Standard key: <a href=\"#standard_{0}\">{0}</a>",
    "path": "Path: <a href=\"{0}\">{0}</a>",
    "kind": None,
    "name": None,
}

def html_list(data, default_kind = None):
    # Type: (Sequence[Any]) => str
    if len(data) == 0: return "None"
    if len(data) == 1: return html_repr(data[0])
    r = "<ul>\n"
    for v in data:
        r += "<li>%s</li>\n"%html_repr(v, default_kind)
    r += "</ul>\n"
    return r

def make_human_readable(s):
    # Type: (str) -> str
    s = s.replace("_", " ")
    # Capitalize the first letter, but don't lowercase any further ones.
    # This may be an abbreviation like "AWS".
    return s[0].upper() + s[1:]

def html_dict(data, default_kind = None):
    # Type: (Dict[str, Any]) => str
    if len(data) == 0: return ""
    r = "<ul>\n"
    dict_kind = default_kind
    if 'kind' in data: dict_kind = data['kind']
    for (k,v) in data.items():
        if k == "narrative":
            print("Processing narrative tag: %s"%(repr(data[k])))
            if type(data[k]) == list:
                # Component Schema v3
                for field in data[k]:
                    r += "<p><span>%s</span>"%(field['text'].replace("\n", "<br>"))
            else:
                # Component Schema <v3
                r += "<p><span>%s</span>"%(data[k].replace("\n", "<br>"))
        elif k in key_translation:
            if key_translation[k]:
                print("debug: translating key type %s with data %s"%(k,repr(v)))
                # TODO: Unsure about using escaped things in the href target.
                r += "<li>" + key_translation[k].format(cgi.escape(v))+"</li>\n"
        else:
            # If it didn't match any known key, it's probably a user-defined name, so make this an anchor
            link_target = k if dict_kind is None else "%s_%s" % (dict_kind, k)

            # TODO: link_target can legitimately contain '>' or '"', which will break things...
            r += "<li id=\"%s\">%s: " % (link_target, cgi.escape (make_human_readable (k)))
            r += html_repr (v, dict_kind) + "</li>\n" # html_repr is where the recursion happens
    r += "</ul>\n"
    return r

def data_path(path):
    pos = data
    for p in path:
        if p not in pos: return None
        pos = pos[p]
    return pos

def is_valid_data_path(path):
    return data_path(path) != None

@bottle.route('/stylesheets/<path>')
def serve_static_files(path):
    return bottle.static_file(path, "stylesheets")

@bottle.route('/')
def show_repo():
    r = "<html><head>%s\n</head><body>" % style
    r += header
    r += "<section class=\"main-content\">\n"

    r += "<h1>%s</h1>\n" % (data['name']) # Heading
    r += "<p>Description for this repository: %s\n" % (data['metadata']['description'])

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

    r += "</section>"
    r += footer
            
    return r



if __name__=="__main__":
    main()
