# main.py
import uuid
from contextlib import asynccontextmanager
from datetime import timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel
import uvicorn
from fastapi.responses import RedirectResponse
# 内部模块导入
from workflow.task_graph import build_graph
from core.database import load_messages, save_messages
from core.user_db import get_user_by_username, create_user
from core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
    SECRET_KEY,
    ALGORITHM,
)
from langchain_core.messages import HumanMessage

load_dotenv()

# --- 认证设置 ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenData(BaseModel):
    username: str | None = None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


# --- 应用生命周期 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 注意：这里需要手动执行上面的 SQL 来创建和修改表
    async with AsyncSqliteSaver.from_conn_string("langgraph.db") as memory:
        app.state.graph = build_graph(checkpointer=memory)
        yield


app = FastAPI(
    title="智能助理API",
    description="这是一个基于LangGraph构建的智能助理API。",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/login.html")

# --- Pydantic 模型 ---
class UserCreate(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    user_input: str
    session_id: str | None = None


# --- API 接口 ---
@app.post("/register", summary="用户注册")
async def register(user: UserCreate):
    db_user = get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    hashed_password = get_password_hash(user.password)
    user_id = create_user(user.username, hashed_password)
    if not user_id:
        raise HTTPException(status_code=500, detail="创建用户失败")
    return {"message": "用户创建成功", "user_id": user_id}


@app.post("/token", summary="用户登录获取令牌")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/chat", summary="聊天接口（需要认证）")
async def chat(
        chat_request: ChatRequest,
        request: Request,
        current_user: dict = Depends(get_current_user)
):
    graph = request.app.state.graph
    user_id = current_user['id']

    # 如果没有提供 session_id，则创建一个新的
    session_id = chat_request.session_id or str(uuid.uuid4())

    config = {"configurable": {"thread_id": f"user_{user_id}_{session_id}"}}

    # 从数据库加载与该用户和会话相关的历史消息
    history_messages = load_messages(user_id, session_id)
    history_len_before = len(history_messages)

    inputs = {
        "input": chat_request.user_input,
        "messages": history_messages + [HumanMessage(content=chat_request.user_input)]
    }

    final_state = await graph.ainvoke(inputs, config=config)

    ai_response = "抱歉，我无法生成回复。"
    if final_state and final_state.get("messages"):
        for msg in reversed(final_state["messages"]):
            if hasattr(msg, 'type') and msg.type == 'ai' and not getattr(msg, 'tool_calls', None):
                ai_response = msg.content
                break

        all_messages = final_state["messages"]
        new_messages_to_save = all_messages[history_len_before:]

        # 保存消息时传入 user_id 和 session_id
        save_messages(user_id, session_id, new_messages_to_save)

    return {"ai_response": ai_response, "session_id": session_id}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
