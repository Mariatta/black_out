import gidgethub.routing


from . import tasks

router = gidgethub.routing.Router()

SECRET_CODES = [
    "turn off the sun",
    "take down the moon",
    "switch off the stars",
    "paint the sky black",
    "black out the sun",
]


@router.register("issues", action="reopened")
@router.register("issues", action="opened")
async def issue_opened(event, gh, *args, **kwargs):
    if event.data["issue"]["title"].strip().lower() in SECRET_CODES:

        issue_number = event.data["issue"]["number"]
        issue_creator = event.data["issue"]["user"]["login"]

        tasks.initiate_black_task.delay(issue_number, issue_creator)


@router.register("pull_request", action="labeled")
async def pr_labeled(event, gh, *args, **kwargs):
    """If the label is `black out` and the PR is still `open`."""
    if (
        event.data["label"]["name"] == "black out"
        and event.data["pull_request"]["state"] == "open"
    ):
        tasks.black_pr_task.delay(event.data)
