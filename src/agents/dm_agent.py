import random
import winsound
import yaml
import json
import os
from datetime import datetime
from termcolor import colored
from typing import TypedDict, List, Annotated, Dict, Any
import operator
import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import langchain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, START, END
# from game_state import gamestate  # Will be replaced by GameStateManager
from src.core.GameStateManager import game_session_manager
from src.services.RemoteOllama import llm
from src.services.RemoteChatterboxTTS import tts_client

langchain.verbose = True

class DMAgent:
    def __init__(self, config_path="config.yaml"):
        self.gamestate = game_session_manager
        self.messages = []
        self._load_config(config_path)
        # self.llm = self._get_llm()
        self.json_parser = JsonOutputParser()

    def _load_config(self, config_path):
        # It's better to load config from a file
        # For now, we'll keep it here
        self.config = {
            "provider": "ollama",
            "gemini_model": "gemini-2.5-flash",
            "ollama_model": "llama3.1:8b",
            "ollama_urls": ["http://localhost:11434", "http://192.168.0.18:11434"],
            "ollama_selected_url": "http://localhost:11434",
            "ollama_temperature": 0.7,
            "ollama_keep_alive": 0
        }

    def _get_llm(self, max_tokens=1000):
        if self.config["provider"] == "gemini":
            return ChatGoogleGenerativeAI(model=self.config["gemini_model"])
        elif self.config["provider"] == "ollama":
            # Use the selected Ollama URL
            return ChatOllama(
                model=self.config["ollama_model"],
                base_url=self.config["ollama_selected_url"],
                temperature=self.config["ollama_temperature"],
                max_tokens=max_tokens,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self.config['provider']}")

    def _get_gamestate_context_for_llm(self):
        """Assembles the current game state context for the LLM."""
        return {
            "location data": self.gamestate.location_manager.get_location_data(),
            "npcs data": self.gamestate.npc_manager.get_npc_data(),
            "players data": self.gamestate.player_manager.get_player_data(),
        }

    def interpret_user_intent(self, player_input: str) -> str:
        """
        Use an LLM to interpret the player's intent from their input.
        This is a placeholder function; replace it with actual LLM integration.
        """
        try:
            with open("prompts.yaml", "r") as f:
                system_prompt = yaml.safe_load(f)["user_intent_prompt"]
        except Exception as e:
            print(f"Error loading prompts.yaml: {e}")
            return "Error"
        
        llm = self._get_llm(max_tokens=2000)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "## Raw User Input: {user_input}"),
        ])

        chain = prompt | llm | self.json_parser

        try:
            parsed_intent = chain.invoke({
                "session_context": self._get_gamestate_context_for_llm(),
                "user_input": player_input
            })
            return parsed_intent
        except Exception as e:
            print(f"An error occurred during LLM intent interpretation: {e}")
            return {"type": "ERROR", "detail": "Failed to interpret intent."}

    def generate_action_plan(self, player_input: str, all_valid_events: List[dict], invalid_events: List[dict]) -> str:
        """
        Use an LLM to interpret the player's input and determine the next action.
        """
        try:
            with open("prompts.yaml", "r") as f:
                system_prompt = yaml.safe_load(f)["interpreter_prompt"]
        except Exception as e:
            print(f"Error loading prompts.yaml: {e}")
            return "Error"
        
        llm = self._get_llm(max_tokens=5000)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "## Parsed User Input:{user_input}"),
        ])

        chain = prompt | llm | self.json_parser

        try:
            parsed_event = chain.invoke({
                "session_context": self._get_gamestate_context_for_llm(),
                "valid_events": all_valid_events,
                "invalid_events": invalid_events,
                "user_input": player_input
            })
            return parsed_event
        except Exception as e:
            print(f"An error occurred during LLM interpretation: {e}")
            return {"type": "ERROR", "detail": "Failed to interpret input."}
        
    def validate_events(self, events: List[dict]) -> List[dict]:
        """
        Validate the interpreted events against the current game state.
        This function is scalable and validates events based on their subtype.
        """
        validated_events = []
        invalid_events = []

        # Get all valid connections from the current location
        current_location_data = self.gamestate.location_manager.get_location_data()
        valid_connections = current_location_data.get("connections", {})

        # Get all valid entity IDs (NPCs and Players) in the current scene
        npc_ids = list(self.gamestate.npc_manager.get_npc_data().keys())
        player_ids = list(self.gamestate.player_manager.get_player_data().keys())
        valid_entity_ids = set(npc_ids + player_ids)

        for event in events:
            subtype = event.get("subtype", "").upper()
            target_id = event.get("parameters", {}).get("target_id")
            is_valid = False

            if subtype == "MOVEMENT":
                # For MOVEMENT, target_id must be a value in the connections dict
                if target_id in valid_connections.values():
                    is_valid = True
                else:
                    event["validation_error"] = f"Invalid MOVEMENT target: '{target_id}'. Valid destinations are: {list(valid_connections.values())}"
            
            elif subtype in ["INTERACTION", "ATTACK", "INSPECT"]:
                # For these actions, target_id must be a valid entity in the scene
                if target_id in valid_entity_ids:
                    is_valid = True
                else:
                    event["validation_error"] = f"Invalid target_id: '{target_id}'. Target not found in the current scene. Valid targets are: {list(valid_entity_ids)}"

            elif not target_id:
                # Actions that don't require a target are considered valid by default
                is_valid = True
            
            else:
                # Fallback for any other action with a target_id
                # You might want to refine this for other subtypes
                if target_id in valid_entity_ids or target_id in valid_connections.values():
                    is_valid = True
                else:
                    event["validation_error"] = f"Generic invalid target_id: '{target_id}'"

            if is_valid:
                validated_events.append(event)
            else:
                invalid_events.append(event)

        return validated_events, invalid_events

    def process_and_validate_plan(self, player_input: str) -> dict:
        """
        Continuously process the player's input and validate events until all events are valid.
        Handles the new dictionary structure with 'player_actions' and 'system_actions'.
        """
        all_valid_player_actions = []
        all_system_actions = []
        invalid_player_actions = []
        
        # We'll give it a few tries to fix invalid actions
        for i in range(3): 
            # 1. Generate action plan (LLM)
            # On retries, we pass the invalid actions back to the LLM to fix.
            interpreted_plan = self.generate_action_plan(player_input, all_valid_player_actions, invalid_player_actions)
            print(f"Interpreted Plan (Attempt {i + 1}): {interpreted_plan}")

            if not isinstance(interpreted_plan, dict):
                print(f"Invalid format from LLM. Expected a dictionary, but got {type(interpreted_plan)}. Forcing regeneration...")
                player_input = "Your previous response was not a valid JSON dictionary with 'player_actions' and 'system_actions' keys. Please correct the format and try again."
                invalid_player_actions = [] # Clear previous invalid actions as this is a format error
                continue # Skip to the next loop iteration to retry

            # 2. Extract player and system actions from the dictionary
            player_actions = interpreted_plan.get("player_actions", [])
            
            # Only grab system actions on the first pass to avoid duplication
            if i == 0:
                all_system_actions = interpreted_plan.get("system_actions", [])
            
            # 3. Validate only the player actions
            valid_events, invalid_events = self.validate_events(player_actions)
            
            if valid_events:
                all_valid_player_actions.extend(valid_events)

            # 4. Check if there are any invalid events
            if not invalid_events:
                # If everything is valid, return the complete plan
                return {
                    "player_actions": all_valid_player_actions,
                    "system_actions": all_system_actions
                }
            
            print(f"Some events were invalid. Retrying interpretation... (Attempt {i + 1}/3)")
            # Prepare for retry
            player_input = "Please fix the following invalid events." # Give a more direct instruction
            invalid_player_actions = invalid_events

        # If it fails after retries, return what we have
        print("Failed to generate a fully valid plan after retries.")
        return {
            "player_actions": all_valid_player_actions,
            "system_actions": all_system_actions
        }

    def roll_tool(self, event: dict) -> dict:
        """
        Generalized roll tool for any event subtype (e.g., perception, athletics, stealth, etc.).
        Rolls a d20, applies the relevant modifier, and returns the result.
        """
        # Get the actor performing the check
        actor_id = event.get("actor_id")
        if not actor_id:
            return {"error": "No actor_id provided for roll."}

        # Find the actor in the current actors list
        actors = self.gamestate.player_manager.get_player_data()
        actor = actors.get(actor_id)
        if not actor:
            return {"error": f"Actor with id {actor_id} not found."}

        # Determine which modifier to use based on the event subtype
        subtype = event.get("subtype", "").lower()
        # Map subtypes to stat keys (customize as needed)
        subtype_to_stat = {
            "perception": "perception",
            "athletics": "athletics",
            "stealth": "stealth",
            "investigation": "investigation",
            "sleight_of_hand": "sleight_of_hand",
            "passive": "passive",
            "attack": "attack",
            "interaction": "interaction",
            "movement": "movement",
            "inventory": "inventory",
            # Add more mappings as needed
        }
        stat_key = subtype_to_stat.get(subtype, subtype)  # fallback to subtype as key

        # Get the modifier (default to 0 if not found)
        modifier = actor.get("stats", {}).get(stat_key, 0)

        # Roll a d20
        roll = random.randint(1, 20)
        total = roll + modifier

        # Determine DC (difficulty class), default to 2 if not provided
        dc = event.get("parameters", {}).get("action_dc", 2)

        result = {
            "actor_id": actor_id,
            "subtype": subtype,
            "roll": roll,
            "modifier": modifier,
            "total": total,
            "dc": dc,
            "success": total >= dc,
        }
        return result

    def execute_events(self, events: dict) -> dict:
        """
        Execute the validated events and update the game state accordingly.
        This is a placeholder function; replace it with actual game logic.
        """
        execution_results = []
        player_actions = events.get("player_actions", [])
        system_actions = events.get("system_actions", [])
        
        for event in player_actions:
                if event.get("subtype") == "MOVEMENT":
                    destination_id = event.get("parameters", {}).get("target_id")
                    if destination_id:
                        try:
                            self.gamestate.move_location(destination_id)
                            execution_results.append({"event": event, "result": f"Moved to {destination_id}"})
                        except ValueError as ve:
                            execution_results.append({"event": event, "result": str(ve)})
                
                if event.get("subtype") == "INTERACTION":
                    target_id = event.get("parameters", {}).get("target_id")
                    execution_results.append({"event": event, "result": f"Interacted with {target_id}"})

                elif event.get("subtype") in ["PERCEPTION", "ATHLETICS", "STEALTH", "INVESTIGATION", "SLEIGHT_OF_HAND", "ATTACK"]:
                    roll_result = self.roll_tool(event)
                    execution_results.append({"event": event, "result": roll_result})
                else:
                    execution_results.append({"event": event, "result": "Action executed."})
        
        for event in system_actions:
            if event.get("type") == "SYSTEM_ACTION":
                # example: {"type": "SYSTEM_ACTION", "subtype": "UPDATE", "parameters": {"target_id": "npc_GoblinWarrior", "key_path": ["knowledge", "revealed"], "value": true}}
                target_id = event.get("parameters", {}).get("target_id")
                if target_id and target_id.startswith("npc_"):
                    self.gamestate.npc_manager.update_npc_data(
                        npc_id=target_id,
                        key_path=event.get("parameters", {}).get("key_path", []),
                        value=event.get("parameters", {}).get("value") # Corrected from 'values'
                    )

        return execution_results

    def generate_narrative(self, user_input: str, validated_plan: List[dict], execution_results: List[dict], messages: List[dict]) -> str:
        """
        Generate a narrative description of the executed events.
        """
        try:
            with open("prompts.yaml", "r") as f:
                system_prompt = yaml.safe_load(f)["narrator_prompt"]
        except Exception as e:
            print(f"Error loading prompts.yaml: {e}")
            return "Error"
        
        llm = self._get_llm(max_tokens=4000)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{user_input}")
        ])

        chain = prompt | llm | self.json_parser

        max_retries = 5
        for attempt in range(max_retries):
            try:
                parsed_narrative = chain.invoke({
                    "user_input": user_input,
                    "validated_plan": validated_plan,
                    "execution_results": execution_results,
                    "session_context": self._get_gamestate_context_for_llm(),
                    "messages": messages  # Pass the history here
                })
                return parsed_narrative
            except Exception as e:
                print(f"An error occurred during LLM narration (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {"type": "ERROR", "detail": "Failed to generate narration after retries."}

    def validate_narrative(self, narrative: dict) -> dict:
        """
        Use an LLM to validate that the narrative is consistent with the game state.
        Returns True if the narrative is valid, False otherwise.
        """
        try:
            with open("prompts.yaml", "r") as f:
                system_prompt = yaml.safe_load(f)["validate_narrative_prompt"]
        except Exception as e:
            print(f"Error loading prompts.yaml: {e}")
            return {"Error": "Failed to load prompts."}

        llm = self._get_llm(max_tokens=2000)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{narrative}")
        ])

        chain = prompt | llm | self.json_parser

        try:
            result = chain.invoke({
                "narrative": narrative["narrative"],
                "session": self.gamestate.game_state["session"]
            })
            return narrative
        except Exception as e:
            print(f"An error occurred during narrative validation: {e}")
            return {"Error": "Failed to validate narrative."}

    def generate_narrative_audio(self, narrative: str):
        AUDIO_PROMPT_PATH = "resources/bg3narrator.wav"
        model = ChatterboxTTS.from_pretrained(device="cuda")
        try:
            audio = model.generate(narrative, audio_prompt_path=AUDIO_PROMPT_PATH)
        except Exception as e:
            print(f"Error generating audio: {e}")
            return
        # Save to a file
        ta.save("./response.wav", audio, model.sr, encoding="PCM_S", bits_per_sample=16)
        del model
        # torch.cpu.empty_cache()

    # def generate_narrative_audio(self, narrative: str):
    #     tts_client.speak(narrative, output_file="./response.wav")
    #     return

    def play_narrative_audio(self):
        AUDIO_FILE_PATH = "./response.wav"
        winsound.PlaySound(AUDIO_FILE_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return

    def run(self):
        # Update only relevant fields in the session
        # Example: set current scene (loads scene data into memory)
        #self.gamestate.set_scene("Havenwood")
        
        while True:
            print(colored(json.dumps(self._get_gamestate_context_for_llm(), indent=2), "cyan"))

            player_input = input(colored(">>> ", "yellow").strip())


            if player_input.lower() in ["exit", "quit"]:
                break

            # Track player input
            self.messages.append({"role": "player", "content": player_input})

            print("\n\n>>>>> INTERPRETED_INTENT <<<<<\n\n")
            try:
                interpreted_intent = self.interpret_user_intent(player_input)
                print(interpreted_intent)
                # Track interpreted intent
                self.messages.append({"role": "system", "content": f"Interpreted Intent: {interpreted_intent}"})
            except Exception as e:
                print(f"Error interpreting user intent: {e}")
                return
            print("\n\n>>>>> END INTERPRETED_INTENT <<<<<\n\n")
            
            print("\n\n>>>>> VALIDATED_PLAN <<<<<\n\n")
            try:
                validated_plan = self.process_and_validate_plan(interpreted_intent)
                print(validated_plan)
                # Track validated plan
                self.messages.append({"role": "system", "content": f"Validated Plan: {validated_plan}"})
            except Exception as e:
                print(f"Error interpreting input: {e}")
                return
            print("\n\n>>>>> END VALIDATED_PLAN <<<<<\n\n")
    
            print("\n\n>>>>> EXECUTION_RESULTS <<<<<\n\n")
            try:
                execution_results = self.execute_events(validated_plan)
                print(execution_results)
                # Track execution results
                self.messages.append({"role": "system", "content": f"Execution Results: {execution_results}"})
            except Exception as e:
                print(f"Error executing events: {e}")
                return
            print("\n\n>>>>> END EXECUTION_RESULTS <<<<<\n\n")

            print("\n\n>>>>> NARRATIVE <<<<<\n\n")
            try:
                narrative = self.generate_narrative(player_input, validated_plan, execution_results, self.messages)
                print(narrative)
                # Track narrative
                # self.messages.append({"role": "narrator", "content": narrative.get("narrative", str(narrative))})
            except Exception as e:
                print(f"Error generating narrative: {e}")
                return
            print("\n\n>>>>> END NARRATIVE <<<<<\n\n")
            
            print("\n\n>>>>> NARRATIVE AUDIO <<<<<\n\n")
            try:
                self.generate_narrative_audio(narrative.get("narrative", ""))
                self.play_narrative_audio()
            except Exception as e:
                print(f"Error with narrative audio: {e}")
                return
            print("\n\n>>>>> END NARRATIVE AUDIO <<<<<\n\n")
            
            # try:
            #     self.play_narrative_audio()
            # except Exception as e:
            #     print(f"Error playing narrative audio: {e}")
            #     return

            # try:
            #     narrative = self.validate_narrative(narrative)
            #     print("\n\n>>>>> VALIDATED NARRATIVE <<<<<\n\n", narrative, "\n\n>>>>> END VALIDATED NARRATIVE <<<<<\n\n")
            #     # Optionally track validated narrative
            # except Exception as e:
            #     print(f"Error validating narrative: {e}")
            #     return

            self.messages.append({"role": "system", "content": f"Validated Narrative: {narrative}"})

            print(colored(narrative, "green"))

            # Optionally, print the full message history for debugging
            # print(json.dumps(self.messages, indent=2))