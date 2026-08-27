import os
from dotenv import load_dotenv

# Load environment variables before anything else
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.db.pool import init_pool, close_pool
from backend.api.routes import router, MerchantRequestHandler

from a2a.server.routes import add_a2a_routes_to_fastapi, create_agent_card_routes, create_jsonrpc_routes
from a2a.types import AgentCard

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing Database Pool...")
    await init_pool()
    yield
    # Shutdown
    print("Closing Database Pool...")
    await close_pool()

app = FastAPI(
    title="Merchant Agent API",
    description="A2A JSON-RPC Endpoint for the Merchant Orchestrator Agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for testing from any frontend if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Define AgentCard statically for the discovery endpoint
agent_card = AgentCard(
    name="AdventureHub Merchant Agent",
    description="An AI agent capable of handling catalog queries, policies, and checkout."
)

# Mount A2A routes
add_a2a_routes_to_fastapi(
    app,
    agent_card_routes=create_agent_card_routes(agent_card, card_url="/.well-known/agent.json"),
    jsonrpc_routes=create_jsonrpc_routes(request_handler=MerchantRequestHandler(), rpc_url="/api/jsonrpc"),
)
