import asyncio
import json
import random
import re
import requests

from discord import Intents
from discord.ext import commands
from discord.utils import get

from environment_variables import (
    DISCORD,
    REDDIT,
    OPTION_FLAGS
)

from links import (
    hummer_links,
    tesla_link,
    prius_link
)

from compliments import (
    compliment_base,
    compliment_subject,
    compliment_descriptor,
    compliment_ending
)



##################################
#         DECLARATION            #
##################################

# Declare the bot
bot = commands.Bot(
    command_prefix = '!', 
    intents = Intents.all()
)

# Remove the {syntax}help option if required
if OPTION_FLAGS["REMOVE_HELP"]:
    bot.remove_command("help")

# Initialize the required queue(s)
reddit_queue = []



##################################
#      AUXILLIARY FUNCTIONS      #
##################################

async def handle_EV(ctx, message):
    """
    Handle any talk of EVs with brutal honesty

    Arguments:
            N/A

    Returns:
            N/A

    Raises:
            N/A
    """

    # Search the message for relevant string(s)
    tesla_regex = re.search(".*tesla.*", message)
    prius_regex = re.search(".*prius.*", message)
    sentiment_regex = re.search(".*((best)|(great)|(fantastic)|(love)).*", message)

    # Respond appriopriately if required to do so
    if (tesla_regex or prius_regex) and sentiment_regex:
        if tesla_regex:
            await ctx.reply(f"{random.choice(hummer_links)}\n{tesla_link}")

        else:
            await ctx.reply(f"{random.choice(hummer_links)}\n{prius_link}")


def get_posts(client, secret, username, password, queue, subreddit, max_posts):
    """
    Populate the given queue with a series of posts from a specified
    subreddit up to a maximum of 'max_posts' using the API constructed
    from the arguments provided

    Arguments:
            client (str): The client ID associated with the bot
            secret (str): The secret token associated with the bot
            username (str): The username of the Reddit account
            password (str): The passsword of the Reddit account
            queue (List): The queue to store posts into
            subreddit (str): The desired subreddit
            max_posts (int): The maximum amount of posts allowed

    Returns:
            N/A

    Raises:
            N/A
    """

    # Get authorization
    authorization = requests.auth.HTTPBasicAuth(client, secret)

    # Specify the login method
    # wth it's associated data
    data = {
        "grant_type": "password",
        "username": username,
        "password": password
    }

    # Setup our headers info
    headers = {"User-Agent": "Thanatos/0.0.1"}

    # Send our request for an OAuth token
    response = requests.post(
        "https://www.reddit.com/api/v1/access_token",
        auth = authorization, 
        data = data, 
        headers = headers
    )

    # Get the access token value
    access_token = response.json()["access_token"]

    # Define headers and get the headers
    headers = {
        **headers, 
        **{"Authorization": f"bearer {access_token}"}
    }
    requests.get("https://oauth.reddit.com/api/v1/me", headers = headers)

    # Get posts based on headers and parameters specified
    parameters = {"limit": 250, 't': "year"}
    response = requests.get(
        f"https://oauth.reddit.com/r/{subreddit}/top", 
        headers = headers, 
        params = parameters
    )

    # Parse the given posts
    response_data = []
    for post in response.json()["data"]["children"]:
        if post["data"]["stickied"] == True:
            continue

        queue.append({
            "title": post["data"]["title"],
            "selftext": post["data"]["selftext"],
            "ups": post["data"]["ups"],
            "downs": post["data"]["downs"],
            "url": post["data"]["url"],
            "thumbnail": post["data"]["thumbnail"]
        })

        if len(queue) >= max_posts:
            return



##################################
#         EVENT HANDLING         #
##################################

@bot.event
async def on_ready():
    print(f"Logged in as: {bot.user.name} (ID {bot.user.id})")


@bot.event
async def on_typing(channel, user, when):

    # Disregard input made by self
    if user == bot.user:
        return


@bot.event
async def on_message(message):

    # Disregard input made by self
    if message.author == bot.user:
        return

    # Check for string input in the message
    # (e.g. not a raw media type alone)
    if len(message.content) > 0:

        # Act on the message as required
        await handle_EV(message, message.content.lower())

        # Try to process the message as a command
        try:
            await bot.process_commands(message)
        except:
            print(exception)



##################################
#          COMMAND CALLS         #
##################################

@bot.command()
async def puppet(ctx):
    """
    Talk through the bot using 
    the corrosponding terminal

    Arguments:
            N/A

    Returns:
            N/A

    Raises:
            N/A
    """

    # Verify the author of the command call
    if (ctx.author.id != DISCORD["OWNER_ID"]):
        return

    # Hide the original command call
    await ctx.message.delete()

    # Take input repeatedly from the 
    # terminal until no input is given
    while True:
        response = input("Message: ")

        if (response != ""):
            await ctx.send(response)

        else:
            print("__END__\n")
            return


@bot.command()
async def peptalk(ctx):
    """
    Generate and reply back with a peptalk,
    sending it to another user if called as
    a reply to a message that user made

    Arguments:
            N/A

    Returns:
            N/A

    Raises:
            N/A
    """

    # Generate random response
    response = ''.join([
        random.choice(compliment_base),
        random.choice(compliment_subject),
        random.choice(compliment_descriptor),
        random.choice(compliment_ending)
    ])

    # Check for message to be
    # directed towards another user
    msg = ctx.message
    if ctx.message.reference != None:
        ctx.message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

    # Send message
    await ctx.message.reply(response)


@bot.command()
async def puptalk(ctx):
    """
    Run an API call to get a random dog

    Arguments:
            N/A

    Returns:
            N/A

    Raises:
            N/A
    """

    response = requests.get("https://random.dog/woof.json").json()
    await ctx.message.reply(response["url"])


@bot.command()
async def cattalk(ctx):
    """
    Run an API call to get a random cat

    Arguments:
            (tag): The filter to parse results from

    Returns:
            N/A

    Raises:
            N/A
    """

    # Handle the optional tags of the user input
    url_base = "https://cataas.com/cat"
    url_tags = ""
    if len(ctx.message.content) > 8:
        url_tags = f"/{ctx.message.content[9:]}"

    # Send out the request and handle responding
    # according to the request response
    response = requests.get(f"{url_base}{url_tags}?json=true")
    if response.status_code == 404:
        await ctx.message.reply(f"Sorry, no results for '{ctx.message.content[9:]}' tags")

    else:
        await ctx.message.reply(f"{url_base}{response.json()['url'][4:]}")


@bot.command()
async def fire(ctx):
    """
    Run an API call to arcgis.com 
    to check for fires in a given area

    Arguments:
            (county): The name of a county specified in
                      the command call (e.g. '!fire butte').

                      If not specified, all counties in the 
                      state are queried, and the first three 
                      returned are used in the text-response.

    Returns:
            N/A

    Raises:
            N/A
    """

    # Define the argument filter for county
    # from the command call
    filter_county = "1%3D1"
    if len(ctx.message.content) >= 6:
            filter_county = f"irwin_POOCounty%20%3D%20'{ctx.message.content.upper()[6:]}'"

    # Define the spatial filter for the request
    # to look specifically in California
    filter_state = [
        "geometry=-138.176%2C31.172%2C-100.471%2C43.363",
        "geometryType=esriGeometryEnvelope",
        "inSR=4326",
        "spatialRel=esriSpatialRelIntersects",
        "outSR=4326",
        "returnGeometry=False"
    ]

    # Define the basic request information and the
    # desired response format
    request_base = '/'.join([
        f"https://services3.arcgis.com",
        f"T4QMspbfLg3qTGWY",
        f"arcgis",
        f"rest",
        f"services",
        f"CY_WildlandFire_Perimeters_ToDate",
        f"FeatureServer",
        f"0",
        f"query?where={filter_county}&outFields="
    ])
    request_format = f"f=json"

    # Define the requested information
    # for each event returned
    request_fields = [
        "poly_Acres_AutoCalc",
        "irwin_FireCause",
        "irwin_IncidentName",
        "irwin_IncidentShortDescription",
        "irwin_PrimaryFuelModel",
        "irwin_UniqueFireIdentifier",
        "irwin_PercentContained",
        "irwin_POOCounty"
    ]

    # Make the request to the API
    response = requests.get(
            request_base 
            + ','.join(request_fields) + '&'
            + '&'.join(filter_state) + '&'
            + request_format
    )

    # Evaluate response JSON data
    reply_amount = 0
    for item in response.json()['features']:

            # Iterate through each event found
            for event, attributes in item.items():

                    # Check only 'big' events with incident descriptions
                    # (which are typically locations and whatnot)
                    if attributes['irwin_IncidentShortDescription'] == None:
                            continue

                    output = '\n'.join([
                        f"\n---------------------------------------------------\n",
                        f"**Incident Name:** {attributes['irwin_IncidentName']}",
                        f"**Unique Fire ID:** {attributes['irwin_UniqueFireIdentifier']}",
                        f"**County:** {attributes['irwin_POOCounty']}",
                        f"**Description:** {attributes['irwin_IncidentShortDescription']}",
                        f"**Primary Fuel:** {attributes['irwin_PrimaryFuelModel']}",
                        f"**Percent Contained:** {attributes['irwin_PercentContained']}%",
                        f"**Acres Affected:** {round(attributes['poly_Acres_AutoCalc'], 2)}",
                        f"**Fire Cause:** {attributes['irwin_FireCause']}"
                    ])

                    await ctx.send(output)
                    reply_amount += 1

                    if reply_amount >= 3:
                        return

    if reply_amount == 0:
        await ctx.message.reply(f"Sorry, no results for '{ctx.message.content[6:]}'")


@bot.command()
async def reddit(ctx):
    """
    Respond to the user with a Reddit post

    Arguments:
            N/A

    Returns:
            N/A

    Raises:
            N/A
    """

    # Check if the queue needs to be repopulated
    if len(reddit_queue) == 0:
        get_posts(
            client = REDDIT["CLIENT_ID"],
            secret = REDDIT["SECRET_TOKEN"],
            username = REDDIT["USERNAME"],
            password = REDDIT["PASSWORD"],
            queue = reddit_queue, 
            subreddit = "memes", 
            max_posts = 250
        )
        random.shuffle(reddit_queue)

    # Prepare the response and then pop from the queue
    # before sending the information to the calling user
    response = f"> {reddit_queue[-1]['title']}\n\n{reddit_queue[-1]['url']}"
    reddit_queue.pop()
    await ctx.reply(response)



##################################
#         INITIALIZATION         #
##################################

if __name__ == "__main__":
    bot.run(DISCORD["TOKEN"])