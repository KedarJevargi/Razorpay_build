import asyncio
import os
import asyncpg
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/commerce")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

async def read_file(filepath: str) -> str:
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

async def generate_embedding(client: genai.Client, text: str) -> list[float]:
    # text-embedding-004 produces 768-dimensional vectors
    response = client.models.embed_content(
        model='gemini-embedding-2',
        contents=text,
    )
    return response.embeddings[0].values

async def run_migrations():
    print(f"Connecting to database at {DB_URL}...")
    try:
        conn = await asyncpg.connect(DB_URL)
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return

    print("Running schema.sql...")
    schema_sql = await read_file(os.path.join(os.path.dirname(__file__), 'schema.sql'))
    await conn.execute(schema_sql)

    print("Running seed.sql...")
    seed_sql = await read_file(os.path.join(os.path.dirname(__file__), 'seed.sql'))
    await conn.execute(seed_sql)

    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        print("WARNING: GEMINI_API_KEY not set. Skipping knowledge document embeddings.")
        await conn.close()
        return

    print("Generating embeddings for knowledge documents...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    docs_dir = os.path.join(os.path.dirname(__file__), 'knowledge_docs')
    merchant_id = 'merch_adventurehub'
    
    for filename in os.listdir(docs_dir):
        if not filename.endswith('.md'):
            continue
            
        filepath = os.path.join(docs_dir, filename)
        content = await read_file(filepath)
        doc_type = filename.replace('.md', '')
        title = doc_type.replace('_', ' ').title()
        
        print(f"Processing {filename}...")
        try:
            embedding = await generate_embedding(client, content)
            
            # Format embedding as string for pgvector '[0.1, 0.2, ...]'
            embedding_str = f"[{','.join(str(x) for x in embedding)}]"
            
            await conn.execute('''
                INSERT INTO knowledge_documents (merchant_id, doc_type, title, content, embedding)
                VALUES ($1, $2, $3, $4, $5)
            ''', merchant_id, doc_type, title, content, embedding_str)
            print(f"Successfully ingested {title}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print("Generating embeddings for products...")
    products = await conn.fetch("SELECT id, name, category, description FROM products")
    for prod in products:
        content_to_embed = f"{prod['name']} - {prod['category']} - {prod['description']}"
        print(f"Embedding product {prod['name']}...")
        try:
            embedding = await generate_embedding(client, content_to_embed)
            embedding_str = f"[{','.join(str(x) for x in embedding)}]"
            await conn.execute("UPDATE products SET embedding = $1 WHERE id = $2", embedding_str, prod['id'])
        except Exception as e:
            print(f"Error embedding product {prod['name']}: {e}")

    print("Migration and seeding complete.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migrations())
