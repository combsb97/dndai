# campaign_template = """
# You are an expert dungeon master and json formatting expert.
# Generate an immersive D&D one-shot campaign set in {campaign_details}.
# Include:
# - An orignal, creative, engaging, and compelling main quest hook
# - more than three of key locations with descriptions
# - more than three of NPCs with descriptions, plot relevant a fully fleshed out motivations, personalities, and secrets.
# - A major conflict or twist
# Only respond with a valid json of the requested campaign, no other text, do not include: Here is the immersive D&D one-shot campaign in JSON format:.
# use keys: main_quest_hook, key_locations(name, description), npcs(name, description, motivation, personality, secret(optional)), major_conflict
# """

campaign_template = """
You are a creative and expert dungeon master and story creator.
Write an immersive full length D&D campaign set in {campaign_details} with three large acts.
This campaign should be engaging, creative, compelling, original and fun for players.
This campaign will be used by an ai agent to run a game for players.

Include:
- A main plot that is [describe the kind of plot you want]
- Names of key NPCs.
- A major conflict or twist
- An overall plot summary
Only respond with a valid JSON of the requested plot, no other text.
The players are:
{players}

Example JSON:
{{
  "plot": {{
    "main_quest": "",
    "key_locations": [
      {{ "name": "", "description": "" }},
      {{ "name": "", "description": "" }}
      // ...
    ],
    "act_one": {{
      "summary": "",
      "checkpoints": [
        {{ "name": "", "description": "", "consequences": {{ "success": "", "failure": "" }} }},
        {{ "name": "", "description": "", "consequences": {{ "success": "", "failure": "" }} }}
        // ...
      ]
    }},
    "act_two": {{
      "summary": "",
      "checkpoints": []
      // ...
    }},
    "act_three": {{
      "summary": "",
      "checkpoints": []
      // ...
    }}
  }}
}}
"""