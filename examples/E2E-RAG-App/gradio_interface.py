import asyncio
import json
import os
import uuid
from queue import Queue
from threading import Thread
from typing import AsyncGenerator, Generator, List, Optional

import chromadb
import gradio as gr
import requests
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client.types.agent_create_params import AgentConfig
from llama_stack_client.types.memory_insert_params import Document


# Load environment variables
load_dotenv()

HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "5000"))
GRADIO_SERVER_PORT = int(os.getenv("GRADIO_SERVER_PORT", "7861"))

MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.2-3B-Instruct")
DOCS_DIR = os.getenv("DOCS_DIR", "./example_data")


class LlamaChatInterface:
    def __init__(self, host: str, port: int, docs_dir: str):
        self.host = host
        self.port = port
        self.docs_dir = docs_dir
        self.client = LlamaStackClient(base_url=f"http://{host}:{port}")
        self.agent = None
        self.session_id = None
        self.memory_bank_id = "test_bank_235"

    async def initialize_system(self):
        """Initialize the entire system including memory bank and agent."""
        await self.setup_memory_bank()
        await self.initialize_agent()

    async def setup_memory_bank(self):
        """Set up the memory bank if it doesn't exist."""
        providers = self.client.providers.list()
        provider_id = providers["memory"][0].provider_id
        memory_banks = self.client.memory_banks.list()
        print(f"Memory banks: {memory_banks}")

        # Check if memory bank exists by identifier
        if any(bank.identifier == self.memory_bank_id for bank in memory_banks):
            print(f"Memory bank '{self.memory_bank_id}' exists.")
        else:
            print(
                f"Memory bank '{self.memory_bank_id}' does not exist. Creating...")
            self.client.memory_banks.register(
                memory_bank_id=self.memory_bank_id,
                params={
                    "embedding_model": "all-MiniLM-L6-v2",
                    "chunk_size_in_tokens": 100,
                    "overlap_size_in_tokens": 10,
                },
                provider_id=provider_id,
            )
            await self.load_documents()
            print(f"Memory bank registered.")

    async def load_documents(self):
        """Load documents from the specified directory into memory bank."""
        documents = []
        for filename in os.listdir(self.docs_dir):
            if filename.endswith((".txt", ".md")):
                file_path = os.path.join(self.docs_dir, filename)
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    document = Document(
                        document_id=filename,
                        content=content,
                        mime_type="text/plain",
                        metadata={"filename": filename},
                    )
                    documents.append(document)

        if documents:
            self.client.memory.insert(
                bank_id=self.memory_bank_id,
                documents=documents,
            )
            print(f"Loaded {len(documents)} documents from {self.docs_dir}")

    async def initialize_agent(self):
        """Initialize the agent with model registration and configuration."""

        if "1b" in MODEL_NAME:
            model_name = "Llama3.2-1B-Instruct"
        elif "3b" in MODEL_NAME:
            model_name = "Llama3.2-3B-Instruct"
        elif "8b" in MODEL_NAME:
            model_name = "Llama3.1-8B-Instruct"
        else:
            model_name = MODEL_NAME

        agent_config = AgentConfig(
            model=model_name,
            instructions="You are a helpful assistant that can answer questions based on provided documents. Return your answer short and concise, less than 50 words.",
            sampling_params={"strategy": "greedy",
                             "temperature": 1.0, "top_p": 0.9},
            tools=[
                {
                    "type": "memory",
                    "memory_bank_configs": [
                        {"bank_id": self.memory_bank_id, "type": "vector"}
                    ],
                    "max_tokens_in_context": 300,
                    "max_chunks": 5,
                }
            ],
            tool_choice="auto",
            tool_prompt_format="json",
            enable_session_persistence=True,
        )
        self.agent = Agent(self.client, agent_config)
        self.session_id = self.agent.create_session(f"session-{uuid.uuid4()}")

    def chat_stream(
        self, message: str, history: List[List[str]]
    ) -> Generator[List[List[str]], None, None]:
        """Stream chat responses token by token with proper history handling."""

        history = history or []
        history.append([message, ""])

        if self.agent is None:
            asyncio.run(self.initialize_system())

        response = self.agent.create_turn(
            messages=[{"role": "user", "content": message}],
            session_id=self.session_id,
        )

        current_response = ""
        for log in EventLogger().log(response):
            log.print()
            if hasattr(log, "content"):
                current_response += log.content
                history[-1][1] = current_response
                yield history.copy()


def create_gradio_interface(
    host: str = HOST,
    port: int = PORT,
    docs_dir: str = DOCS_DIR,
):
    chat_interface = LlamaChatInterface(host, port, docs_dir)

    with gr.Blocks(theme=gr.themes.Soft()) as interface:
        gr.Markdown("# LlamaStack Chat")

        chatbot = gr.Chatbot(bubble_full_width=False,
                             show_label=False, height=400)
        msg = gr.Textbox(
            label="Message",
            placeholder="Type your message here...",
            show_label=False,
            container=False,
        )
        with gr.Row():
            submit = gr.Button("Send", variant="primary")
            clear = gr.Button("Clear")

        gr.Examples(
            examples=[
                "What topics are covered in the documents?",
                "Can you summarize the main points?",
                "Tell me more about specific details in the text.",
            ],
            inputs=msg,
        )

        def clear_chat():
            return [], ""

        submit_event = msg.submit(
            fn=chat_interface.chat_stream,
            inputs=[msg, chatbot],
            outputs=chatbot,
            queue=True,
        ).then(
            fn=lambda: "",
            outputs=msg,
        )

        submit_click = submit.click(
            fn=chat_interface.chat_stream,
            inputs=[msg, chatbot],
            outputs=chatbot,
            queue=True,
        ).then(
            fn=lambda: "",
            outputs=msg,
        )

        clear.click(clear_chat, outputs=[chatbot, msg], queue=False)

        msg.submit(lambda: None, None, None, api_name=False)
        interface.load(fn=chat_interface.initialize_system)

    return interface


if __name__ == "__main__":
    # Create and launch the Gradio interface
    interface = create_gradio_interface()
    interface.launch(
        server_name=HOST, server_port=GRADIO_SERVER_PORT, share=True, debug=True
    )
