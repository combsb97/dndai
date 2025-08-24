from langchain_ollama import OllamaLLM
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import TypedDict
import json

import cmpgn_info
from map import Map, Location, Path

# Define the Campaign class as a top-level component
class Campaign:
    def __init__(self, main_quest_hook: str, key_locations: list[str], npcs: list[dict[str, str]], major_conflict: str, world_map: Map):
        self.main_quest_hook = main_quest_hook
        self.key_locations = key_locations
        self.npcs = npcs
        self.major_conflict = major_conflict
        self.world_map = world_map
        
    def __str__(self):
        return f"""
        Main Quest Hook: {self.main_quest_hook}
        Key Locations: {self.key_locations}
        NPCs: {self.npcs}
        Major Conflict: {self.major_conflict}
        """

# Define the CampaignGenerator class
class CampaignGenerator:
    # Initialize the CampaignGenerator with the base URL and model
    def __init__(self, base_url: str, model: str, campaign_template: str = cmpgn_info.campaign_template):
        self.base_url = base_url
        self.model = model
        self.campaign_template = campaign_template
        self.llm = self.initialize_llm()

    # Initialize the LLM
    def initialize_llm(self):
        try:
            return OllamaLLM(base_url=self.base_url, model=self.model, max_tokens=2048, temperature=0.7)
        except Exception as e:
            print(f"error: {e}")
            return None

    # Generate a plot for the campaign using the LLM.
    def generate_plot(self, campaign_details: str, players: str) -> str:
        if not self.llm:
            return None
        
        max_retries: int = 1

        prompt_template = PromptTemplate(
            title = "Generate a D&D campaign",
            template=self.campaign_template,
        )

        for attempt in range(max_retries):
            try:
                print("Generating plot...")
                response = self.llm.invoke(prompt_template.format(campaign_details=campaign_details, players=players))
                print(response)
                return response
            except Exception as e:
                print(f"Attempt failed: {e}")
                if attempt == max_retries - 1:
                    raise e

    # Parse the campaign dictionary into a Campaign object
    def parse_campaign(self, campaign_dict: dict) -> Campaign:
        world_map = self.create_world_map(campaign_dict["key_locations"])
        return Campaign(
            main_quest_hook=campaign_dict["main_quest_hook"],
            key_locations=campaign_dict["key_locations"],
            npcs=campaign_dict["npcs"],
            major_conflict=campaign_dict["major_conflict"],
            world_map=world_map
        )

    # Generate a campaign using the LLM
    def generate_campaign(self, campaign_details: str) -> Campaign:
        if not self.llm:
            return None

        max_retries: int = 1

        prompt_template = PromptTemplate(
            title="Generate a D&D campaign",
            template=self.campaign_template,
            placeholders={"campaign_details": campaign_details}
        )
        
        for attempt in range(max_retries):
            try:
                print("Generating campaign...")
                response = self.llm.invoke(prompt_template.format(campaign_details=campaign_details))
                print(response)
                campaign_dict = json.loads(response)
                campaign = self.parse_campaign(campaign_dict)
                print(type(campaign))
                return campaign
            except Exception as e:
                print(f"Attempt failed: {e}")
                if attempt == max_retries - 1:
                    raise e

    # Create a map of the campaign
    def create_world_map(self, key_locations: list[str]) -> Map:
        map = Map()
        for location in key_locations:
            map.add_location(location['name'], location['description'])

        for i in range(len(key_locations)-1):
            map.add_path(key_locations[i]['name'], key_locations[i+1]['name'])
        
        return map