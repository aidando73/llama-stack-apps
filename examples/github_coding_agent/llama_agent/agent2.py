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

# Currently only supports 3.3-70B-Instruct at the moment since it depends on the 3.3/3.2 tool prompt format
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"
ITERATIONS = 15

def run_agent(
    client: LlamaStackClient, repo: str, issue_title: str, issue_body: str
) -> Tuple[Literal["changes_made", "no_changes_made"], str, Optional[str]]:
    print("Hello")