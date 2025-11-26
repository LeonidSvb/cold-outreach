from agency_swarm import Agent


class WebScrapingAgent(Agent):
    def __init__(self):
        super().__init__(
            name="WebScrapingAgent",
            description="Expert web scraping agent specialized in bulk website processing, "
                       "email extraction, and content analysis at scale.",
            instructions="./instructions.md",
            tools_folder="./tools",
            temperature=0.5,
            max_prompt_tokens=4000,
        )


if __name__ == "__main__":
    agent = WebScrapingAgent()
    print(f"Agent '{agent.name}' initialized successfully!")
    print(f"Description: {agent.description}")
    print(f"Tools available: {len(agent.tools)}")
