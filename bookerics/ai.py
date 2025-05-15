import json

from openai import AsyncOpenAI

from .constants import BOOKERICS_OPENAI_KEY, TAG_GPT_MODEL
from .utils import logger

client = AsyncOpenAI(api_key=BOOKERICS_OPENAI_KEY)


async def get_tags_and_description_from_bookmark(bookmark):
    logger.info(f"🤖 Getting tags and description for {bookmark}...")
    prompt = f"""You are an expert summarizer. Given metadata about a website bookmark, create a description and a list of tags.

Metadata:
Title: {bookmark["title"]}
URL: {bookmark["url"]}
Metadata Description: {bookmark["description"]}

Your output should be a Python dictionary with the following keys:
- "description": a sentence or two summarizing the content
- "tags": a list of 3-4 simple, plural-form tags. Use ["like","this"] format. Avoid hyphens and keep them relevant.

Only return the dictionary. Do not add any extra commentary."""

    completion = await client.chat.completions.create(
        model=TAG_GPT_MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {"role": "user", "content": bookmark["url"]},
        ],
    )

    tags_and_description = completion.choices[0].message.content
    if tags_and_description is None:
        raise ValueError("No content received from OpenAI API")
    tags_and_description_dict = json.loads(tags_and_description)

    tags_list = tags_and_description_dict["tags"]
    formatted_tags_list = [tag.lower().replace(" ", "-") for tag in tags_list]

    description = tags_and_description_dict["description"]

    logger.info(f"🏷️ Generated tags: {formatted_tags_list}")
    logger.info(f"📖 Generated decription: {description}")

    return formatted_tags_list, description
