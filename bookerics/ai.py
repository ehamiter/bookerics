import json

from openai import AsyncOpenAI

from .constants import BOOKERICS_OPENROUTER_KEY, OPENROUTER_BASE_URL, TAG_GPT_MODEL
from .utils import logger

client = AsyncOpenAI(api_key=BOOKERICS_OPENROUTER_KEY, base_url=OPENROUTER_BASE_URL)


async def get_tags_and_description_from_bookmark(bookmark):
    if not isinstance(bookmark, dict):
        raise ValueError("bookmark must be a dictionary")

    required_keys = ["title", "url", "description"]
    if not all(key in bookmark for key in required_keys):
        raise ValueError(f"bookmark must contain all required keys: {required_keys}")

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
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(bookmark)},
        ],
    )

    tags_and_description = completion.choices[0].message.content
    if tags_and_description is None:
        raise ValueError("No content received from OpenRouter API")
    tags_and_description_dict = json.loads(tags_and_description)

    tags_list = tags_and_description_dict["tags"]
    formatted_tags_list = [tag.lower().replace(" ", "-") for tag in tags_list]

    description = tags_and_description_dict["description"]

    logger.info(f"🏷️ Generated tags: {formatted_tags_list}")
    logger.info(f"📖 Generated decription: {description}")

    return formatted_tags_list, description
