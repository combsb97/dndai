import random
import winsound
import yaml
import json
from termcolor import colored
from typing import TypedDict, List, Annotated, Dict
import operator
import torch
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS
import langchain
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, START, END
from game_state import gamestate

langchain.verbose = True

# --- 1. Agent State Definition ---
# This class defines the "state" that is passed between all the nodes in our graph.
# It remains unchanged as it's the core data structure for the agent.
class AgentState(TypedDict):
    """The state passed between nodes in the graph."""
    game_state: dict
    player_input: str


# --- 2. LLM Interface Functions (TO BE IMPLEMENTED) ---
# This is where you will integrate your Ollama and LangChain code.

def interpret_user_intent(player_input: str) -> str:
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
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "## Raw User Input: {user_input}"),
    ])

    LLM = ChatOllama(base_url="http://localhost:11434", model="mistral", temperature=0.7, keep_alive=0)
    output_parser = JsonOutputParser()
    chain = prompt | LLM | output_parser

    try:
        parsed_intent = chain.invoke({
            "user_input": player_input
        })
        return parsed_intent
    except Exception as e:
        print(f"An error occurred during LLM intent interpretation: {e}")
        return {"type": "ERROR", "detail": "Failed to interpret intent."}

def interpret_player_input(player_input: str, invalid_events: List[dict]) -> str:
    """
    Use an LLM to interpret the player's input and determine the next action.
    This is a placeholder function; replace it with actual LLM integration.
    """
    try:
        with open("prompts.yaml", "r") as f:
            system_prompt = yaml.safe_load(f)["interpreter_prompt"]
    except Exception as e:
        print(f"Error loading prompts.yaml: {e}")
        return "Error"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "## Parsed User Input:{user_input}"),
    ])

    LLM = ChatOllama(base_url="http://localhost:11434", model="mistral", temperature=0.7, keep_alive=0)
    output_parser = JsonOutputParser()
    chain = prompt | LLM | output_parser

    try:
        parsed_event = chain.invoke({
            "session": gamestate.game_state["session"],
            "invalid_events": invalid_events,
            "user_input": player_input
        })
        return parsed_event
    except Exception as e:
        print(f"An error occurred during LLM interpretation: {e}")
        return {"type": "ERROR", "detail": "Failed to interpret input."}
    
def validate_events(events: List[dict]) -> List[dict]:
    """
    Validate the interpreted events against the current game state.
    This function traverses the game state JSON recursively to check for valid targets.
    """
    def traverse_json(data, target_id):
        """
        Recursively traverse the JSON-like dictionary to find the target_id.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if key == target_id or value == target_id or traverse_json(value, target_id):
                    return True
        elif isinstance(data, list):
            for item in data:
                if traverse_json(item, target_id):
                    return True
        return False

    validated_events = []
    invalid_events = []
    for event in events:
        target_id = event.get("parameters", {}).get("target_id")
        if target_id and traverse_json(gamestate.game_state["session"], target_id):
            validated_events.append(event)
        elif target_id and not traverse_json(gamestate.game_state["session"], target_id):
            event["validation_error"] = f"Invalid target_id: {target_id}"
            invalid_events.append(event)
        else:
            validated_events.append(event)

    print(f"Validated Events: {validated_events}")
    print(f"Invalid Events: {invalid_events}")
    return validated_events, invalid_events

def process_player_input(player_input: str) -> List[dict]:
    """
    Continuously process the player's input and validate events until all events are valid.
    """
    invalid_events = []
    while True:
        interpreted_events = interpret_player_input(player_input, invalid_events)
        if isinstance(interpreted_events, dict) or isinstance(interpreted_events, str):
            interpreted_events = [interpreted_events]
        valid_events, invalid_events = validate_events(interpreted_events)
        if len(valid_events) == len(interpreted_events):
            return valid_events
        print("Some events were invalid. Retrying interpretation...")

def roll_tool(event: dict) -> dict:
    """
    Generalized roll tool for any event subtype (e.g., perception, athletics, stealth, etc.).
    Rolls a d20, applies the relevant modifier, and returns the result.
    """
    # Get the actor performing the check
    actor_id = event.get("actor_id")
    if not actor_id:
        return {"error": "No actor_id provided for roll."}

    # Find the actor in the current actors list
    actors = gamestate.game_state.get("actors", {}).get("pcs", {})
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

def execute_events(events: List[dict]) -> dict:
    """
    Execute the validated events and update the game state accordingly.
    This is a placeholder function; replace it with actual game logic.
    """
    execution_results = []
    for event in events:
        if event.get("type") == "PLAYER_ACTION":
            if event.get("subtype") == "MOVEMENT":
                destination_id = event.get("parameters", {}).get("target_id")
                if destination_id:
                    try:
                        gamestate.set_session_location_by_key(destination_id)
                        gamestate.set_current_actors_by_location_id(destination_id)
                        execution_results.append({"event": event, "result": f"Moved to {destination_id}"})
                    except ValueError as ve:
                        execution_results.append({"event": event, "result": str(ve)})
            
            elif event.get("subtype") in ["PERCEPTION", "ATHLETICS", "STEALTH", "INVESTIGATION", "SLEIGHT_OF_HAND", "ATTACK"]:
                roll_result = roll_tool(event)
                execution_results.append({"event": event, "result": roll_result})
            else:
                execution_results.append({"event": event, "result": "Action executed."})

    return execution_results

def generate_narrative(user_input: str, validated_plan: List[dict], execution_results: List[dict], messages: List[dict]) -> str:
    """
    Generate a narrative description of the executed events.
    """
    try:
        with open("prompts.yaml", "r") as f:
            system_prompt = yaml.safe_load(f)["narrator_prompt"]
    except Exception as e:
        print(f"Error loading prompts.yaml: {e}")
        return "Error"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{user_input}")
    ])

    LLM = ChatOllama(base_url="http://localhost:11434", model="llama3.1:8b", temperature=0.7, keep_alive=0)
    output_parser = JsonOutputParser()
    chain = prompt | LLM | output_parser

    max_retries = 5
    for attempt in range(max_retries):
        try:
            parsed_narrative = chain.invoke({
                "user_input": user_input,
                "validated_plan": validated_plan,
                "execution_results": execution_results,
                "session": gamestate.game_state["session"],
                "messages": messages  # Pass the history here
            })
            return parsed_narrative
        except Exception as e:
            print(f"An error occurred during LLM narration (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                return {"type": "ERROR", "detail": "Failed to generate narration after retries."}

def validate_narrative(narrative: dict) -> dict:
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

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "{narrative}")
    ])

    LLM = ChatOllama(base_url="http://localhost:11434", model="llama3.1:8b", temperature=0.7, keep_alive=0)

    output_parser = JsonOutputParser()
    chain = prompt | LLM | output_parser

    try:
        result = chain.invoke({
            "narrative": narrative["narrative"],
            "session": gamestate.game_state["session"]
        })
        return narrative
    except Exception as e:
        print(f"An error occurred during narrative validation: {e}")
        return {"Error": "Failed to validate narrative."}

def generate_narrative_audio(narrative: str):
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
    torch.cuda.empty_cache()

def play_narrative_audio():
    AUDIO_FILE_PATH = "./response.wav"
    winsound.PlaySound(AUDIO_FILE_PATH, winsound.SND_FILENAME | winsound.SND_ASYNC)
    return

def main():
    # Update only relevant fields in the session
    gamestate.set_session_location_by_key("loc_Havenwood")
    gamestate.set_current_actors_by_location_id("loc_Havenwood")
    
    messages = []  # <-- Track message history here

    while True:
        print(colored(json.dumps(gamestate.game_state["session"], indent=2), "cyan"))

        player_input = input(colored(">>> ", "yellow").strip())

        if player_input.lower() in ["exit", "quit"]:
            break

        # Track player input
        messages.append({"role": "player", "content": player_input})

        try:
            interpreted_intent = interpret_user_intent(player_input)
            print("\n\n>>>>> INTERPRETED_INTENT <<<<<\n\n", interpreted_intent, "\n\n>>>>> END INTERPRETED_INTENT <<<<<\n\n")
            # Track interpreted intent
            messages.append({"role": "system", "content": f"Interpreted Intent: {interpreted_intent}"})
        except Exception as e:
            print(f"Error interpreting user intent: {e}")
            return
        
        try:
            validated_plan = process_player_input(interpreted_intent)
            print("\n\n>>>>> VALIDATED_PLAN <<<<<\n\n", validated_plan, "\n\n>>>>> END VALIDATED_PLAN <<<<<\n\n")
            # Track validated plan
            messages.append({"role": "system", "content": f"Validated Plan: {validated_plan}"})
        except Exception as e:
            print(f"Error interpreting input: {e}")
            return

        try:
            execution_results = execute_events(validated_plan)
            print("\n\n>>>>> EXECUTION_RESULTS <<<<<\n\n", execution_results, "\n\n>>>>> END EXECUTION_RESULTS <<<<<\n\n")
            # Track execution results
            messages.append({"role": "system", "content": f"Execution Results: {execution_results}"})
        except Exception as e:
            print(f"Error executing events: {e}")
            return

        try:
            narrative = generate_narrative(player_input, validated_plan, execution_results, messages)
            print("\n\n>>>>> NARRATIVE <<<<<\n\n", narrative, "\n\n>>>>> END NARRATIVE <<<<<\n\n")
            # Track narrative
            # messages.append({"role": "narrator", "content": narrative.get("narrative", str(narrative))})
        except Exception as e:
            print(f"Error generating narrative: {e}")
            return
        
        # try:
        #     generate_narrative_audio(narrative.get("narrative", ""))
        #     play_narrative_audio()
        # except Exception as e:
        #     print(f"Error with narrative audio: {e}")
        #     return
        
        # try:
        #     play_narrative_audio()
        # except Exception as e:
        #     print(f"Error playing narrative audio: {e}")
        #     return

        # try:
        #     narrative = validate_narrative(narrative)
        #     print("\n\n>>>>> VALIDATED NARRATIVE <<<<<\n\n", narrative, "\n\n>>>>> END VALIDATED NARRATIVE <<<<<\n\n")
        #     # Optionally track validated narrative
        # except Exception as e:
        #     print(f"Error validating narrative: {e}")
        #     return

        messages.append({"role": "system", "content": f"Validated Narrative: {narrative}"})

        print(colored(narrative, "green"))

        # Optionally, print the full message history for debugging
        # print(json.dumps(messages, indent=2))


if __name__ == "__main__":
    main() 