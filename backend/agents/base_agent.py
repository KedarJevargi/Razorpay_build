import os
import json
import logging
import inspect
from functools import wraps
from typing import List, Dict, Any, Callable, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from a2a.types import AgentCard, Task, Message, Role, Part
from backend.agents.exceptions import PaymentVerificationError

class TaskResult(BaseModel):
    task_id: str
    status: str
    result_data: Optional[Dict] = None
    error_message: Optional[str] = None

logger = logging.getLogger(__name__)

def make_serializable(obj: Any) -> Any:
    from decimal import Decimal
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

class BaseAgent:
    """
    Base Agent class that wraps the Google GenAI SDK.
    It expects a Pydantic Task object and returns a TaskResult.
    """
    def __init__(self, agent_card: AgentCard, model_name: str = "gemini-2.5-flash"):
        self.agent_card = agent_card
        self.model_name = model_name
        # The SDK automatically picks up GEMINI_API_KEY from the environment
        self.client = genai.Client()
        self.tools: List[Callable] = []

    def register_tool(self, func: Callable):
        """Register a Python function as a tool for the agent."""
        self.tools.append(func)
        
    @staticmethod
    def _python_type_to_schema_type(annotation) -> str:
        """Map Python type hints to GenAI Schema types."""
        if annotation is inspect.Parameter.empty:
            return "STRING"
        # Unwrap Optional[X] -> X
        origin = getattr(annotation, '__origin__', None)
        if origin is not None:
            args = getattr(annotation, '__args__', ())
            # Handle Optional (Union[X, None])
            if len(args) == 2 and type(None) in args:
                annotation = args[0] if args[1] is type(None) else args[1]
        if annotation in (int,):
            return "INTEGER"
        elif annotation in (float,):
            return "NUMBER"
        elif annotation in (bool,):
            return "BOOLEAN"
        return "STRING"

    async def process_task(self, task: Task) -> TaskResult:
        """
        Process an incoming Task by formulating the context and using the LLM.
        """
        # Convert A2A Task history to google-genai history
        history: List[types.Content] = []
        for msg in task.history:
            # Map buyer/system to 'user' role for the LLM, and merchant to 'model'
            role = "user" if msg.role in [Role.ROLE_USER, Role.ROLE_UNSPECIFIED] else "model"
            text_content = "".join([p.text for p in msg.parts if p.HasField("text")])
            history.append(
                types.Content(role=role, parts=[types.Part.from_text(text=text_content)])
            )
            
        system_instruction = f"You are {self.agent_card.name}. {self.agent_card.description}"

        genai_tools = []
        for t in self.tools:
            sig = inspect.signature(t)
            properties = {}
            required = []
            for name, param in sig.parameters.items():
                if name == "self": continue
                # Infer schema type from Python type hints
                schema_type = self._python_type_to_schema_type(param.annotation)
                properties[name] = types.Schema(type=schema_type, description=f"Parameter {name}")
                # Only mark parameters without defaults as required
                if param.default is inspect.Parameter.empty:
                    required.append(name)
                
            fd = types.FunctionDeclaration(
                name=t.__name__,
                description=t.__doc__ or f"Tool {t.__name__}",
                parameters=types.Schema(
                    type="OBJECT",
                    properties=properties,
                    required=required
                ) if properties else None
            )
            genai_tools.append(fd)

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            tools=[types.Tool(function_declarations=genai_tools)] if genai_tools else None,
            # We handle function calling manually to support async tools
        )

        try:
            # Create a chat session with the historical messages
            chat = self.client.aio.chats.create(
                model=self.model_name,
                config=config,
                history=history
            )
            
            # The actual goal is the last message in history
            intent = "".join([p.text for p in task.history[-1].parts if p.HasField("text")])
            logger.info(f"Agent {self.agent_card.name} processing task {task.id}: {intent}")
            
            # Manual function calling loop
            response = await chat.send_message(intent)
            
            while response.function_calls:
                function_responses = []
                for fc in response.function_calls:
                    tool_name = fc.name
                    tool_args = fc.args
                    
                    logger.info(f"Agent {self.agent_card.name} calling tool: {tool_name} with args: {tool_args}")
                    print(f"DEBUG: Agent {self.agent_card.name} calling tool: {tool_name} with args: {tool_args}")
                    
                    # Find the tool
                    tool_func = next((t for t in self.tools if t.__name__ == tool_name), None)
                    if not tool_func:
                        error_msg = f"Tool {tool_name} not found"
                        print(f"DEBUG: Error - {error_msg}")
                        function_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response={"error": error_msg}
                        ))
                        continue
                        
                    try:
                        if inspect.iscoroutinefunction(tool_func):
                            result = await tool_func(**tool_args)
                        else:
                            result = tool_func(**tool_args)
                            
                        print(f"DEBUG: Tool {tool_name} returned successfully")
                        function_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response={"result": make_serializable(result)}
                        ))
                    except PaymentVerificationError as e:
                        print(f"DEBUG: Tool {tool_name} raised PaymentVerificationError: {e}")
                        raise e  # Bubble this up out of the agent loop!
                    except Exception as e:
                        print(f"DEBUG: Tool {tool_name} raised exception: {e}")
                        function_responses.append(types.Part.from_function_response(
                            name=tool_name,
                            response={"error": str(e)}
                        ))
                        
                # Send the function responses back to the model
                print(f"DEBUG: Sending tool responses back to {self.agent_card.name}'s LLM...")
                response = await chat.send_message(function_responses)
                print(f"DEBUG: Received reply from {self.agent_card.name}'s LLM.")
            
            return TaskResult(
                task_id=task.id,
                status="completed",
                result_data={"response": response.text},
                error_message=None
            )
        except PaymentVerificationError as e:
            logger.error(f"Agent {self.agent_card.name} halting on PaymentVerificationError: {e}")
            raise e
        except Exception as e:
            logger.error(f"Agent {self.agent_card.name} failed task {task.id}: {e}", exc_info=True)
            return TaskResult(
                task_id=task.id,
                status="failed",
                result_data=None,
                error_message=str(e)
            )
