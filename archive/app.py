import json
import inspect
import copy
import random
import re
import torch
import winsound
import torchaudio as ta
from termcolor import colored
from typing import Annotated, Sequence, TypedDict, Dict, Any, List
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
)
from langchain_ollama import ChatOllama
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langgraph.prebuilt import InjectedState, ToolNode
from chatterbox.tts import ChatterboxTTS

# Constants
LLM_MODEL = "llama3.1:8b"
LLM_BASE_URL = "http://localhost:11434"
MAX_TOKENS = 2048
TEMPERATURE = 0.7
AUDIO_PROMPT_PATH = "./resources/bg3narrator.wav"

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    game_state: dict

@tool
def update_game_state_by_key(
    state: Annotated[AgentState, InjectedState],
    path: list[str],
    new_value: Any,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    """
    Updates a specific key in the game state with a new value.
    Parameters:
        path (list[str]): The path to the key in the game state to update.
        new_value (Any): The new value to set for the specified key.
        state (AgentState): The current state of the agent.
    example:
        path = ["nearby_npcs", "values", 0, "hp", "29"]
    """
    gs = state["game_state"]
    obj = gs
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = new_value
    return Command(
        update={
            "game_state": gs,
            "messages": [
                ToolMessage(
                    content=f"Updated game state path: {'.'.join(path)}",
                    tool_call_id=tool_call_id,
                )
            ],
        }
    )

class TTSManager:
    def __init__(self, device: str = "cuda", audio_prompt_path: str = AUDIO_PROMPT_PATH):
        self.device = device if torch.cuda.is_available() else "cpu"
        self.audio_prompt_path = audio_prompt_path
        self.tts_model = ChatterboxTTS.from_pretrained(device=self.device)

    def generate_and_play(self, text: str, filename: str) -> None:
        wav = self.tts_model.generate(text, audio_prompt_path=self.audio_prompt_path)
        ta.save(filename, wav, self.tts_model.sr, encoding="PCM_S", bits_per_sample=16)
        del wav
        unload_gpu_resources()
        winsound.PlaySound(filename, winsound.SND_FILENAME | winsound.SND_ASYNC)

class AdventureApp:
    def __init__(self):
        self.agent = Agent()
        self.tts = TTSManager()
        self.state = AgentState(
            messages=[],
            game_state={
                "current_location": {
                    "description": "The current location of the player characters.",
                    "value": "In the seedy tavern 'The Drunken Dragon' in the city of Eldoria.",
                },
                "nearby_npcs": {
                    "description": "A list of notable NPCs currently near the player characters.",
                    "values": [
                        {"name": "Grog the Barkeep", "description": "The gruff owner of 'The Drunken Dragon', always ready with a drink.", "hp": "30", "status": "healthy", "personality": "gruff, friendly, cautious", "motivation": "to serve drinks and keep the peace [known to the player]"},
                        {"name": "Mysterious Stranger", "description": "A hooded figure in the corner, watching the room intently.", "hp": "20", "status": "healthy", "personality": "secretive, observant", "motivation": ""},
                    ]
                },
            }
        )
        self.turn_counter = 1
        self.start_index = 0

    def run(self):
        print("Welcome to the D&D adventure! Type 'exit' to quit.\n")
        starting_message = HumanMessage(
            content=(
                "Narrate the beginning of the session as the Dungeon Master. "
                f"Use ONLY the game state information provided in the initial state: {json.dumps(self.state['game_state'], indent=2)}."
            )
        )
        self.state["messages"].append(starting_message)
        outputs = graph.invoke(self.state)
        initial_msg = outputs["messages"][-1]
        serialized_msg = serialize_message(initial_msg)
        print(colored(json.dumps(serialized_msg, indent=2), "light_blue"))
        narration = outputs["messages"][-1].content
        self.tts.generate_and_play(narration, "./response.wav")
        self.turn_counter = 1
        self.start_index = len(self.state["messages"])
        while True:
            user_input = input("You: ")
            if user_input.lower() == "exit":
                print("Exiting the adventure. Goodbye!")
                unload_gpu_resources()
                break
            self.state["messages"].append(HumanMessage(content=user_input))
            outputs = graph.invoke(self.state)
            print(colored("\n" + "="*15 + f" Turn {self.turn_counter} Summary " + "="*15, "white", attrs=["bold"]))
            new_msg = outputs["messages"][self.start_index:]
            for msg in new_msg:
                if isinstance(msg, HumanMessage):
                    print(colored(f"User: {msg.content}", "light_green"))
                elif isinstance(msg, AIMessage):
                    print(colored(f"DM: {msg.content.strip()}", "light_blue"))
                elif isinstance(msg, ToolMessage):
                    print(colored(f"Tool Msg: {msg}", "light_yellow"))
            self.state = outputs
            self.turn_counter += 1
            self.start_index = len(self.state["messages"])
            print(colored("Current Game State:", "cyan", attrs=["bold"]))
            print(colored(json.dumps(self.state["game_state"], indent=2), "cyan"))

            ai_response = outputs["messages"][-1].content
            self.tts.generate_and_play(ai_response, f"./response{self.turn_counter}.wav")

@tool
def roll_dice(formula:str, mode:str="normal") -> str:
    """
    Classification: Mechanics
    Description: Rolls dice based on the NdN+/-N formula, e.g., 2d6+1. 
                 Supports optional modes: normal, advantage, and disadvantage.
    Parameters:
        formula (str): The dice roll formula in NdN+/-N format.
        mode (str): The rolling mode. Options are "normal", "advantage", or "disadvantage". Default is "normal".
    Returns:
        str: The result of the dice roll as a string.
    """
    import random
    import re

    # parse the formula
    match = re.match(r'(\d)[d](\d)([+-]\d)', formula)
    if not match:
        return "Invalid formula"
    n, d, mod = int(match.groups())

    if mode == "normal":
        total = sum([random.randint(1, d) for _ in range(n)]) + mod
        return str(total)
    elif mode == "advantage":
        total = max([sum(random.randint(1, d) for _ in range(n)) for _ in range(2)]) + mod
        return str(total)
    elif mode == "disadvantage":
        total = min([sum(random.randint(1, d) for _ in range(n)) for _ in range(2)]) + mod
        return str(total)
    

class Agent:
    def __init__(self, model=LLM_MODEL, base_url=LLM_BASE_URL, max_tokens=MAX_TOKENS, temperature=TEMPERATURE):
        self.llm = ChatOllama(base_url=base_url, model=model, max_tokens=max_tokens, temperature=temperature, keep_alive=0)
        self.tools = [update_game_state_by_key, roll_dice]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.tool_node = ToolNode(self.tools)

    def llm_node(self, state: AgentState, config: RunnableConfig) -> dict:
        system_prompt = SystemMessage(
            content="""
            You are a skilled and creative Dungeon Master orchestrating an engaging D&D campaign.
            ...existing code...
            Game State Keys and Descriptions:
            """ + json.dumps({k: state["game_state"][k]["description"] for k in state["game_state"]}, indent=2)
        )
        print(colored("@llm_node", "yellow"))
        print(colored(system_prompt, "yellow"))
        response = self.llm_with_tools.invoke([system_prompt] + state["messages"], config)
        return {"messages": [response]}

#================================================#
# EDGES                                          #
#================================================#
def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    return "continue"


#================================================#
# GRAPH                                          #
#================================================#
workflow = StateGraph(AgentState)

# workflow.add_node("campaign_start", campaign_start_node)
agent_instance = Agent()
workflow.add_node("agent", agent_instance.llm_node)
workflow.add_node("tools", agent_instance.tool_node)

#workflow.set_entry_point("campaign_start")

#workflow.add_edge("campaign_start", "agent")

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": END,
    }
)

workflow.add_edge("tools", "agent")

graph = workflow.compile()

from IPython.display import Image, display

try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception as e:
    print(f"Could not display graph visualization: {e}")

def serialize_message(msg: BaseMessage) -> dict[str, Any]:
    """Turn any LC message into a plain dict so we can pretty-print everything."""
    base = {
        "type": msg.__class__.__name__,
        "content": msg.content,
    }
    # Common optional fields
    if hasattr(msg, "name") and getattr(msg, "name"):
        base["name"] = msg.name
    if isinstance(msg, AIMessage):
        # tool_calls, response_metadata, etc.
        if getattr(msg, "tool_calls", None):
            base["tool_calls"] = msg.tool_calls
        if getattr(msg, "response_metadata", None):
            base["response_metadata"] = msg.response_metadata
    if isinstance(msg, ToolMessage):
        base["tool_call_id"] = msg.tool_call_id
    if getattr(msg, "additional_kwargs", None):
        base["additional_kwargs"] = msg.additional_kwargs
    return base

def pp_json(obj: Any) -> str:
    """Pretty-print JSON or fallback to string."""
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)

def unload_gpu_resources():
    """Utility function to unload GPU resources."""
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()

def main():
    """Main loop for D&D adventure agent."""
    unload_gpu_resources()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts_model = ChatterboxTTS.from_pretrained(device=device)
    state = AgentState(
        messages=[],
        game_state={
            "current_location": {
                "description": "The current location of the player characters.",
                "value": "In the seedy tavern 'The Drunken Dragon' in the city of Eldoria.",
            },
            "nearby_npcs": {
                "description": "A list of notable NPCs currently near the player characters.",
                "values": [
                    {"name": "Grog the Barkeep", "description": "The gruff owner of 'The Drunken Dragon', always ready with a drink.", "hp": "30", "status": "healthy", "personality": "gruff, friendly, cautious", "motivation": "to serve drinks and keep the peace [known to the player]"},
                    {"name": "Mysterious Stranger", "description": "A hooded figure in the corner, watching the room intently.", "hp": "20", "status": "healthy", "personality": "secretive, observant", "motivation": ""},
                ]
            },
        }
    )
    print("Welcome to the D&D adventure! Type 'exit' to quit.\n")
    starting_message = HumanMessage(
        content=(
            "Narrate the beginning of the session as the Dungeon Master. "
            f"Use ONLY the game state information provided in the initial state: {json.dumps(state['game_state'], indent=2)}."
        )
    )
    state["messages"].append(starting_message)
    outputs = graph.invoke(state)
    initial_msg = outputs["messages"][-1]
    serialized_msg = serialize_message(initial_msg)
    print(colored(json.dumps(serialized_msg, indent=2), "light_blue"))
    narration = outputs["messages"][-1].content
    wav = tts_model.generate(narration, audio_prompt_path=AUDIO_PROMPT_PATH)
    ta.save("./response.wav", wav, tts_model.sr, encoding="PCM_S", bits_per_sample=16)
    del wav
    unload_gpu_resources()
    winsound.PlaySound("./response.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
    turn_counter = 1
    start_index = len(state["messages"])
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Exiting the adventure. Goodbye!")
            unload_gpu_resources()
            break
        state["messages"].append(HumanMessage(content=user_input))
        outputs = graph.invoke(state)
        print(colored("\n" + "="*15 + f" Turn {turn_counter} Summary " + "="*15, "white", attrs=["bold"]))
        new_msg = outputs["messages"][start_index:]
        for msg in new_msg:
            if isinstance(msg, HumanMessage):
                print(colored(f"User: {msg.content}", "light_green"))
            elif isinstance(msg, AIMessage):
                print(colored(f"DM: {msg.content.strip()}", "light_blue"))
            elif isinstance(msg, ToolMessage):
                print(colored(f"Tool Msg: {msg}", "light_yellow"))
        state = outputs
        turn_counter += 1
        start_index = len(state["messages"])
        print(colored("Current Game State:", "cyan", attrs=["bold"]))
        print(colored(json.dumps(state["game_state"], indent=2), "cyan"))
        ai_response = outputs["messages"][-1].content
        wav = tts_model.generate(ai_response, audio_prompt_path=AUDIO_PROMPT_PATH)
        ta.save(f"./response{turn_counter}.wav", wav, tts_model.sr, encoding="PCM_S", bits_per_sample=16)
        del wav
        unload_gpu_resources()
        winsound.PlaySound(f"./response{turn_counter}.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
        unload_gpu_resources()