from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig

from langchain.globals import set_debug

import chainlit as cl

from configparser import ConfigParser
import logging

logger = logging.getLogger(__name__)
set_debug(True)

def read_config(parser: ConfigParser, filepath: str) -> None:
    assert parser.read(filepath), f"Couldn't read config file {filepath}"

env_config = ConfigParser()
CONFIG_FILE = "./env/env.conf"
read_config(env_config, CONFIG_FILE)
OPENAI_API_KEY = env_config.get(section="OPENAI", option="OPENAI_API_KEY")


@cl.on_chat_start
async def on_chat_start():
    model = ChatOpenAI(streaming=True, openai_api_key=OPENAI_API_KEY)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You're a very knowledgeable historian who provides accurate and eloquent answers to historical questions.",
            ),
            ("human", "{question}"),
        ]
    )
    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)


@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    msg = cl.Message(content="")

    async for chunk in runnable.astream(
        {"question": message.content},
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()
