import sys
import os
import asyncio
import asyncpg
from dotenv import load_dotenv

# Add the project root to the Python path so we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from a2a.types import Task, Message, Role, Part
from backend.agents.catalog_agent import CatalogAgent
from backend.agents.knowledge_agent import KnowledgeAgent

load_dotenv()

async def test_agents():
    print("--- Testing Phase 3 Agents ---")
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/commerce")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        print("⚠️  GEMINI_API_KEY not set in .env. We will test instantiation but skip the LLM execution.")
    
    try:
        # Connect to DB
        pool = await asyncpg.create_pool(db_url)
        print("✅ Database connection successful.")
        
        # 1. Instantiate Catalog Agent
        catalog_agent = CatalogAgent(db_pool=pool)
        print(f"✅ Catalog Agent created: {catalog_agent.agent_card.name}")
        print(f"   Registered Tools: {[t.__name__ for t in catalog_agent.tools]}")
        
        # 2. Instantiate Knowledge Agent
        knowledge_agent = KnowledgeAgent(db_pool=pool)
        print(f"✅ Knowledge Agent created: {knowledge_agent.agent_card.name}")
        print(f"   Registered Tools: {[t.__name__ for t in knowledge_agent.tools]}")
        
        # Run E2E if API key is provided
        if gemini_key and gemini_key != "your_gemini_api_key_here":
            print("\n--- Running Task with Catalog Agent ---")
            task = Task(
                id="test-task-1",
                history=[
                    Message(role=Role.ROLE_USER, parts=[Part(text="Context: Merchant=m1. Can you find any tents in the catalog for merchant 'm1'?")])
                ]
            )
            print(f"Task Intent: 'Context: Merchant=m1. Can you find any tents in the catalog for merchant 'm1'?'")
            print("Processing... (this may take a few seconds)")
            
            result = await catalog_agent.process_task(task)
            
            print(f"\nTask Status: {result.status}")
            if result.status == "completed":
                print(f"Response: {result.result_data.get('response')}")
            else:
                print(f"Error: {result.error_message}")
                
        await pool.close()

    except ConnectionRefusedError:
        print("❌ Could not connect to PostgreSQL. Make sure Docker container is running (docker-compose up -d).")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    asyncio.run(test_agents())
