#!/usr/bin/env python
#
# MIT License
# 
# Copyright (c) 2016 Codethink Limited
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
# =*= License: MIT =*=

def match_certs_to_components(data):
    controls_expected = []
    certification_sets = data['dependencies']['certifications']
    for certification_set in certification_sets:
        for (certification_name, cert_data) in certification_set.items():
            if(type(cert_data) == dict):
                standards = cert_data['standards']
                for (standard_name, controls_dict) in standards.items():
                    for (control_name, empty_dict) in controls_dict.items():
                        controls_expected.append(control_name)
    controls_satisfied = []

    components = [data['components']] + data['dependencies']['systems']
    for c in components:
        for (policy_name, policy_data) in c.items():
            if type(policy_data) == dict:
                for s in policy_data['satisfies']:
                    controls_satisfied.append(s['control_key'])

    print("Controls expected: %s"%controls_expected)
    print("Controls satisfied: %s"%controls_satisfied)
    return controls_satisfied
