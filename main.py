import asyncio
import uuid
from workflow.task_graph import build_graph
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import sqlite3
from fastapi import FastAPI,Request
from fastapi.staticfiles import StaticFiles
import uvicorn
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSqliteSaver.from_conn_string("langgraph.db") as memory:
        app.state.graph = build_graph(checkpointer=memory)
        yield

app = FastAPI(
    title="智能助理API",
    description="这是一个基于LangGraph构建的智能助理API。",
    lifespan=lifespan
)


app.mount("/static", StaticFiles(directory="static"), name="static")


class ChatRequest(BaseModel):
    user_input: str
    session_id:str | None = None


@app.post("/chat")
async def chat(chat_request: ChatRequest, request: Request):
    """接收用户输入并且返回接口输出"""

    graph = request.app.state.graph
    session_id = chat_request.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}
    inputs = {"input": chat_request.user_input}
    final_state = await graph.ainvoke(inputs, config=config)

    ai_response = "Sorry, I couldn't generate a response."
    if final_state and final_state.get("messages"):
        last_message = final_state["messages"][-1]
        if hasattr(last_message, 'type') and last_message.type == 'ai':
            ai_response = last_message.content

    return {"ai_response": ai_response, "session_id": session_id}


@app.get("/")
async def root():
    """
    根路径，提供一个简单的欢迎信息。
    """
    return {"message": "Welcome to the LangGraph Chat API. Please use the /chat endpoint to interact."}


if __name__ == "__main__":

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)