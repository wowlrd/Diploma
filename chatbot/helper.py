import csv
import torch
from sentence_transformers import SentenceTransformer, util
import openai
from .models import *
import os
from bing_image_urls import bing_image_urls
from dotenv import load_dotenv

import openai
try:
    from openai import OpenAIError
except ImportError:
    OpenAIError = Exception

load_dotenv() 

os.environ["TOKENIZERS_PARALLELISM"] = "false"

def chatGPT(query: str):
    openai.api_key = os.environ['API_KEY']

    prompt = f"Search the web for information about '{query}' and provide a concise answer and address the user as a human would and remove any greetings at the beginning in a maximum of 80-100 words :\n"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

    except OpenAIError as e:
        return f"OpenAI API error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

    return response.choices[0].message.content.strip()



model = SentenceTransformer("all-MiniLM-L6-v2")


def data_generator():
    file = open('data.csv', mode='r', encoding='utf-8', newline='\n')
    reader = csv.reader(file, delimiter=',')
    next(reader)

    for contents in reader:
        yield tuple(contents)

    file.close()


def find_similarity(prompt: str):
    all_matches = []
    embeddings1 = model.encode(prompt, convert_to_tensor=True)

    for data in tuple(data_generator()):
        embeddings2 = model.encode(data[1], convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(embeddings1, embeddings2)

        if torch.lt(similarity, torch.tensor([[0.01]])):
            continue

        if torch.gt(similarity, torch.tensor([[0.35]])):
            all_matches.append([similarity, data[2]])

    if len(all_matches) > 1:
        final = [torch.tensor([[0.0]]), '']

        for item in all_matches:
            if torch.gt(item[0], final[0]):
                final = [item[0], item[1]]

        return [final]

    return all_matches


def image(prompt):
    url = bing_image_urls(prompt, limit=1)[0]

    return url
