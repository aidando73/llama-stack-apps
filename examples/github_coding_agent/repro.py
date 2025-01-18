import os
from typing import Literal, Optional, Tuple, Union, Dict, List
from llama_stack_client import LlamaStackClient
from llama_models.llama3.api.chat_format import ChatFormat
from llama_models.llama3.api.tokenizer import Tokenizer
from llama_models.llama3.api.datatypes import StopReason
from llama_models.llama3.api.tool_utils import (
    is_valid_python_list,
    parse_python_list_for_function_calls,
)
import re
from llama_agent.utils.file_tree import list_files_in_repo
from llama_agent import REPO_DIR
from llama_agent.utils.ansi import red, yellow, magenta, blue
from subprocess import run
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client.types.agent_create_params import AgentConfig
from llama_stack_client.types.tool_def_param import ToolDefParam, Parameter
from llama_stack_client.lib.agents.client_tool import ClientTool
from llama_stack.apis.inference import ToolResponseMessage, UserMessage

MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"


class ExampleTool(ClientTool):
    def get_name(self) -> str:
        return "example_tool"

    def get_description(self) -> str:
        return "List all files in a directory."

    def get_params_definition(self) -> Dict[str, Parameter]:
        return {
            "path": Parameter(
                name="path",
                parameter_type="string",
                description="Path to a directory. E.g., `src/` or `src/example` If referencing a file, will return the name of the file.",
                required=True,
            )
        }
    
    def run_impl(self, path: str) -> str:
        return f"Listed files in {path}"

    def run(
        self, messages: List[Union[UserMessage, ToolResponseMessage]]
    ) -> List[Union[UserMessage, ToolResponseMessage]]:
        print("Example tool called")
        return messages

agent_config = AgentConfig(
    model=MODEL_ID,
    instructions="Please call the example_tool tool",
    client_tools=[
        ToolDefParam(
        name="example_tool",
        description="Example tool",
        parameters=[
            Parameter(
                name="path",
                parameter_type="string",
                description="Path to a directory. E.g., `src/` or `src/example` If referencing a file, will return the name of the file.",
                required=True,
            )
        ],
    )],
    enable_session_persistence=False,
    tool_prompt_format="python_list",
)
client = LlamaStackClient(base_url="http://localhost:5000")
agent = Agent(client, agent_config, client_tools=[ExampleTool()])
session_id = agent.create_session("test-session")
response = agent.create_turn(
    session_id=session_id,
    messages=[
        {"role": "user", "content": "Please call the example_tool tool."}
    ],
)

for log in EventLogger().log(response):
    print(magenta(log), end="")