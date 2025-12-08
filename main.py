from src.agents.dm_agent import DMAgent

def main():
    """
    Initializes and runs the Dungeon Master agent.
    """
    print("Initializing the DM Agent...")
    try:
        agent = DMAgent()
        agent.run()
    except Exception as e:
        print(f"A critical error occurred: {e}")

if __name__ == "__main__":
    main()