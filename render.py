#!/usr/bin/env python

import argparse
import bottle
import os
import shutil
import subprocess
import sys
import tempfile
import yaml
import cgi # Required only for HTML escaping.

from retrieval import load_yaml_recursive
from stylesheet import style, header, footer
from match_certs import match_certs_to_components

data = None
controls_satisfied = None

def main():
    parser = argparse.ArgumentParser(description =
                                     'Visualize OpenControl projects')
    parser.add_argument('sourcedir', help =
                        "A directory containing an OpenControl project")
    parser.add_argument('--nofetch', default = False, action="store_const",
                        const = True, help =
                        'Use cached git directories without fetching')
    options = parser.parse_args()
    global data, controls_satisfied
    data = load_yaml_recursive(options.sourcedir, options)
    controls_satisfied = match_certs_to_components(data)
    print(yaml.dump(data))
    print "controls_satisfied: %s"%controls_satisfied
    bottle.run(host='0.0.0.0', port=8080, debug=True)

def html_repr(value, dict_kind = None):
    # Type: (Any, str) => str
    if type(value) is dict:
        return html_dict(value, dict_kind)
    elif type(value) is list:
        return html_list(value, dict_kind)
    elif type(value) is str:
        return cgi.escape(value)
    else:
        return cgi.escape(repr(value))

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
    html = "<ul>\n"
    for list_item in data:
        html += "<li>%s</li>\n"%html_repr(list_item, default_kind)
    html += "</ul>\n"
    return html

def make_human_readable(field_name):
    # Type: (str) -> str
    human_name = field_name.replace("_", " ")
    # Capitalize the first letter, but don't lowercase any further ones.
    # This may be an abbreviation like "AWS".
    return human_name[0].upper() + human_name[1:]

# Converts trees marked with the type 'certification' into HTML
# representing the certification status as list items.
def certification_status_items(certification_data):
    # Type (Dict[str, Any]) => str
    html = ""
    for (standard_name, standard_data) in certification_data:
        for(control_name, control_data) in standard_data.items():
            if control_name in controls_satisfied:
                html += "<li class=\"positive\">%s (from %s) - Satisfied</li>\n"%(control_name, standard_name)
            else:
                html += "<li class=\"negative\">%s (from %s) - Not satisfied</li>\n"%(control_name, standard_name)
    return html

# Attempts to encode a block comment (usually a 'description' field)
# into a HTML string.
def html_encode_block_quote(yaml_quote):
    return yaml_quote.replace("\n", "<br>")

def html_dict(data, default_kind = None):
    # Type: (Dict[str, Any]) => str
    if len(data) == 0: return ""
    html = "<ul>\n"
    dict_kind = default_kind
    if 'kind' in data: dict_kind = data['kind']
    for (k,v) in data.items():
        if dict_kind == "certification" and type(v) == dict:
            html += certification_status_items(v['standards'].items())
        elif k == "narrative":
            print("Processing narrative tag: %s"%(repr(v)))
            if type(data[k]) == list:
                # Component Schema v3
                for field in data[k]:                    
                    html += "<p><span>"
                    html += html_encode_block_quote(field['text'])
                    html += "</span>"
            else:
                # Component Schema <v3
                html += "<p><span>%s</span>" % (v.replace("\n", "<br>"))
        elif k in key_translation:
            if key_translation[k]:
                # TODO: Unsure about using escaped things in the href target.
                html += "<li>"
                html += key_translation[k].format(cgi.escape(v))+"</li>\n"
        else:
            # If it didn't match any known key, it's probably a user-defined
            # name, so make this an anchor
            link_target = k if dict_kind is None else "%s_%s" % (dict_kind, k)

            # TODO: link_target can legitimately contain '>' or '"', which
            # will break things...
            html += "<li id=\"%s\">%s: " % (link_target,
                                            cgi.escape (
                                                make_human_readable (k) ) )

            # html_repr can recursively call this function
            html += html_repr (v, dict_kind) + "</li>\n"
    html += "</ul>\n"
    return html

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
    r += "<p>Description for this repository: %s\n" % (
        data['metadata']['description'] )

    headings = [
        (['components'], "Components specified in this repository"),
        (['dependencies', 'systems'], "External systems"),
        (['dependencies', 'standards'], "External standards"),
        (['dependencies', 'certifications'], "External certification sets")
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
