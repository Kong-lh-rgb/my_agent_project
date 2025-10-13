from langchain_core.messages import AnyMessage, HumanMessage
from langgraph.graph import StateGraph,START,END
from typing import Annotated,List,Literal
from typing_extensions import TypedDict, Any
from langchain_core.documents import Document
from nodes.manager_agent import create_manager_router_chain
from nodes.research_agent import create_research_agent
from nodes.put_in_db_node import put_in_db_node
from nodes.find_node import find
from nodes.writer_agent import create_writer_agent





class State(TypedDict):
    input:str
    messages: Annotated[List[AnyMessage], lambda x, y: x + y]
    documents:List[Document]
    report_summary:str
    raw_text:str
    next_node:str
    current_task:str
    serialized_vectorstore: bytes


def manager_node(state:State):
    """
    管理智能体节点，负责根据用户输入和当前状态决定下一个执行的智能体节点。
    它使用一个路由链来分析用户的查询，并选择最合适的智能体来处理任务。
    """
    print("---调用 Manager 节点，开始进行意图判断---")
    messages = state.get("messages", []) + [HumanMessage(content=state["input"])]
    if not messages[-1].content:
        print("错误：最新的消息内容为空")
        return {"next_node": "END"}

    manager_chain = create_manager_router_chain()
    res = manager_chain.invoke({
        "messages": messages,
        "input": state["input"],
    })

    print(f"Manager 决策: 下一步路由到 -> {res.destination}")
    print(f"Manager 决策: 下一步任务 -> {res.next_input}")

    return {
        "messages": messages,
        "next_node":res.destination,
        "current_task":res.next_input
    }


def research_node(state:State):
    """接受用户输入，进行信息检索和初步分析，将结果存入state"""
    print("---调用 Research 节点 搜索信息---")
    research_agent = create_research_agent()
    result = research_agent.invoke({"input":state["current_task"]})
    return {
        "raw_text":result["output"]
    }


def rag_node(state:State):
    """接受原始文本，对文本进行分块，向量化存入数据库"""
    print("对数据进行向量化中...")
    print("---调用 RAG 节点---")
    return put_in_db_node(state)


def find_answer_node(state:State):
    """接受用户问题到向量库中进行检索"""
    print("从向量库中检索相关信息...")
    print("---调用 Find Answer 节点---")
    res = find(state)
    return res


def writer_node(state:State):
    """负责整理报告并写入文件"""
    print("---调用 Writer 节点，生成报告---")
    final_result = create_writer_agent(state)
    return {
        "report_summary": final_result.get("report_summary", "")
    }

def route_after_manage(state:State):
    """根据 manager 的决策路由到下一个节点"""
    next_node = state.get("next_node")
    print("next_node:", next_node)
    if next_node == "research_agent":
        return "research_agent"
    elif next_node == "writer_agent":
        return "writer_agent"
    elif next_node == "code_agent":
        print("code_agent 节点尚未实现，路由到 END")
        return END
    elif next_node == "END":
        return END
    else:
        print(f"未知的 next_node: {next_node}，路由到 END")
        return END

def build_graph():
    workflow = StateGraph(State)

    workflow.add_node("manager_agent", manager_node)
    workflow.add_node("research_agent", research_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("find_node", find_answer_node)
    workflow.add_node("writer_agent", writer_node)

    # 执行流程
    workflow.set_entry_point("manager_agent")

    #条件路由
    workflow.add_conditional_edges(
        "manager_agent",
        route_after_manage,
        {
            "research_agent": "research_agent",
            "writer_agent": "writer_agent",
            "code_agent": END,  # code_agent 节点尚未实现，直接路由到 END
            END: END
        }
    )

    workflow.add_edge("research_agent", "rag_node")
    workflow.add_edge("rag_node", "find_node")
    workflow.add_edge("find_node", "writer_agent")
    workflow.add_edge("writer_agent", END)

    app = workflow.compile()
    return app
