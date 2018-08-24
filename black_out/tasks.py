import base64
import celery
import os
import shutil
import subprocess


from . import util, exceptions

app = celery.Celery("black_out")

app.conf.update(
    BROKER_URL=os.environ["REDIS_URL"], CELERY_RESULT_BACKEND=os.environ["REDIS_URL"]
)


@app.task()
def setup_repo(repo_name, repo_full_name):

    os.mkdir("repo_checkout")
    os.chdir("repo_checkout")
    print(f"Setting up {repo_name} repository, cloning from {repo_full_name}")

    if repo_name not in os.listdir("."):
        email_address = os.environ.get("GH_EMAIL")
        full_name = os.environ.get("GH_FULL_NAME")
        subprocess.check_output(
            [
                "git",
                "clone",
                f"https://{os.environ.get('GH_AUTH')}:x-oauth-basic@github.com/{repo_full_name}.git",
            ]
        )
        subprocess.check_output(
            ["git", "config", "--global", "user.email", f"'{email_address}'"]
        )
        subprocess.check_output(
            ["git", "config", "--global", "user.name", f"'{full_name}'"]
        )
        os.chdir(f"./{repo_name}")
        print(f"Finished setting up {repo_name} Repo")
    else:
        print(f"{repo_name} directory already exists")


@app.task()
def cleanup_repo():
    os.chdir("../..")
    shutil.rmtree("repo_checkout")


@app.task()
def initiate_black_task(repo_name, repo_full_name, issue_number, issue_creator):
    """Execute black

    1. git fetch origin
    2. git checkout -b issue-NNNN-initialize-black origin/master
    3. black .
    4. git commit -am "🤖 Format code using `black` ..."
    5. git push origin issue-NNNN-initialize-black
    6. create the PR
    7. git checkout master
    7. git branch -D issue-NNNN-initialize-black
    """
    setup_repo(repo_name, repo_full_name)
    # cd to the checked out repo, if not already there
    if "repo_checkout" in os.listdir("."):
        os.chdir("repo_checkout")
        os.chdir(f"./{repo_name}")

    branch_name = f"issue-{issue_number}-initialize-black"

    util.exec_command(["git", "fetch", "origin"])

    try:
        util.checkout_branch(branch_name)
    except exceptions.BranchCheckoutException as e:
        message = f"""
🤖 Sorry @{issue_creator}. I was not able to check out the branch in order
to create the pull request. Perhaps a pull request has been made, or
black has been initiated? (I'm a bot 🤖)
"""
        util.comment_on_pr(repo_full_name, issue_number, message)
        raise e

    needs_black = util.check_black(".")
    if needs_black:
        util.exec_command(["black", "."])
        commit_title, commit_body = util.commit_changes(issue_number)
        util.exec_command(["git", "push", "origin", branch_name])
        util.create_gh_pr("master", branch_name, title=commit_title, body=commit_body, repo_full_name=repo_full_name)
        util.exec_command(["git", "checkout", "master"])
        util.delete_branch(branch_name)
    else:
        message = f"""
🤖 @{issue_creator}, the repo appears to be already well formatted with `black`.
Closing the issue. 🌮
(I'm a bot 🤖)
"""

        util.comment_on_pr(repo_full_name, issue_number, message)
        util.close_issue(repo_full_name, issue_number)

    cleanup_repo()


@app.task()
def black_pr_task(event_data):
    """Execute black on a PR

    1. git fetch origin pull/{pr_number}/head:pr_{pr_number}
    2. git checkout pr_{pr_number}
    3. find out all affected files
    4. black <all affected files>
    5. gh PUT /repos/:owner/:repo/contents/:path
    6. comment on PR
    7. git stash
    8. git checkout master
    9. git branch -D pr_{pr_number}
    """
    repo_name = event_data["repository"]["name"]
    repo_full_name = event_data["repository"]["full_name"]

    setup_repo(repo_name, repo_full_name)

    # cd to the checked out repo, if not already there
    if "repo_checkout" in os.listdir("."):
        os.chdir("repo_checkout")
        os.chdir(f"./{repo_name}")

    pr_author = event_data["pull_request"]["user"]["login"]

    pr_number = event_data["pull_request"]["number"]
    pr_diff_url = event_data["pull_request"]["diff_url"]

    util.exec_command(
        ["git", "fetch", "origin", f"pull/{pr_number}/head:pr_{pr_number}"]
    )
    util.exec_command(["git", "checkout", f"pr_{pr_number}"])
    files_affected = util.get_pr_diff_files(pr_diff_url)

    blackened_files = []
    for path in files_affected:
        needs_black = util.check_black(path)
        if needs_black:
            commands = ["black"]
            commands.extend([path])
            util.exec_command(commands)
            with open(path, "rb") as reader:
                encoded = base64.b64encode(reader.read())
                decoded = encoded.decode("utf-8")
                util.update_pr(event_data, path, decoded)
                blackened_files.append(path)

    if blackened_files:

        message = f"🐍🌚🤖 @{pr_author}, I've formatted these files using `black`:"
        for b in blackened_files:
            message = message + f"\n - {b}"
        message = message + "\n (I'm a bot 🤖)"
        util.comment_on_pr(repo_full_name, pr_number, message)
        util.remove_label(repo_full_name, pr_number, "black out")

    else:
        message = "🐍🌚🤖 PR is already black! Good job!"
        util.comment_on_pr(repo_full_name, pr_number, message)
        util.remove_label(repo_full_name, pr_number, "black out")

    util.exec_command(["git", "stash"])
    util.exec_command(["git", "checkout", "master"])
    util.delete_branch(f"pr_{pr_number}")
    cleanup_repo()
