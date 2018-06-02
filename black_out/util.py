import subprocess
import os

import requests
from gidgethub import sansio

from . import exceptions


def exec_command(cmd):
    subprocess.check_output(cmd)


def checkout_branch(branch_name):
    cmd = ["git", "checkout", "-b", branch_name, "origin/master"]
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        raise exceptions.BranchCheckoutException(
            f"Can't check out `{branch_name}` branch"
        )


def check_black(src):
    commands = ["black", "--check"]
    commands.extend(src)
    result = subprocess.call(commands)
    return result


def commit_changes(issue_number=None):
    title = "🤖 Format code using `black`"
    closes_issue_message = f"Closes #{issue_number}" if issue_number else ""
    body = f"""

{closes_issue_message}
(I'm a bot 🤖)
"""
    message = title + body
    cmd = ["git", "commit", "-am", message]
    subprocess.check_output(cmd)
    return title, body


def comment_on_pr(issue_number, message):
    """
    Leave a comment on a PR/Issue
    """
    request_headers = sansio.create_headers(
        os.environ.get("GH_USERNAME"), oauth_token=os.getenv("GH_AUTH")
    )
    issue_comment_url = (
        f"https://api.github.com/repos/{os.environ.get('GH_REPO_FULL_NAME')}/issues/{issue_number}/comments"
    )
    data = {"body": message}
    response = requests.post(issue_comment_url, headers=request_headers, json=data)
    if response.status_code == requests.codes.created:
        print(f"Commented at {response.json()['html_url']}, message: {message}")
    else:
        print(response.status_code)
        print(response.text)


def create_gh_pr(base_branch, head_branch, *, title, body):
    """
    Create PR in GitHub
    """
    username = os.environ.get("GH_USERNAME")
    gh_auth = os.environ.get("GH_AUTH")
    repo_full_name = os.environ.get("GH_REPO_FULL_NAME")

    request_headers = sansio.create_headers(username, oauth_token=gh_auth)

    data = {
        "title": title,
        "body": body,
        "head": head_branch,
        "base": base_branch,
        "maintainer_can_modify": True,
    }
    url = f"https://api.github.com/repos/{repo_full_name}/pulls"
    response = requests.post(url, headers=request_headers, json=data)
    if response.status_code == requests.codes.created:
        print(f"PR created at {response.json()['html_url']}")
    else:
        print(response.status_code)
        print(response.text)


def delete_branch(branch_name):
    cmd = ["git", "branch", "-D", branch_name]
    subprocess.check_output(cmd)


def close_issue(issue_number):
    username = os.environ.get("GH_USERNAME")
    gh_auth = os.environ.get("GH_AUTH")
    repo_full_name = os.environ.get("GH_REPO_FULL_NAME")

    request_headers = sansio.create_headers(username, oauth_token=gh_auth)

    data = {"state": "closed"}
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{issue_number}"
    response = requests.patch(url, headers=request_headers, json=data)
    if response.status_code == requests.codes.created:
        print(f"PR created at {response.json()['html_url']}")
    else:
        print(response.status_code)
        print(response.text)


def get_pr_diff_files(diff_url):
    result = requests.get(diff_url)
    lines = result.text.split("\n")
    result = []
    for line in lines:
        if line.strip().startswith("diff --git "):
            chunks = line.strip().split(" ")
            a_file = chunks[2]
            filename = a_file[2:]
            result.append(filename)
    return result
