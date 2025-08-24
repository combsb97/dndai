import streamlit as st
from campaign_generator import CampaignGenerator

st.title("D&D Campaign Generator")

# Input area for campaign details
campaign_details = st.text_area(
    "Enter details for your campaign (e.g., setting, tone, desired themes):",
    height=150  # Adjust height as needed
)

# Button to generate the campaign
if st.button("Generate Campaign"):
    if not campaign_details:
        st.warning("Please enter some details for your campaign.")
    else:
        with st.spinner("Generating campaign..."):  # Show a spinner while generating
            # Initialize the campaign generator
            generated_campaign = CampaignGenerator(
                base_url="http://localhost:11434",
                model="llama3.2",
            ).generate_campaign(campaign_details)

        if generated_campaign:
            st.write(generated_campaign)  # Display the generated campaign
    