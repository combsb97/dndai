import os
import json
import yaml
from datetime import datetime
import logging

### --- GameStateManager and Entity Managers ---

class LocationManager:
    """
    Handles loading and accessing location data by ID.
    """
    def __init__(self, state_dir, location_id):
        self.state_dir = state_dir
        self.location_id = location_id
        self.data = self._load_location(location_id)

    def _id_to_path(self, location_id):
        return os.path.join(self.state_dir, f"{location_id}.json")

    def _load_location(self, location_id):
        path = self._id_to_path(location_id)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def get_npc_ids(self):
        # Assumes location data has an 'npcs' dict or list of IDs
        npcs = self.data.get("npcs", {})
        if isinstance(npcs, dict):
            return list(npcs.keys())
        elif isinstance(npcs, list):
            return npcs
        return []

    def get_location_data(self):
        return self.data

    def save(self):
        path = self._id_to_path(self.location_id)
        with open(path, "w") as f:
            json.dump(self.data, f, indent=2)


class NPCManager:
    """
    Handles loading and accessing NPC data by ID.
    """
    def __init__(self, state_dir, npc_ids):
        self.state_dir = state_dir
        self.npc_ids = npc_ids
        self.npcs = self._load_npcs(npc_ids)

    def _id_to_path(self, npc_id):
        # Convention: npc_{id}.json
        return os.path.join(self.state_dir, f"{npc_id}.json")

    def _load_npcs(self, npc_ids):
        npcs = {}
        for npc_id in npc_ids:
            path = self._id_to_path(npc_id)
            if os.path.exists(path):
                with open(path, "r") as f:
                    npcs[npc_id] = json.load(f)
            else:
                npcs[npc_id] = {}  # Empty if missing
        return npcs

    def get_npc(self, npc_id):
        return self.npcs.get(npc_id)

    def get_all_npcs(self):
        return self.npcs

    def save(self):
        for npc_id, data in self.npcs.items():
            path = self._id_to_path(npc_id)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)

    def get_npc_name(self, npc_id):
        npc = self.get_npc(npc_id)
        return npc.get("name", {}) if npc else {}


class GameStateManager:   
    """
    Hybrid in-memory and file-based persistent game state manager.
    session.json lists all state modules by ID (e.g., players, location, quests).
    The manager maps these IDs to file paths and loads/persists state accordingly.
    session.json is the single source of truth for the current game state.
    """
    def __init__(self, config_path="state_config.yaml", state_dir="state_data", log_path="state.log", session_path=None):
        self.state_dir = state_dir
        self.log_path = log_path
        self.session_path = session_path or os.path.join(self.state_dir, "session.json")
        os.makedirs(self.state_dir, exist_ok=True)
        self.memory_state = {}
        self.session = {}
        self.config = self._load_config(config_path)
        self.location_manager = None
        self.npc_manager = None
        self._load_session()

    def __str__(self):
        return f"<GameStateManager scene={self.scene} memory_keys={list(self.memory_state.keys())}>"

    def _load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        # Default config: everything in memory
        return {"default": {"players": "memory", "npcs": "on_demand", "items": "on_demand"}}

    def _get_scene_config(self, location_id):
        # Config overrides can be keyed by location ID
        return self.config.get(f"scene:{location_id}", self.config.get("default", {}))

    def _id_to_path(self, module_id):
        """
        Map a module ID to its file path. E.g., 'players' -> 'state_data/players.json',
        'loc_Havenwood' -> 'state_data/loc_Havenwood.json', 'main_quest' -> 'state_data/main_quest.json'.
        """
        if module_id.startswith("loc_"):
            return os.path.join(self.state_dir, f"{module_id}.json")
        else:
            return os.path.join(self.state_dir, f"{module_id}.json")

    def _load_session(self):
        # Load session.json and all referenced modules into memory_state
        self.memory_state = {}
        if os.path.exists(self.session_path):
            with open(self.session_path, "r") as f:
                self.session = json.load(f)
            for module, module_id in self.session.items():
                path = self._id_to_path(module_id)
                if os.path.exists(path):
                    with open(path, "r") as mf:
                        self.memory_state[module] = json.load(mf)
                else:
                    self.memory_state[module] = {}  # Initialize empty if missing
            # Set up managers
            location_id = self.session.get("location")
            self.scene = location_id
            if location_id:
                self.location_manager = LocationManager(self.state_dir, location_id)
                npc_ids = self.location_manager.get_npc_ids()
                self.npc_manager = NPCManager(self.state_dir, npc_ids)
            else:
                self.location_manager = None
                self.npc_manager = None
        else:
            self.session = {}
            self.scene = None
            self.location_manager = None
            self.npc_manager = None

    def _save_session(self):
        # Save the current session.json (IDs for all modules)
        with open(self.session_path, "w") as f:
            json.dump(self.session, f, indent=2)

    def set_scene(self, location_id):
        """
        Set the current scene by location ID. Updates session.json and reloads state.
        """
        self.scene = location_id
        self.session["location"] = location_id
        self._save_session()
        # Reload all modules (including new location)
        self._load_session()

    def get_current_location(self):
        """Return the current location ID (scene)."""
        return self.session.get("location")
    
    def get_current_location_data(self):
        """Return the current location data from memory_state."""
        location_id = self.get_current_location()
        return self.memory_state.get("location", {}) if location_id else None

    def set_current_location(self, location_id):
        """Set the current location (scene) by location ID."""
        self.set_scene(location_id)

    def get_entity(self, module, entity_id):
        # Always check memory first
        entities = self.memory_state.get(module, {})
        return entities.get(entity_id)

    def update_entity(self, module, entity_id, data, source="system"):
        # Update in memory
        if module not in self.memory_state:
            self.memory_state[module] = {}
        self.memory_state[module][entity_id] = data
        # Log change
        self._log_change(module, entity_id, data, source)
        # Persist
        self._persist_entity(module)

    def _persist_entity(self, module):
        # Persist a module's state to its mapped file
        module_id = self.session.get(module)
        if not module_id:
            return
        path = self._id_to_path(module_id)
        with open(path, "w") as f:
            json.dump(self.memory_state[module], f, indent=2)

    def _log_change(self, module, entity_id, data, source):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "module": module,
            "location": self.get_current_location(),
            "entity_id": entity_id,
            "data": data,
            "source": source
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def snapshot(self):
        # Save all in-memory state modules to disk using specialized managers if available
        if self.location_manager:
            self.location_manager.data = self.memory_state.get("location", {})
            self.location_manager.save()
        if self.npc_manager:
            # Update all loaded NPCs from memory_state if present
            npcs_mem = self.memory_state.get("npcs", {})
            for npc_id in self.npc_manager.npc_ids:
                if npc_id in npcs_mem:
                    self.npc_manager.npcs[npc_id] = npcs_mem[npc_id]
            self.npc_manager.save()
        # Fallback for other modules
        for module in self.memory_state:
            if module not in ["location", "npcs"]:
                self._persist_entity(module)

    # Get all NPC data for current location
    def get_location_npcs(self):
        if self.npc_manager:
            return self.npc_manager.get_all_npcs()
        return {}

    # Example: get all players
    def get_players(self):
        return self.memory_state.get("players", {})
    
    def update_nested_key(self, module, entity_id, key_path, value, source="system"):
            """
            Update a nested key in the in-memory state for a given module/entity.
            key_path: list of keys to traverse (e.g., ["dialogue_state", "mood"])
            value: new value to set
            """
            if module not in self.memory_state or entity_id not in self.memory_state[module]:
                raise KeyError(f"Entity {entity_id} not found in module {module}.")
            target = self.memory_state[module][entity_id]
            d = target
            for k in key_path[:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]
            d[key_path[-1]] = value
            self._log_change(module, entity_id, {"updated_path": key_path, "new_value": value}, source)


# Instantiate the new game state manager
# gamestate = GameStateManager()
# 

def test():
    gamestate = GameStateManager()
    print("=== GameStateManager Test ===")
    print(f"Current Scene: {gamestate.scene}")
    print(f"Memory State Keys: {list(gamestate.memory_state.keys())}")
    print(f"Current Location Data: {gamestate.get_current_location_data()}")
    print(f"Location NPCs: {gamestate.get_location_npcs()}")
    print(f"NPC Name: {gamestate.npc_manager.get_npc_name('npc_GuardCaptainThorne')}")

test()