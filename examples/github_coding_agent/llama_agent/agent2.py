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
ITERATIONS = 15

def run_agent(
    client: LlamaStackClient,
    repo: str,
    problem_statement: str,
    instance_id: str,
    eval_dir: str,
    sandbox_dir: str,
) -> Tuple[Literal["changes_made", "no_changes_made"], str, Optional[str]]:
    files_in_repo = "\n".join(
        list_files_in_repo(os.path.join(sandbox_dir, repo), depth=1)
    )
    system_prompt = PHASE1_SYSTEM.format(
        problem_statement=problem_statement, file_tree=files_in_repo, repo=repo
    )
    agent_config = AgentConfig(
        model=MODEL_ID,
        instructions=system_prompt,
        client_tools=PHASE1_TOOLS,
        enable_session_persistence=False,
        tool_prompt_format="python_list",
    )
    agent = Agent(client, agent_config, client_tools=[PickFileTool(), ListFilesTool(), ViewFileTool()])
    session_id = agent.create_session("test-session")
    response = agent.create_turn(
        session_id=session_id,
        messages=[
            {"role": "user", "content": "Find the file that is relevant to the problem statement."}
        ],
    )
    for chunk in response:
        if hasattr(chunk, "event"):
            if hasattr(chunk.event, "payload") and hasattr(chunk.event.payload, "delta"):
                print(magenta(chunk.event.payload.delta.text), end="")
            else:
                print(blue(chunk.event))
        else:
            print(blue(chunk))
    # for log in EventLogger().log(response):
    #     print(magenta(log), end="")




PHASE1_SYSTEM = """
You are an expert software engineer. You are given the following problem:
<problem_statement>
{problem_statement}
</problem_statement>

The repo is called {repo}.

Here is the file tree of the repository:
<file_tree>
{file_tree}
</file_tree>

Your task is to locate the relevant file to the problem statement by making one or more function/tool calls.

If you have located the relevant file, call the `pick_file` function with the path to the file. \
E.g., `pick_file(path="src/file.py")`
"""

PHASE1_TOOLS = [
    ToolDefParam(
        name="list_files",
        description="List all files in a directory.",
        parameters=[
            Parameter(
                name="path",
                parameter_type="string",
                description="Path to a directory. E.g., `src/` or `src/example` If referencing a file, will return the name of the file.",
                required=True,
            )
        ],
    ),
    ToolDefParam(
        name="view_file",
        description="View a file",
        parameters=[
            Parameter(
                name="path",
                parameter_type="string",
                description="Path to file, e.g. `src/file.py` or `src/example/file.py`.",
                required=True,
            )
        ],
    ),
    ToolDefParam(
        name="pick_file",
        description=("Pick the file that is relevant to the problem statement."),
        parameters=[
            Parameter(
                name="path",
                parameter_type="string",
                description="Path to file, e.g. `src/file.py` or `src/example/file.py`.",
                required=True,
            )
        ],
    ),
]


class PickFileTool(ClientTool):
    def get_name(self) -> str:
        return "pick_file"

    def get_description(self) -> str:
        return "Pick the file that is relevant to the problem statement."

    def get_params_definition(self) -> Dict[str, Parameter]:
        return {
            "path": Parameter(
                name="path",
                parameter_type="string",
                description="Path to file, e.g. `src/file.py` or `src/example/file.py`.",
                required=True,
            )
        }

    def run(
        self, messages: List[Union[UserMessage, ToolResponseMessage]]
    ) -> List[Union[UserMessage, ToolResponseMessage]]:
        print("Pick file called")
        return messages



class ListFilesTool(ClientTool):
    def get_name(self) -> str:
        return "list_files"

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
        print("List files called")
        return messages

class ViewFileTool(ClientTool):
    def get_name(self) -> str:
        return "view_file"

    def get_description(self) -> str:
        return "View a file"

    def get_params_definition(self) -> Dict[str, Parameter]:
        return {
            "path": Parameter(
                name="path",
                parameter_type="string",
                description="Path to file, e.g. `src/file.py` or `src/example/file.py`.",
                required=True,
            )
        }
    
    def run(
        self, messages: List[Union[UserMessage, ToolResponseMessage]]
    ) -> List[Union[UserMessage, ToolResponseMessage]]:
        print("View file called")
        return messages