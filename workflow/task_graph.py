from langchain_core.messages import AnyMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph,START,END
from typing import Annotated,List,Literal
from typing_extensions import TypedDict, Any
from langchain_core.documents import Document
from nodes.manager_agent import create_manager_router_chain,manager_process
from nodes.research_agent import research_process
from nodes.put_in_db_node import put_in_db_node
from nodes.find_node import find
from nodes.writer_agent import writer_process
from nodes.qa_agent_node import create_qa_agent,qa_process
from nodes.other_chat_node import other_chat_process


class State(TypedDict):
    input:str
    messages: Annotated[List[AnyMessage], lambda x, y: x + y]
    documents:List[Document]
    report_summary:str
    raw_text:str
    next_node:str
    current_task:str
    serialized_vectorstore: bytes
    required_report:bool
    awaiting_clarification:bool
    rewritten_input:str
    clarification_type:str




def manager_node(state:State):
    """
    管理智能体节点，负责根据用户输入和当前状态决定下一个执行的智能体节点。
    它使用一个路由链来分析用户的查询，并选择最合适的智能体来处理任务。
    """
    res = manager_process(state)
    return res


def research_node(state:State):
    """接受用户输入，进行信息检索和初步分析，将结果存入state"""
    print("---调用 Research 节点 搜索信息---")
    research_agent = research_process(state)
    return research_agent


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


def qa_node(state: State):
    """
    节点函数：根据检索到的文档和聊天历史生成最终答案。
    """
    res = qa_process(state)
    return res


def writer_node(state:State):
    """负责整理报告并写入文件"""
    print("---调用 Writer 节点，生成报告---")
    final_result = writer_process(state)
    out_put = final_result.get("output", "")
    print(f"节点信息: {out_put}")
    return {
        "report_summary": out_put,
        "messages": [AIMessage(content=out_put)]
    }


def other_chat_node(state:State):
    res = other_chat_process(state)
    return res






def route_after_manage(state:State):
    """根据 manager 的决策路由到下一个节点"""
    next_node = state.get("next_node")
    print("next_node:", next_node)
    if next_node == "research_agent":
        return "research_agent"
    elif next_node == "writer_agent":
        return "research_agent"
    elif next_node == "qa_agent":
        return "qa_agent"
    elif next_node == "code_agent":
        print("code_agent 节点尚未实现，路由到 END")
        return END
    elif next_node == "other_chat_node":
        return "other_chat_node"
    elif next_node == "END":
        return END
    else:
        print(f"未知的 next_node: {next_node}，路由到 END")
        return END


def route_after_find(state: State):
    """在 find_node 后，根据原始意图决定去向"""
    report_choice = state.get("required_report")
    next_node = state.get("next_node")
    print("find_node 后的 next_node:", next_node)
    print(f"是否需要生成报告: 原始意图是 {report_choice}")
    # if next_node == "qa_agent":
    #     return "qa_node"
    if report_choice is True:
    # if report_choice is True:
        return "writer_agent"
    elif next_node == "writer_agent":
        return "writer_agent"
    elif next_node == "research_agent":
        return "research_agent"
    else:
        return "qa_node"





def build_graph(checkpointer):
    workflow = StateGraph(State)

    workflow.add_node("manager_agent", manager_node)
    workflow.add_node("research_agent", research_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("find_node", find_answer_node)
    workflow.add_node("writer_agent", writer_node)
    workflow.add_node("qa_node", qa_node)
    workflow.add_node("other_chat_node", other_chat_node)


    workflow.set_entry_point("manager_agent")


    workflow.add_conditional_edges(
        "manager_agent",
        route_after_manage,
        {
            "research_agent": "research_agent",
            "writer_agent": "writer_agent",
            # "find_node": "find_node",
            "other_chat_node": "other_chat_node",
            "qa_agent": "qa_node",
            "code_agent": END,  # code_agent 节点尚未实现，直接路由到 END
            END: END
        }
    )

    workflow.add_edge("research_agent", "rag_node")
    workflow.add_edge("rag_node", "find_node")

    # workflow.add_edge("find_node", "qa_node")

    workflow.add_conditional_edges(
        "find_node",
        route_after_find,
        {
            "qa_node": "qa_node",
            "writer_agent": "writer_agent"
        }
    )

    workflow.add_edge("writer_agent", END)
    workflow.add_edge("qa_node", END)
    workflow.add_edge("other_chat_node", END)



    app = workflow.compile(checkpointer=checkpointer)
    return app
