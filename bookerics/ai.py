import json
from typing import List

from openai import OpenAI

from .constants import BOOKERICS_OPENAI_KEY, GPT_MODEL
from .utils import logger
import asyncio
from openai import AsyncOpenAI

# client = OpenAI(api_key=BOOKERICS_OPENAI_KEY)
client = AsyncOpenAI(api_key=BOOKERICS_OPENAI_KEY)

async def get_tags_and_description_from_bookmark_url(bookmark_url):
    logger.info(f'Getting tags and description for {bookmark_url}...')
    completion = await client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "you are an expert in summarizing the essence of a web page down into easily digestable parts. \n\na user gives you a website address, and you investigate it, and come up with what you think is the essence of the web site. you create two things from this: a description, and tags.\n\na description is as simple as it sounds. within a sentence or two, distill what the page is about. this is to reference later when looking up the url so the user is familiar with what the page does or represents. a description is a string.\n\nyou also create tags. tags should be simple and direct, and categorized so as to not interfere or contradict each other. for generic nouns, use the plural form. for example:\n\n* if the page was hosted on a site such as: https://travelgearreview.com\n* an image of a backpack that has text surrounding it talking about the bag being great for travel\n* the author talks about how great their Patagonia backpack is for traveling\n\nthen the tags you would generate for the response would be something like:\n\n[\"travel\",\"reviews\",\"bags\",\"backpacks\",\"gear\"]\n\nthis takes in info from the url, any text found on the web page, and using image recognition for whatever might appear on the front page from the user-supplied web address.\n\nin the instance where nothing is decipherable, either from poor descriptions, absent text, or non-descriptive urls, return:\n\n[\"\"]\n\nthere is a degree of creativity involved in picking appropriate tags. try to create them based on perceived weight of importance. do not get into the weeds of having a million tags that would be overkill. \"backpacks\" is a fine and descriptive tag; it is better than multiple words that could describe what a backpack is.\n\nthere are popular tags that should be included when found or when you find appropriate:\n\n\"code\" should be applied to any coding, programming, programming languages, etc.\n\n\"github\" should be applied to anything hosted on github.com\n\n\"books\" should be applied to any book, set of books, booklists, book reviews, etc. \"book\" should not be used, and the plural \"books\" should be used instead.\n\n\"apps\" should follow the same rule. as should other single noun items that could describe collections of thing: \"movies\", \"music\", \"songs\", \"videos\", \"shows\", \"food\", \"reviews\", etc.\n\nyour tags response should just be the tags you come up with after visiting the web page. respond with the tags inside quotes which are nestled inside brackets:\n\n[\"just\",\"like\",\"this\"]\n\nyour final response will look like a Python dictionary. the keys will be \"description\" and \"tags\", and each value represents the description and tags that you just learned about. so an example for the previous website mentioned:\n\n{\n    \"description\": \"<the description goes here>\",\n    \"tags\": [\"this\",\"is\",\"the\",\"list\",\"of\",\"tags\"]\n}\n\nthis object/dictionary is the only thing you should return.\n"
                    }
                ],
            },
            {"role": "user", "content": [{"type": "text", "text": bookmark_url}]},
        ],
    )

    tags_and_description = completion.choices[0].message.content
    tags_and_description_dict = json.loads(tags_and_description)

    tags_list = tags_and_description_dict['tags']
    formatted_tags_list = [tag.lower().replace(' ', '-') for tag in tags_list]

    description = tags_and_description_dict['description']

    logger.info(f'Generated tags: {formatted_tags_list}')
    logger.info(f'Generated decription: {description}')

    return formatted_tags_list, description
