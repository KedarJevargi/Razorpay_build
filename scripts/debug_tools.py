import sys
import os
import asyncio
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.agents.merchant_orchestrator import MerchantOrchestratorAgent

class DummyAgent:
    pass

orchestrator = MerchantOrchestratorAgent(
    catalog_agent=DummyAgent(),
    knowledge_agent=DummyAgent(),
    recommendation_agent=DummyAgent(),
    checkout_agent=DummyAgent()
)

import inspect
from functools import wraps
sync_tools = []
for t in orchestrator.tools:
    if inspect.iscoroutinefunction(t):
        @wraps(t)
        def dummy_sync(*args, **kwargs):
            pass
        dummy_sync.__signature__ = inspect.signature(t)
        dummy_sync.__annotations__ = getattr(t, '__annotations__', {})
        sync_tools.append(dummy_sync)
    else:
        sync_tools.append(t)

print("Docstrings:")
for st in sync_tools:
    print(f"Tool {st.__name__}: {st.__doc__}")

from google.genai.types import GenerateContentConfig
config = GenerateContentConfig(tools=sync_tools)
print(f"Config tools: {config.tools}")
