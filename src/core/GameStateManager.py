import os
import json
import yaml
from datetime import datetime
import logging
import termcolor
from typing import Union

# Location Manager
class LocationManager:
    #load location data from a JSON file based on id that matches file name
    def __init__(self, base_path:str="data/locations", location_id:str=None):
        self.loc_file_path = os.path.join(base_path, f"{location_id}.json")
        self.location_data = self.load_location_data()
        self.valid_ids = self.location_data.get("connections", []).copy()

    def load_location_data(self):
        """
        Load location data from a JSON file.
        """
        if os.path.exists(self.loc_file_path):
            with open(self.loc_file_path, 'r') as file:
                return json.load(file)
        else:
            logging.warning(f"Location file {self.loc_file_path} not found.")
            return {}
        
    def get_location_data(self):
        """
        Get the loaded location data.
        """
        return self.location_data
    
    def __str__(self):
        return json.dumps(self.location_data, indent=2)
    
class NPCManager:
    def __init__(self, base_path:str="data/npcs", npc_ids:list[str]=None):
        self.base_path = base_path
        self.npc_ids = npc_ids if npc_ids else []
        self.npc_data = self.load_npc_data()

    def load_npc_data(self)->dict:
        """
        Load NPC data from a JSON file.
        """
        npc_data = {}
        for npc_id in self.npc_ids:
            npc_file_path = os.path.join(self.base_path, f"{npc_id}.json")
            if os.path.exists(npc_file_path):
                with open(npc_file_path, 'r') as file:
                    npc_data[npc_id] = json.load(file)
            else:
                logging.warning(f"NPC file {npc_file_path} not found.")
        return npc_data
    
    def get_npc_data(self)->dict:
        """
        Get the loaded NPC data.
        """
        return self.npc_data
    
    def update_npc_data(self, npc_id:str, key_path:list[str], value:Union[str, int, bool, dict, list])->None:
        """
        Update a specific field in an NPC's data.
        Args:
            npc_id (str): The ID of the NPC to update.
            key_path (list[str]): The path of keys to navigate to the target field.
            value (Union[str, int, bool, dict, list]): The value to set at the target field.
        """
        if npc_id not in self.npc_data:
            logging.error(f"NPC ID {npc_id} not found in loaded data.")
            return
        
        target = self.npc_data[npc_id] # get the NPC data dict
        for key in key_path[:-1]:
            target = target.setdefault(key, {})
        
        target[key_path[-1]] = value
    
    def __str__(self):
        return json.dumps(self.npc_data, indent=2)
    
class PlayerManager:
    def __init__(self, base_path:str="data/players", player_ids:list[str]=None):
        self.base_path = base_path
        self.player_ids = player_ids if player_ids else []
        self.player_data = self.load_player_data()

    def load_player_data(self)->dict:
        """
        Load Player data from a JSON file.
        """
        player_data = {}
        for player_id in self.player_ids:
            player_file_path = os.path.join(self.base_path, f"{player_id}.json")
            if os.path.exists(player_file_path):
                with open(player_file_path, 'r') as file:
                    player_data[player_id] = json.load(file)
            else:
                logging.warning(f"Player file {player_file_path} not found.")
        return player_data
    
    def get_player_data(self)->dict:
        """
        Get the loaded Player data.
        """
        return self.player_data
    

class GameSessionManager:

    def __init__(self, base_path:str="data/sessions", session_id:str="session"):
        self.session_file_path = os.path.join(base_path, f"{session_id}.json")
        self.session_data = self.load_session_data()
        self.location_manager = None
        self.npc_manager = None
        self.player_manager = None
    
    def load_session_data(self)->dict:
        """
        Load session data from a JSON file.
        """
        if os.path.exists(self.session_file_path):
            with open(self.session_file_path, 'r') as file:
                return json.load(file)
        else:
            logging.warning(f"Session file {self.session_file_path} not found.")
            return {}
        
    def init_session_managers(self):
        # Initialize all session-related managers.
        # -- Location Manager --
        self.init_location_manager()

        # -- NPC Manager --
        self.init_npc_manager()

        # -- Player Manager --
        self.init_player_manager()

        # -- Other managers can be initialized here --

    def init_location_manager(self)->None:
        """
        Initialize the Location Manager with the current location ID.
        """
        location_id = self.session_data.get("location_id", None)
        if location_id:
            self.location_manager = LocationManager(location_id=location_id)
        else:
            raise ValueError(f"Location ID not found in session data. {location_id}")
        
    def init_npc_manager(self)->None:
        """
        Initialize the NPC Manager with the current NPC IDs.
        """
        npc_ids = self.location_manager.get_location_data().get("npcs", [])
        if npc_ids:
            self.npc_manager = NPCManager(npc_ids=npc_ids)
        else:
            raise ValueError(f"NPC IDs not found in session data. {npc_ids}")
    
    def init_player_manager(self)->None:
        """
        Initialize the Player Manager with the current Player IDs.
        """
        player_ids = self.session_data.get("players", [])
        if player_ids:
            self.player_manager = PlayerManager(player_ids=player_ids)
        else:
            raise ValueError(f"Player IDs not found in session data. {player_ids}")
        
    def save_session_data(self)->None:
        """
        Save the current session data back to the JSON file.
        """
        try:
            with open(self.session_file_path, 'w') as file:
                json.dump(self.session_data, file, indent=2)
        except Exception as e:
            logging.error(f"Failed to save session data: {e}")

    def get_session_data(self)->dict:
        """
        Get the loaded session data.
        """
        return self.session_data

    def move_location(self, new_location_id:str)->None:
        """
        Update the current location in the session data and reinitialize the Location Manager.
        """
        try:
            # 1. Update the session data with the new location ID
            self.session_data["location_id"] = new_location_id
            # 2. Reinitialize the Location Manager
            self.init_location_manager()
            # 3. Reinitialize the NPC Manager based on the new location
            self.init_npc_manager()
            # 4. Save the updated session data
            # self.save_session_data()
            
        except Exception as e:
            logging.error(f"Failed to update location: {e}")

    def __str__(self):
        return json.dumps(self.session_data, indent=2)

#singleton instance for global access
game_session_manager = GameSessionManager(session_id="session")
game_session_manager.init_session_managers()


# def main():
#     # Example usage
#     session_manager = GameSessionManager(session_id="session")
#     session_manager.init_session_managers()

#     print("Initial Session Data:")
#     print(session_manager)
#     print("\nLocation Data:")
#     print(session_manager.location_manager)
#     print("\nNPC Data:")
#     print(session_manager.npc_manager)

#     # Example of updating the location
#     session_manager.update_location("loc_Gloomwood")

#     print(termcolor.colored("\nUpdated Session Data:", "green"))
#     print(termcolor.colored(session_manager, "green"))
#     print(termcolor.colored("\nUpdated Location Data:", "yellow"))
#     print(termcolor.colored(session_manager.location_manager, "yellow"))
#     print(termcolor.colored("\nUpdated NPC Data:", "cyan"))
#     print(termcolor.colored(session_manager.npc_manager, "cyan"))


# if __name__ == "__main__":
#     main()