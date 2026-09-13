import sys

try:
    from langgraph.graph import StateGraph as LGStateGraph, END
    USE_LANGGRAPH_LIB = True
except ImportError:
    USE_LANGGRAPH_LIB = False
    END = "END"

from graph.state import AgentState
from graph.nodes.node1_reconciliation import node1_reconcile_records
from graph.nodes.node2_case_retriever import node2_retrieve_similar_cases
from graph.nodes.node3_evidence import node3_gather_evidence
from graph.nodes.node4_summarizer import node4_synthesize_scenarios
from graph.nodes.node5_cashflow import node5_cashflow_evaluator
from graph.nodes.node6_selector import node6_selector_ranker
from graph.nodes.node7_validator import node7_guardrail_validator
from graph.tools.io_csv import DataLoader
from graph.tools.bedrock_client import BedrockClient

class LocalStateGraph:
    """
    Lightweight, zero-dependency fallback StateGraph implementation
    matching the LangGraph StateGraph API. Ensures out-of-the-box runnability
    in any clean Python runtime.
    """
    def __init__(self, state_schema):
        self.state_schema = state_schema
        self.nodes = {}
        self.edges = {}
        self.entry_point = None

    def add_node(self, name, func):
        self.nodes[name] = func

    def add_edge(self, src, dst):
        self.edges[src] = dst

    def set_entry_point(self, name):
        self.entry_point = name

    def compile(self):
        return LocalCompiledGraph(self.nodes, self.edges, self.entry_point)

class LocalCompiledGraph:
    def __init__(self, nodes, edges, entry_point):
        self.nodes = nodes
        self.edges = edges
        self.entry_point = entry_point

    def invoke(self, state):
        curr = self.entry_point
        while curr and curr != "END":
            node_fn = self.nodes[curr]
            out = node_fn(state)
            if out and isinstance(out, dict):
                state.update(out)
            curr = self.edges.get(curr, "END")
        return state

def build_agent_graph(data_loader: DataLoader, bedrock_client: BedrockClient):
    """
    Builds and compiles the LangGraph StateGraph pipeline for the Buy or Wait financial agent.
    """
    if USE_LANGGRAPH_LIB:
        builder = LGStateGraph(AgentState)
    else:
        builder = LocalStateGraph(AgentState)

    # Define Node Wrappers
    def n1(state: AgentState):
        return node1_reconcile_records(state, data_loader, bedrock_client)

    def n2(state: AgentState):
        return node2_retrieve_similar_cases(state, data_loader)

    def n3(state: AgentState):
        return node3_gather_evidence(state, data_loader)

    def n4(state: AgentState):
        return node4_synthesize_scenarios(state)

    def n5(state: AgentState):
        return node5_cashflow_evaluator(state)

    def n6(state: AgentState):
        return node6_selector_ranker(state)

    def n7(state: AgentState):
        return node7_guardrail_validator(state)

    # Add Nodes to Graph
    builder.add_node("node1_reconcile", n1)
    builder.add_node("node2_retriever", n2)
    builder.add_node("node3_evidence", n3)
    builder.add_node("node4_summarizer", n4)
    builder.add_node("node5_cashflow", n5)
    builder.add_node("node6_selector", n6)
    builder.add_node("node7_validator", n7)

    # Define Workflow Edges
    builder.set_entry_point("node1_reconcile")
    builder.add_edge("node1_reconcile", "node2_retriever")
    builder.add_edge("node2_retriever", "node3_evidence")
    builder.add_edge("node3_evidence", "node4_summarizer")
    builder.add_edge("node4_summarizer", "node5_cashflow")
    builder.add_edge("node5_cashflow", "node6_selector")
    builder.add_edge("node6_selector", "node7_validator")
    builder.add_edge("node7_validator", END)

    return builder.compile()
