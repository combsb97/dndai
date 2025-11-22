import json
import random
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

llm = Ollama(base_url="http://localhost:11434", model="mistral")

def stream_response(text):
    for chunk in llm.stream(text):
        if "content" in chunk and chunk["content"]:  # Check if "content" key exists and is not empty
            word = chunk["content"]
            print(chunk["content"], end=" ", flush=True)  # Print word and flush to immediately display
    print() # Add a newline at the end

# Example usage:
prompt = "Write a short story about a cat who goes on an adventure."
stream_response(prompt)

# prompt_template = PromptTemplate(
#     input_variabels=["theme"]
#     template="""
#     Generate a short but immersive D&D one-shot campaign set in {theme} world.
#     Include:
#     - A main quest hook
#     - Three key locations with descriptions
#     - Three NPCs with descriptions, motivations, personalities, and secrets.
#     - A major conflict or twist
#     Return the story in a structured JSON format.
#     """
# )

# def generate_campaign(theme: str) -> dict:
#     prompt = prompt_template.render(theme=theme)
#     response = llm.complete(prompt, max_tokens=1024)
#     return json.loads(response)

# player_state = {
#     "players": {},
#     "global_flags": {}
# }

# def add_player(player_id, name, race, char_class):
#     player_state["players"][player_id] = {
#         "name": name,
#         "race": race,
#         "class": char_class,
#         "location": "starting_area",
#         "inventory": [],
#         "quests_completed": []
#     }

# def update_location(player_id, new_location):
#     player_state["players"][player_id]["location"] = new_location

# def complete_quest(player_id, quest_id):
#     player_state["players"][player_id]["quests_completed"].append(quest_id)

# campaign = generate_campaign()