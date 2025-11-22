import streamlit as st
from urllib.parse import parse_qs
from dm_agent import (
    interpret_user_intent,
    process_player_input,
    execute_events,
    generate_narrative,
)
from game_state import gamestate

st.set_page_config(page_title="D&D AI Playtest", layout="wide")

# Get player id from URL
query_params = st.experimental_get_query_params()
player_id = query_params.get("player", [None])[0]

pcs = gamestate.game_state["actors"]["pcs"]
pc_ids = list(pcs.keys())

st.title("D&D AI Playtest")

if not player_id or player_id not in pcs:
    st.warning("Add ?player=pc_Elara (or another PC id) to the URL to play as a character.")
    st.write("Available PCs:", pc_ids)
    st.stop()

st.header(f"Current Scene for {pcs[player_id]['name']} ({player_id})")
st.json(gamestate.game_state["session"])

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "player_inputs" not in st.session_state:
    st.session_state.player_inputs = {}

st.header("Your Action")
with st.form("player_action"):
    player_input = st.text_input("What do you do?", key=f"input_{player_id}")
    submitted = st.form_submit_button("Submit Action")

if submitted and player_input.strip():
    st.session_state.player_inputs[player_id] = player_input.strip()
    st.success("Action submitted! Wait for the DM to process the turn.")

# DM view: process all actions when ready
if st.button("DM: Process Turn"):
    turn_messages = st.session_state.messages.copy()

    # Step 1: Combine all player inputs into a batch JSON
    batch_inputs = [
        {"actor_id": pc_id, "input": player_input}
        for pc_id, player_input in st.session_state.player_inputs.items()
    ]
    print("\n\n>>>>> BATCH_PLAYER_INPUTS <<<<<\n\n", batch_inputs, "\n\n>>>>> END BATCH_PLAYER_INPUTS <<<<<\n\n")
    turn_messages.append({"role": "system", "content": f"Batch Player Inputs: {batch_inputs}"})

    # Step 2: Interpret all intents at once
    try:
        interpreted_intents = interpret_user_intent(batch_inputs)
        print("\n\n>>>>> INTERPRETED_INTENTS <<<<<\n\n", interpreted_intents, "\n\n>>>>> END INTERPRETED_INTENTS <<<<<\n\n")
        turn_messages.append({"role": "system", "content": f"Interpreted Intents: {interpreted_intents}"})
    except Exception as e:
        st.error(f"Error interpreting user intents: {e}")

    # Step 3: Validate/process all interpreted intents at once
    try:
        validated_plan = process_player_input(interpreted_intents)
        print("\n\n>>>>> VALIDATED_PLAN <<<<<\n\n", validated_plan, "\n\n>>>>> END VALIDATED_PLAN <<<<<\n\n")
        turn_messages.append({"role": "system", "content": f"Validated Plan: {validated_plan}"})
    except Exception as e:
        st.error(f"Error validating plan: {e}")

    # Step 4: Execute all events together
    try:
        execution_results = execute_events(validated_plan)
        print("\n\n>>>>> EXECUTION_RESULTS <<<<<\n\n", execution_results, "\n\n>>>>> END EXECUTION_RESULTS <<<<<\n\n")
        turn_messages.append({"role": "system", "content": f"Execution Results: {execution_results}"})
    except Exception as e:
        st.error(f"Error executing events: {e}")

    # Step 5: Generate a single narrative for all actions
    try:
        combined_input = " | ".join([f"{pcs[pc_id]['name']}: {inp}" for pc_id, inp in st.session_state.player_inputs.items()])
        narrative = generate_narrative(
            combined_input, validated_plan, execution_results, turn_messages
        )
        print("\n\n>>>>> NARRATIVE <<<<<\n\n", narrative, "\n\n>>>>> END NARRATIVE <<<<<\n\n")
        turn_messages.append({"role": "system", "content": f"Narrative: {narrative}"})
    except Exception as e:
        st.error(f"Error generating narrative: {e}")

    # Update session messages and clear inputs for next turn
    st.session_state.messages = turn_messages
    st.session_state.player_inputs = {}
    st.success("Turn processed!")

# Show narrative history
st.header("Narrative History")
for msg in st.session_state.messages:
    if msg["role"] == "system" and "Narrative" in msg["content"]:
        st.markdown(f"**Narrator:** {msg['content']}")