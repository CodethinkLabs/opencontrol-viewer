#!/usr/bin/env python

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
            print("Processing component_set: %s"%(policy_data))
            if type(policy_name) == dict:
                for s in policy_data['satisfies']:
                    controls_satisfied.append(s['control_key'])

    print("Controls expected: %s"%controls_expected)
    print("Controls satisfied: %s"%controls_satisfied)
    return controls_satisfied
