from os import environ
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_vertexai import ChatVertexAI

from typing import Literal
from typing_extensions import TypedDict

from langgraph.graph import MessagesState
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent

print("graph: setting environment")
environ["LANGCHAIN_TRACING_V2"]="true"
environ["LANGCHAIN_ENDPOINT"]="https://eu.api.smith.langchain.com"
#environ["LANGCHAIN_API_KEY"]="lsv2_"
#environ["LANGCHAIN_PROJECT"]="afprojekt"

# members = ["extractor", "assessor", "int_assessor"]
members = ["extractor", "assessor"]
# Our team supervisor is an LLM node. It just picks the next agent to process
# and decides when the work is completed
options = members + ["FINISH"]

print("graph: setting class Router")
class Router(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""

    next: Literal[*options]

print("graph: setting llm ChatVertexAI")
llm = ChatVertexAI(
    model="gemini-2.0-flash-exp",
    temperature=0,
    max_tokens=8192,
    timeout=None,
    max_retries=2,
)

# Create Agent worker extractor
extract_agent = create_react_agent(
    llm, tools=[], state_modifier="You are a pdf extractor. DO NOT do any math. You extracts transactions from given pdf file and outputs them in CSV format." # @TODO: insert my system message
)

# Create Agent worker assessor
assert_agent = create_react_agent(
    llm, tools=[], state_modifier="You are a csv assessor. DO NOT do any math. You simply check if given user input is in CSV format" # @TODO: insert my system message
)

def supervisor_node(state: MessagesState) -> Command[Literal[*members, "__end__"]]:
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        f" following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )
    messages = [
        {"role": "system", "content": system_prompt},
    ] + state["messages"]
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    if goto == "FINISH":
        goto = END

    return Command(goto=goto)

def extract_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = extract_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="extract_agent")
            ]
        },
        goto="supervisor",
    )

def assert_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    result = assert_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="assessor_agent")
            ]
        },
        goto="supervisor",
    )

print("graph: Building graph")
builder = StateGraph(MessagesState)
builder.add_edge(START, "supervisor")
builder.add_node("supervisor", supervisor_node)
builder.add_node("extractor", extract_node)
builder.add_node("assessor", assert_node)
graph = builder.compile()
graph.name = "AF_Supervisor_Graph"  # This customizes the name in LangSmith

# print("graph: Saving image")
# graph.get_graph().draw_mermaid_png(output_file_path=f"{graph.name}.png")
print("graph: Asking question")
print(graph.invoke({"messages": [("user", "Extract transations from this pdf file")]}))
print("graph: Done")

# for s in graph.stream(
#     {"messages": [("user", "What's the square root of 42?")]}, subgraphs=True
# ):
#     print(s)
#     print("----")

