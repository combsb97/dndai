from typing import Dict, List, Any
import json

class GameState:
    def __init__(self):
        self.game_state = {
            "world":{
                "locations": {
                    "loc_Havenwood": {
                        "name": "Havenwood",
                        "type": "Town",
                        "description": "A small, resilient town built amidst the colossal ruins of the past. Wooden structures are nestled against ancient, vine-covered Elven stonework.",
                        "connections": {
                        "north_path": "loc_Gloomwood",
                        "town_square": "loc_WearyWandererTavern"
                        },
                        "state": ["peaceful", "tense_undercurrent"]
                    },
                    "loc_Gloomwood": {
                        "name": "The Gloomwood",
                        "type": "Forest",
                        "description": "A dark and menacing forest of ancient ironwood trees. Sunlight struggles to pierce the thick canopy, and strange sounds echo from the shadows.",
                        "connections": {
                        "south_path": "loc_Havenwood"
                        },
                        "state": ["dangerous", "unnatural_silence"]
                    },
                    "loc_WearyWandererTavern": {
                        "name": "The Weary Wanderer Tavern",
                        "type": "Building",
                        "description": "The heart of Havenwood. The air is thick with the smell of woodsmoke, roasting meat, and spilled ale. A large, crackling fireplace dominates one wall.",
                        "connections": {
                        "town_square": "loc_Havenwood"
                        },
                        "state": ["bustling", "cozy"]
                    }                    
                }
            },
            "actors": {
                "pcs": {
                    "pc_Elara": {
                        "name": "Elara",
                        "class": "Rogue",
                        "race": "Human",
                        "background": "Outlander",
                        "stats": {
                            "hp_current": 22,
                            "hp_max": 22,
                            "ac": 14,
                            "str": 10,
                            "dex": 17,
                            "con": 12,
                            "int": 14,
                            "wis": 11,
                            "cha": 13
                        },
                        "inventory": ["item_Shortsword", "item_LeatherArmor", "item_ThievesTools", "item_MapFragment"],
                        "statusEffects": [],
                        "personalGoals": ["Discover the meaning of the symbols on the strange map fragment."],
                        "currentLocation": "loc_Havenwood"
                    },
                    "pc_Bryn": {
                        "name": "Bryn",
                        "class": "Cleric",
                        "race": "Dwarf",
                        "background": "Acolyte",
                        "stats": {
                            "hp_current": 28,
                            "hp_max": 28,
                            "ac": 16,
                            "str": 12,
                            "dex": 10,
                            "con": 14,
                            "int": 13,
                            "wis": 17,
                            "cha": 11
                        },
                        "inventory": ["item_Mace", "item_ChainMail", "item_HolySymbol"],
                        "statusEffects": [],
                        "personalGoals": ["Uncover the truth behind the ancient ruins."],
                        "currentLocation": "loc_Havenwood"
                    }
                },
                "npcs": {
                    "npc_GuardCaptainThorne": {
                        "name": "Guard Captain Thorne",
                        "role": "Guard",
                        "currentLocation": "loc_Havenwood",
                        "dispositionToParty": "neutral",
                        "stats": { "hp_current": 30, "hp_max": 30, "ac": 16 },
                        "knowledge": [
                            {
                                "id": "know_HavenwoodHistory",
                                "info": "Havenwood was once a thriving Elven settlement before the Great War.",
                                "revealed": False
                            }
                        ],
                        "dialogue_state": {
                            "mood": "cautious"
                        }
                    },
                    "npc_BoricTheBarkeep": {
                        "name": "Boric the Barkeep",
                        "role": "Quest Giver / Merchant",
                        "currentLocation": "loc_WearyWandererTavern",
                        "dispositionToParty": "friendly",
                        "stats": { "hp_current": 18, "hp_max": 18 },
                        "knowledge": [
                        {
                            "id": "know_GloomwoodDangers",
                            "info": "The Gloomwood has become more aggressive lately; the wolf packs are getting bolder.",
                            "revealed": False
                        }
                        ],
                        "dialogue_state": {
                        "mood": "worried"
                        }
                    },
                    "npc_GloomfangWolf": {
                        "name": "Gloomfang Wolf",
                        "role": "Hostile Creature",
                        "currentLocation": "loc_Gloomwood",
                        "dispositionToParty": "hostile",
                        "stats": { "hp_current": 11, "hp_max": 11, "ac": 13 }
                    }
                }
            },
            "journal": "",
            "session": {
                "currentLocation": {
                "loc_Havenwood": {
                        "name": "Havenwood",
                        "type": "Town",
                        "description": "A small, resilient town built amidst the colossal ruins of the past. Wooden structures are nestled against ancient, vine-covered Elven stonework.",
                        "pointsOfInterest": {
                        "loc_WearyWandererTavern": {
                                "name": "The Weary Wanderer Tavern",
                                "description": "The heart of Havenwood. The air is thick with the smell of woodsmoke, roasting meat, and spilled ale. A large, crackling fireplace dominates one wall."
                            }
                        },
                        "connections": {
                        "north_path": "loc_Gloomwood"
                        },
                        "state": ["peaceful", "tense_undercurrent"]
                    }
                }
            },
            "history": ""
        }
        self.hostile_game_state = {
            "world": {
                "locations": {
                    "loc_Battlefield": {
                        "name": "Abandoned Battlefield",
                        "type": "Field",
                        "description": "A muddy, blood-soaked field littered with broken weapons and armor. The air is thick with tension and the cries of battle.",
                        "connections": {
                            "north": "loc_ForestEdge",
                            "south": "loc_VillageOutskirts"
                        },
                        "state": ["chaotic", "dangerous"]
                    },
                    "loc_ForestEdge": {
                        "name": "Forest Edge",
                        "type": "Forest",
                        "description": "The edge of a dense forest, offering cover and concealment.",
                        "connections": {
                            "south": "loc_Battlefield"
                        },
                        "state": ["quiet", "ominous"]
                    },
                    "loc_VillageOutskirts": {
                        "name": "Village Outskirts",
                        "type": "Village",
                        "description": "The outskirts of a small village, with a few scattered cottages.",
                        "connections": {
                            "north": "loc_Battlefield"
                        },
                        "state": ["tense"]
                    }
                }
            },
            "actors": {
                "pcs": {
                    "pc_Arin": {
                        "name": "Arin",
                        "class": "Fighter",
                        "race": "Human",
                        "background": "Soldier",
                        "stats": {
                            "hp_current": 16,
                            "hp_max": 20,
                            "ac": 16,
                            "str": 15,
                            "dex": 12,
                            "con": 14,
                            "int": 10,
                            "wis": 11,
                            "cha": 13
                        },
                        "inventory": ["item_LongSword", "item_Shield", "item_ChainMail"],
                        "statusEffects": ["in_combat"],
                        "personalGoals": ["Defeat the orc raider."],
                        "currentLocation": "loc_Battlefield"
                    }
                },
                "npcs": {
                    "npc_OrcRaider": {
                        "name": "Orc Raider",
                        "role": "Hostile Creature",
                        "currentLocation": "loc_Battlefield",
                        "dispositionToParty": "hostile",
                        "stats": {
                            "hp_current": 10,
                            "hp_max": 15,
                            "ac": 13,
                            "str": 16,
                            "dex": 11,
                            "con": 12
                        },
                        "statusEffects": ["in_combat"],
                        "knowledge": [],
                        "dialogue_state": {
                            "mood": "aggressive"
                        }
                    },
                    "npc_Villager": {
                        "name": "Terrified Villager",
                        "role": "Civilian",
                        "currentLocation": "loc_Battlefield",
                        "dispositionToParty": "neutral",
                        "stats": {
                            "hp_current": 4,
                            "hp_max": 4,
                            "ac": 10
                        },
                        "statusEffects": ["frightened"],
                        "knowledge": [],
                        "dialogue_state": {
                            "mood": "panicked"
                        }
                    }
                }
            },
            "journal": "",
            "session": {
                "currentLocation": {
                    "loc_Battlefield": {
                        "name": "Abandoned Battlefield",
                        "type": "Field",
                        "description": "A muddy, blood-soaked field littered with broken weapons and armor. The air is thick with tension and the cries of battle.",
                        "connections": {
                            "north": "loc_ForestEdge",
                            "south": "loc_VillageOutskirts"
                        },
                        "state": ["chaotic", "dangerous"]
                    }
                },
                "currentActors": {
                    "pcs": {
                        "pc_Arin": {
                            "name": "Arin",
                            "class": "Fighter",
                            "race": "Human",
                            "background": "Soldier",
                            "stats": {
                                "hp_current": 16,
                                "hp_max": 20,
                                "ac": 16,
                                "str": 15,
                                "dex": 12,
                                "con": 14,
                                "int": 10,
                                "wis": 11,
                                "cha": 13
                            },
                            "inventory": ["item_LongSword", "item_Shield", "item_ChainMail"],
                            "statusEffects": ["in_combat"],
                            "personalGoals": ["Defeat the orc raider."],
                            "currentLocation": "loc_Battlefield"
                        }
                    },
                    "npcs": {
                        "npc_OrcRaider": {
                            "name": "Orc Raider",
                            "role": "Hostile Creature",
                            "currentLocation": "loc_Battlefield",
                            "dispositionToParty": "hostile",
                            "stats": {
                                "hp_current": 10,
                                "hp_max": 15,
                                "ac": 13,
                                "str": 16,
                                "dex": 11,
                                "con": 12
                            },
                            "statusEffects": ["in_combat"],
                            "knowledge": [],
                            "dialogue_state": {
                                "mood": "aggressive"
                            }
                        },
                        "npc_Villager": {
                            "name": "Terrified Villager",
                            "role": "Civilian",
                            "currentLocation": "loc_Battlefield",
                            "dispositionToParty": "neutral",
                            "stats": {
                                "hp_current": 4,
                                "hp_max": 4,
                                "ac": 10
                            },
                            "statusEffects": ["frightened"],
                            "knowledge": [],
                            "dialogue_state": {
                                "mood": "panicked"
                            }
                        }
                    }
                }
            },
            "history": ""
        }


    

    def update_session_by_location(self) -> dict:
        """
        Update the session information based on the current location.
        """
        current_session = self.game_state.get("session", {})
        current_location_id = list(current_session.get("currentLocation").keys())[0]

        if not current_location_id:
            return {"error": "No current location set in session."}
        
        location_details = None
        locations = self.game_state.get("world", {}).get("locations", {})
        if current_location_id in locations:
            location_details = json.loads(json.dumps(locations[current_location_id]))  # Deep copy
        else:
            return {"error": f"Location ID '{current_location_id}' not found in world locations."}
        
        actor_details = {"pcs": {}, "npcs": {}}
        pcs = self.game_state.get("actors", {}).get("pcs", {})
        for pc_id, pc in pcs.items():
            actor_details["pcs"][pc_id] = json.loads(json.dumps(pc))  # Deep copy

        npcs = self.game_state.get("actors", {}).get("npcs", {})
        for npc_id, npc in npcs.items():
            if npc.get("currentLocation") == current_location_id:
                actor_details["npcs"][npc_id] = json.loads(json.dumps(npc))  # Deep copy

        session_update = {
            "currentLocation": {
                current_location_id: location_details
            },
            "currentActors": actor_details
        }

        return session_update
    
    def get_location_by_key(self, location_key: str) -> dict:
        """
        Retrieve a location dictionary from game_state['world']['locations'] by its key.
        """
        try:
            locations = self.game_state.get("world", {}).get("locations", {})
            return locations.get(location_key, None)
        except Exception as e:
            print(f"Error retrieving location by key '{location_key}': {e}")
            return None
    
    def set_session_location_by_key(self, location_key: str) -> None:
        """
        Set the current location in the session by location key.
        """
        location = self.get_location_by_key(location_key)
        if location:
            self.game_state["session"]["currentLocation"] = {location_key: location}
        else:
            raise ValueError(f"Location key '{location_key}' not found in world locations.")
        
    def get_current_actors_by_location_id(self, location_id: str) -> dict:
        """
        Retrieve all actors (PCs and NPCs) currently at the specified location ID.
        """
        actors_at_location = {"pcs": {}, "npcs": {}}
        
        pcs = self.game_state.get("actors", {}).get("pcs", {})
        for pc_id, pc in pcs.items():
            # if pc.get("currentLocation") == location_id:
            #     actors_at_location["pcs"][pc_id] = json.loads(json.dumps(pc))  # Deep copy
            actors_at_location["pcs"][pc_id] = json.loads(json.dumps(pc))  # Deep copy

        npcs = self.game_state.get("actors", {}).get("npcs", {})
        for npc_id, npc in npcs.items():
            if npc.get("currentLocation") == location_id:
                actors_at_location["npcs"][npc_id] = json.loads(json.dumps(npc))  # Deep copy

        return actors_at_location
    
    def set_current_actors_by_location_id(self, location_id: str) -> None:
        """
        Update the current actors in the session based on the specified location ID.
        """
        actors = self.get_current_actors_by_location_id(location_id)
        self.game_state["session"]["currentActors"] = actors
    

gamestate = GameState()
