# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
# Copyright (c) Meta Platforms, Inc. and affiliates.
# This software may be used and distributed in accordance with the terms of the Llama 3 Community License Agreement.

import asyncio
import os
import fire
from typing import Optional
from urllib.parse import urlparse
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client.types.agent_create_params import AgentConfig


async def run_main(
    host: str,
    port: int,
    use_https: bool = False,
    disable_safety: bool = False,
    cert_path: Optional[str] = None,
):
    # Construct the base URL with the appropriate protocol
    protocol = "https" if use_https else "http"
    base_url = f"{protocol}://{host}:{port}"

    # Configure client with SSL certificate if provided
    client_kwargs = {"base_url": base_url}
    if use_https and cert_path:
        client_kwargs["verify"] = cert_path

    client = LlamaStackClient(**client_kwargs)

    agent_config = AgentConfig(
        model="Llama3.1-8B-Instruct",
        instructions="You are a helpful assistant",
        sampling_params={
            "strategy": "greedy",
            "temperature": 1.0,
            "top_p": 0.9,
        },
        tools=[
            {
                "type": "brave_search",
                "engine": "brave",
                "api_key": os.getenv("BRAVE_SEARCH_API_KEY"),
            }
        ],
        tool_choice="auto",
        tool_prompt_format="function_tag",
        input_shields=[],
        output_shields=[],
        enable_session_persistence=False,
    )

    agent = Agent(client, agent_config)
    session_id = agent.create_session("test-session")
    print(f"Created session_id={session_id} for Agent({agent.agent_id})")

    user_prompts = [
        """
        Query: What methods are best for finetuning llama?

        Specialist answers:Based on the provided context, it appears that finetuning LLaMA is not directly mentioned in the code snippets. However, I can infer that finetuning LLaMA is likely to be performed using the `llama_recipes.finetuning` module.

        In the `finetuning.py` file, the `main` function is imported from `llama_recipes.finetuning`, which suggests that this file contains the code for finetuning LLaMA.

        To finetun...<more>...Guard.

        As for finetuning Llama in general, it seems that the provided context only provides information on finetuning Llama Guard, which is a specific application of the Llama model. For general finetuning of Llama, you may need to refer to the official documentation or other external resources.

        However, based on the provided context, it seems that the `finetune_vision_model.md` file in the `quickstart` folder may provide some information on finetuning Llama for vision tasks.
        """
    ]

    for prompt in user_prompts:
        response = agent.create_turn(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            session_id=session_id,
        )
        for log in EventLogger().log(response):
            log.print()


def main(
    host: str,
    port: int,
    use_https: bool = False,
    disable_safety: bool = False,
    cert_path: Optional[str] = None,
):
    asyncio.run(run_main(host, port, use_https, disable_safety, cert_path))


if __name__ == "__main__":
    fire.Fire(main)