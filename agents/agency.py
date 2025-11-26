from agency_swarm import Agency
from web_scraping_agent.web_scraping_agent import WebScrapingAgent


def create_agency():
    """
    Create and return the Web Scraping Agency.

    This agency consists of a single WebScrapingAgent that handles
    all web scraping, email extraction, and data processing tasks.
    """

    # Initialize the agent
    web_scraper = WebScrapingAgent()

    # Create agency with the agent
    agency = Agency(
        [web_scraper],  # Single agent agency
        shared_instructions="./agency_manifesto.md",
        temperature=0.5,
        max_prompt_tokens=4000,
    )

    return agency


if __name__ == "__main__":
    import asyncio

    # Create the agency
    agency = create_agency()

    print("\n" + "="*60)
    print("    WEB SCRAPING AGENCY - READY")
    print("="*60)
    print("\nAgency successfully initialized!")
    print("\nAvailable Agent: WebScrapingAgent")
    print("\nCapabilities:")
    print("  - Bulk website scraping (quick/standard/full modes)")
    print("  - Email and phone extraction")
    print("  - CSV processing with parallel workers")
    print("  - Multiple export formats (CSV/JSON/Excel)")
    print("\nStarting terminal demo...")
    print("-"*60 + "\n")

    # Run in terminal mode for testing
    agency.demo_gradio()
