import aiohttp
import os

from aiohttp import web
from gidgethub import routing, sansio
from gidgethub import aiohttp as gh_aiohttp

router = routing.Router()


@router.register("issues", action="opened")
async def issue_opened_event(event, gh, *args, **kwargs):
    """ Whenever an issue is opened, greet the author and say thanks."""

    url = event.data['issue']['comments_url']
    author = event.data['issue']['user']['login']
    message = f"Thanks for report @{author}! I will look into this ASAP! (I'm a bot)"

    await gh.post(url, data={"body": message})

@router.register("pull_request", action="closed")
async def pull_request_closed(event, gh, *args, **kwargs):

    merged = event.data['pull_request']['merged']

    if merged:
        url = event.data['pull_request']['comments_url']
        message = "Thanks!"

        await gh.post(url, data={"body": message})


@router.register("pull_request", action="opened")
async def pull_request_closed(event, gh, *args, **kwargs):

    url = event.data['pull_request']['issue_url']
    await gh.patch(url, data={"labels": ['pending_review']})


@router.register("issue_comment", action="created")
async def issue_comment_created(event, gh, *args, **kwargs):

    author = event.data['comment']['user']['login']

    is_me = author == "jColeChanged"
    reaction_url = event.data['comment']['url'] + '/reactions'
    if is_me:

        await gh.post(
            reaction_url,
            data={'content': 'heart'},
            accept='application/vnd.github.squirrel-girl-preview+json'
        )


async def main(request):
    body = await request.read()

    # our authentication token and secret
    secret = os.environ.get("GH_SECRET")
    oauth_token = os.environ.get("GH_AUTH")

    # a representation of GitHub webhook event
    event = sansio.Event.from_http(request.headers, body, secret=secret)

    # instead of mariatta, use your own username
    async with aiohttp.ClientSession() as session:
        gh = gh_aiohttp.GitHubAPI(session, "jcolechanged", oauth_token=oauth_token)

        # call the appropriate callback for the event
        await router.dispatch(event, gh)

    # return a "Success"
    return web.Response(status=200)

if __name__ == "__main__":
    app = web.Application()
    app.router.add_post("/", main)
    port = os.environ.get("PORT")
    if port is not None:
        port = int(port)

    web.run_app(app, port=port)
