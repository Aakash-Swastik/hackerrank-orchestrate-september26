from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    LangGraph AgentState dictionary passed across graph nodes.
    """
    # Request Inputs
    request_id: str
    request_data: Dict[str, Any]
    user_id: str
    request_date: str
    
    # Node 1 Outputs
    past_record: Dict[str, Any]
    updated_record: Dict[str, Any]
    change_list: List[Dict[str, Any]]
    
    # Nodes 2 & 3 Outputs
    similar_cases: List[Dict[str, Any]]
    evidence_pack: Dict[str, Any]
    
    # Nodes 4, 5, 6, 7 Outputs
    candidate_scenarios: List[Dict[str, Any]]
    evaluated_scenarios: List[Dict[str, Any]]
    winning_scenario: Optional[Dict[str, Any]]
    final_output: Dict[str, Any]
    
    # Audit & Error Handling
    audit_log: Dict[str, Any]
    error_state: Optional[str]
