import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from google import genai

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/commerce")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def test_db():
    print("\n--- PHASE 1: DATABASE TEST SCRIPT ---")
    
    conn = await asyncpg.connect(DB_URL)
    
    # 1. Test standard relational tables (Products & Inventory)
    print("\n📦 1. Fetching Catalog & Inventory...")
    products = await conn.fetch('''
        SELECT p.name, p.price, i.quantity 
        FROM products p 
        JOIN inventory i ON p.id = i.product_id
        LIMIT 3
    ''')
    for p in products:
        print(f"  - {p['name']}: ₹{p['price']} (Stock: {p['quantity']})")

    # 2. Test Policy Engine rules are seeded
    print("\n🛡️ 2. Fetching Policy Engine Guardrails...")
    policies = await conn.fetch("SELECT policy_key, policy_value FROM merchant_policies")
    for p in policies:
        print(f"  - Rule: {p['policy_key']} => {p['policy_value']}")

    # 3. Test pgvector RAG capabilities
    print("\n🧠 3. Testing pgvector Semantic Search (RAG)...")
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("Skipping RAG test because GEMINI_API_KEY is not set.")
    else:
        query = "Do you accept returns for climbing ropes?"
        print(f"  - Querying for: '{query}'")
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.embed_content(
            model='gemini-embedding-2',
            contents=query,
        )
        embedding = response.embeddings[0].values
        embedding_str = f"[{','.join(str(x) for x in embedding)}]"
        
        # <=>: Cosine distance in pgvector
        results = await conn.fetch('''
            SELECT title, doc_type, 1 - (embedding <=> $1) AS similarity
            FROM knowledge_documents
            ORDER BY embedding <=> $1
            LIMIT 1
        ''', embedding_str)
        
        if results:
            print(f"  - Closest Document Found: {results[0]['title']} ({results[0]['doc_type']}.md)")
            print(f"  - Similarity Score: {results[0]['similarity']:.4f}")
            if results[0]['doc_type'] == 'return_policy':
                print("  - ✅ SUCCESS: Correctly identified Return Policy as the source for this query!")
        else:
            print("  - No documents found.")

    await conn.close()
    print("\n--- TEST COMPLETE ---\n")

if __name__ == "__main__":
    asyncio.run(test_db())
