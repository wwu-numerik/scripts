#!/usr/bin/env python3

import os

import format_check as fc


def clang_format_status(dirname):
    import requests
    token = os.environ['STATUS_TOKEN']
    auth = ('renemilk', token)
    pr = os.environ['TRAVIS_PULL_REQUEST']
    slug = os.environ['TRAVIS_REPO_SLUG']
    if pr == 'false':
        statuses_url = 'https://api.github.com/repos/{}/statuses/{}'.format(slug, os.environ['TRAVIS_COMMIT'])
    else:
        r = requests.get('https://api.github.com/repos/{}/{}'.format(slug, pr), auth=auth)
        statuses_url = r.json()['statuses_url']

    r = requests.post(statuses_url,
                  auth=auth, data={"state" : "pending",
                  "description" : "Checking if clang-format has been applied to all source files",
                  "context" : "ci/clang-format"})
    try:
        fails = fc.check_dir(dirname, staged_only=False)
    except Exception as _:
        state = 'error'
    else:
        state = 'failure' if len(fails) > 0 else 'success'

    r = requests.post(statuses_url,
                      auth=auth, data={"state" : state,
                      "description" : "Checked if clang-format has been applied to all source files",
                      "context" : "ci/clang-format"})
