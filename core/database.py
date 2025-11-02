import mysql.connector
from mysql.connector import Error
from langchain_core.messages import AIMessage, HumanMessage,SystemMessage,ToolMessage,AnyMessage
from typing import List
import json
from core.config import DB_CONFIG
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"数据库连接失败因为:{e}")
        return None

def save_messages(user_id: int, conversation_id:str,messages:List[AnyMessage]):
    conn = get_db_connection()
    if not conn:
        return
    messages_to_save = []
    for msg in reversed(messages):
        if isinstance(msg,(HumanMessage,AIMessage)):
            messages_to_save.append(msg)
            if len(messages_to_save) >=2:
                break
    if not messages_to_save:
        print("没有需要保存的新消息。")
        return

    sql = "INSERT INTO chat_history (user_id, conversation_id, role, content, metadata) VALUES (%s,%s, %s, %s, %s)"
    values = []
    for msg in reversed(messages_to_save):
        if isinstance(msg,HumanMessage):
            role = 'user'
            metadata = None
        elif isinstance(msg,AIMessage):
            role = 'assistant'
            metadata = json.dumps(msg.additional_kwargs) if msg.additional_kwargs else None
        elif isinstance(msg,SystemMessage):
            role = 'system'
            metadata = None
        elif isinstance(msg,ToolMessage):
            role = 'tool'
            metadata = json.dumps({"tool_call_id": msg.tool_call_id}) if msg.tool_call_id else None
        else:
            continue
        values.append((user_id, conversation_id, role, msg.content, metadata))
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, values)
        conn.commit()
        print(f"成功保存 {len(values)} 条消息到数据库。")
    except Error as e:
        print(f"保存消息失败因为: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def load_messages(user_id:int ,session_id:str):
    conn = get_db_connection()
    if not conn:
        return []
    messages = []
    try:
        cursor = conn.cursor(dictionary = True)
        cursor.execute(
            "SELECT role, content FROM chat_history WHERE session_id = %s ORDER BY created_at ASC",
            (user_id, session_id,)
        )
        for row in cursor.fetchall():
            role = row['role']
            content = row['content']
            if role == 'user':
                messages.append(HumanMessage(content=content))
            elif role == 'assistant':
                messages.append(AIMessage(content=content))
            elif role == 'system':
                messages.append(SystemMessage(content=content))
            elif role == 'tool':
                messages.append(ToolMessage(content=content))
    except Error as e:
        print(f"加载消息失败因为: {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
    print(f"成功加载 {len(messages)} 条消息从数据库。")
    return messages
