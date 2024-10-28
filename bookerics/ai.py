import json

from openai import AsyncOpenAI

from .constants import BOOKERICS_OPENAI_KEY, GPT_MODEL
from .utils import logger

client = AsyncOpenAI(api_key=BOOKERICS_OPENAI_KEY)


async def get_tags_and_description_from_bookmark_url(bookmark_url):
    logger.info(f"🤖 Getting tags and description for {bookmark_url}...")
    completion = await client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": 'you are an expert summarizer. given a website address, you visit it and come up with what you think is the essence of the web site. you create two things from this: a description, and tags. a description is a sentence or two that distills what the page is about. you also create tags. tags should be simple and direct, and categorized so as to not interfere or contradict each other. aim for 3 - 4 per entry. avoid hyphenated names if possible. for generic nouns, use the plural form (books or cars, instead of book or car). an example: if the page was hosted on a site called https://travelgearreview.com, has an image of a backpack that has text surrounding it talking about the bag being great for travel, then a reasonable set of tags would be ["travel","reviews","bags","gear"]. This takes in info from the url, any text found on the web page, and using image recognition for whatever might appear on the front page from the user-supplied web address. there is a degree of creativity involved in picking appropriate tags. try to create them based on perceived weight of importance. your tags response should just be the tags you come up with after visiting the web page. respond with the tags inside quotes which are nestled inside brackets: ["just","like","this"] your final response will look like a Python dictionary. the keys will be "description" and "tags", and each value represents the description and tags that you just learned about. so an example for the previous website mentioned: {\n    "description": "<the description goes here>",\n    "tags": ["this","is","the","list","of","tags"]\n} this object/dictionary is the only thing you should return.\n',
                    }
                ],
            },
            {"role": "user", "content": [{"type": "text", "text": bookmark_url}]},
        ],
    )

    tags_and_description = completion.choices[0].message.content
    tags_and_description_dict = json.loads(tags_and_description)

    tags_list = tags_and_description_dict["tags"]
    formatted_tags_list = [tag.lower().replace(" ", "-") for tag in tags_list]

    description = tags_and_description_dict["description"]

    logger.info(f"🏷️ Generated tags: {formatted_tags_list}")
    logger.info(f"📖 Generated decription: {description}")

    return formatted_tags_list, description
