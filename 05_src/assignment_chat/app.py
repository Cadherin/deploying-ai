import gradio as gr
from assignment_chat.main import assignment_chat
from dotenv import load_dotenv
from typing import Optional
import os

from utils.logger import get_logger

_logs = get_logger(__name__)

load_dotenv('.secrets')

chat = gr.ChatInterface(
    fn=assignment_chat,
    type="messages"
)

if __name__ == "__main__":
    _logs.info('Starting Weather Chat App...')
    chat.launch()
