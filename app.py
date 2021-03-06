import json
import logging
from random import choice
import os

import requests
import responder


api = responder.API()


VERSIONED_REPOS = [
    'IATI-Rulesets',
    'IATI-Extra-Documentation',
    'IATI-Codelists',
    'IATI-Standard-SSOT',
]

UNVERSIONED_REPOS = [
    'IATI-Developer-Documentation',
    'IATI-Guidance',
    'IATI-Codelists-NonEmbedded',
    'IATI-Websites',
]


VERSIONS = [
    '2.03',
    '2.02',
    '2.01',
    '1.05',
    '1.04',
]


BASE_BRANCHES = ['version-{}'.format(version) for version in VERSIONS]


EMOJI = [
    '⭐️', '✨', '🌟', '👍', '🙌', '💅', '😸',
    '🔥', '💥', '⚡️', '🐨', '🐝', '🐜', '🐬',
    '🌈', '🎉',
]


EXCLAMATIONS = [
    'Okay - no problem!',
    'Okey dokey!',
    'On it!',
    'Righto!',
    'Gotcha!',
]


def random_exclamation():
    return choice(EXCLAMATIONS) + ' ' + choice(EMOJI)


def post_to_travis(env):
    travis_url = 'https://api.travis-ci.com/repo/referencebot%2F' + \
                 'referencebot.github.io/requests'
    travis_data = {
        'request': {
            'branch': 'master',
            'config': {
                'env': env,
            }
        }
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Travis-API-Version': '3',
        'Authorization': 'token ' + os.environ['TRAVIS_TOKEN'],
    }
    resp = requests.post(travis_url, json=travis_data, headers=headers)
    return resp


def post_github_comment(comment, url):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'token ' + os.environ['GITHUB_TOKEN'],
    }
    data = {
        'body': comment
    }
    resp = requests.post(url, json=data, headers=headers)
    logging.info(f'Github comment: "{comment}" ({resp.status_code})')
    return resp


def is_relevant(data):
    if data.get('action') != 'created':
        logging.info('ignoring - not a creation event')
        return False
    if not data.get('issue', {}).get('pull_request'):
        logging.info('ignoring - not a PR')
        return False
    if '@referencebot' not in data.get('comment', {}).get('body', '').lower():
        logging.info('ignoring - comment not addressed to me!')
        return False
    return True


@api.background.task
def process_data(data):
    logging.info(data)

    if not is_relevant(data):
        return

    comment_url = data['comment']['issue_url'] + '/comments'

    if 'build' not in data['comment']['body'].lower():
        msg = 'Hi! How can I help? If you want me to build, just ' + \
              'mention my name and say "build".'
        post_github_comment(msg, comment_url)
        return

    if data['issue']['state'] != 'open':
        msg = 'Sorry - the pull request is closed so I can\'t build.'
        post_github_comment(msg, comment_url)
        return

    pr_url = data['issue']['pull_request']['url']
    pr_data = requests.get(pr_url).json()

    travis_env = {
        'GITHUB_API_URL': comment_url,
        'HEAD_REPO_URL': pr_data['head']['repo']['clone_url'],
        'HEAD_BRANCH': pr_data['head']['ref'],
        'REPO_NAME': pr_data['base']['repo']['name'],
        'VERSION': pr_data['base']['ref'],
    }

    build_version = [version for version in VERSIONS
                     if version in data['comment']['body']]
    build_version = 'version-{}'.format(build_version[0]) \
                    if len(build_version) == 1 else None
    if build_version:
        travis_env['VERSION'] = build_version

    if travis_env['REPO_NAME'] in UNVERSIONED_REPOS:
        if travis_env['VERSION'] == 'master':
            travis_env['VERSION'] = 'version-2.03'
        elif not build_version:
            msg = 'Sorry - the base branch is not the `master` ' + \
                  'branch, and you didn\'t specify another branch to ' + \
                  'build against. So, I\'m not sure how to proceed.'
            post_github_comment(msg, comment_url)
            return

    if travis_env['REPO_NAME'] not in VERSIONED_REPOS + UNVERSIONED_REPOS:
        msg = f'Sorry - I\'m afraid I don\'t know how to build the ' + \
              f'{travis_env["REPO_NAME"]} repository.'
        post_github_comment(msg, comment_url)
        return
    if travis_env['VERSION'] not in BASE_BRANCHES:
        msg = 'Sorry - the base branch doesn\'t look like a version ' + \
              'branch, so I\'m not sure how to proceed.'
        post_github_comment(msg, comment_url)
        return

    resp = post_to_travis(travis_env)

    if resp.status_code != 202:
        msg = f'Err... I had some problem:\n\n{resp.reason}'
        post_github_comment(msg, comment_url)
        return

    txt_version = travis_env['VERSION'].replace('-', ' ')

    msg = random_exclamation()

    if travis_env['REPO_NAME'] != 'IATI-Standard-SSOT':
        msg += f' I\'ll build against ' + \
               f'[`{txt_version}`](https://github.com/IATI/' + \
               f'IATI-Standard-SSOT/tree/{travis_env["VERSION"]}).'

    msg += f'\n\nI\'ll post a link when it\'s ready.'
    post_github_comment(msg, comment_url)


@api.route('/')
async def home(req, resp):
    resp.text = 'Nothing to see here!'


@api.route('/github')
async def webhook(req, resp):
    try:
        data = await req.media()
    except json.decoder.JSONDecodeError:
        resp.media = {'success': False}
        return
    process_data(data)
    resp.media = {'success': True}


if __name__ == '__main__':
    api.run()
