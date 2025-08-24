# from langchain_ollama import OllamaLLM
# from langchain.chains import LLMChain
# from langchain.prompts import PromptTemplate
# from typing import TypedDict
# import json

# class DungeonMasterAgent:

#     def __init__(self, base_url: str, model: str):
#         self.llm = self.initialize_llm()
#         self.prompt = PromptTemplate(
#             input_variables=["context", "question"],
#             template="You are a Dungeon Master. {context}\n\nQuestion: {question}\nAnswer:"
#         )
#         self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

#     # Initialize the LLM
#     def initialize_llm(self):
#         try:
#             return OllamaLLM(base_url=self.base_url, model=self.model, max_tokens=2048, temperature=0.7)
#         except Exception as e:
#             print(f"error: {e}")
#             return None

#     def ask(self, context: str, question: str) -> str:
#         return self.chain.run(context=context, question=question)
    
#     def exposition(self, context: str) -> str:
#         return self.llm.invoke(context)
    
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Dict, List, Any
from langchain_ollama import OllamaLLM
import toml

class DungeonMasterAgent:

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model
        self.llm = self.initialize_llm()
        self.prompts = self.load_prompts_from_file("prompt.toml")
        self.game_graph = self.create_game_graph()

    def load_prompts_from_file(self, file_path: str) -> Dict[str, str]:
        try:
            with open(file_path, "r") as file:
                return toml.load(file)
        except Exception as e:
            print(f"Error loading prompts from {file_path}: {e}")
            return {}

    def initialize_llm(self):
        try:
            return OllamaLLM(base_url=self.base_url, model=self.model, max_tokens=2048, temperature=0.7)
        except Exception as e:
            print(f"error: {e}")
            return None

    def create_game_graph(self):
        # Define the state schema
        class GameState(TypedDict):
            context: str
            current_player_input: str
            intent: str
            response: str
            history: List[Dict[str, str]]

        # Create nodes for your graph
        def recognize_intent(state: GameState):
            # Logic to recognize intent using your existing intent agent
            response = self.llm.invoke(str.format(self.prompts["intent_recognition"], context=state["context"], question=state["current_player_input"]))
            state["intent"] = response
            return state

        def handle_dm_question(state: GameState):
            # Logic to handle DM questions
            state["response"] = "DM response"
            return state

        def handle_action(state: GameState):
            # Logic to handle character actions
            state["response"] = "Action result"
            return state

        # Define the graph
        game_graph = StateGraph(GameState)

        # Add nodes
        game_graph.add_node("intent_recognition", recognize_intent)
        game_graph.add_node("dm_question", handle_dm_question)
        game_graph.add_node("character_action", handle_action)

        # Add edges
        game_graph.add_edge("intent_recognition", "dm_question")
        game_graph.add_conditional_edges(
            "intent_recognition",
            lambda state: state["recognized_intent"],
            {
                "ask_dm": "dm_question",
                "character_action": "character_action"
            }
        )

        # Set starting node
        game_graph.set_entry_point("intent_recognition")

        # Edges from result nodes to END
        game_graph.add_edge("dm_question", END)
        game_graph.add_edge("character_action", END)

        # Compile the graph
        return game_graph.compile()

    def run_game(self, initial_state: Dict[str, Any]):
        return self.game_graph.run(initial_state)