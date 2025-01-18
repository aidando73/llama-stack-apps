import os
from typing import Literal, Optional, Tuple, Union
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
from llama_stack_client.types import Attachment
from llama_stack_client.types.agent_create_params import AgentConfig

# Currently only supports 3.3-70B-Instruct at the moment since it depends on the 3.3/3.2 tool prompt format
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"
ITERATIONS = 15

def run_agent(
    client: LlamaStackClient, repo: str, problem_statement: str, instance_id: str, eval_dir: str, sandbox_dir: str
) -> Tuple[Literal["changes_made", "no_changes_made"], str, Optional[str]]:
    agent_config = AgentConfig(
        model=MODEL_ID,
        instructions="You are a helpful assistant",
        tools=[],
        enable_session_persistence=False
    )

    agent = Agent(client, agent_config)
    session_id = agent.create_session("test-session")
    response = agent.create_turn(
        session_id=session_id,
        messages=[{"role": "user", "content": "Hello World"}],
    )
    for log in EventLogger().log(response):
        log.print()
