from typing import Dict, Any
from graph.state import AgentState
from graph.tools.bedrock_client import BedrockClient
from graph.tools.ocr_tool import OCRTool
from graph.tools.message_tool import MessageTool
from graph.tools.calculator_tool import Node1CalculatorTool
from graph.tools.io_csv import DataLoader

def node1_reconcile_records(state: AgentState, data_loader: DataLoader, bedrock_client: BedrockClient) -> Dict[str, Any]:
    """
    Node 1 LangGraph Node: Past vs Updated Records Reconciliation.
    Reads user profile, events, messages, images, runs OCR and message extraction,
    and calculates updated_record and change_list.
    """
    user_id = state["user_id"]
    request_date = state["request_date"]

    user_profile = data_loader.get_user_profile(user_id) or {}
    user_events = data_loader.get_user_events(user_id)
    user_messages = data_loader.get_user_messages(user_id)
    user_images = data_loader.images_by_user.get(user_id, [])

    ocr_tool = OCRTool(bedrock_client=bedrock_client)
    message_tool = MessageTool(bedrock_client=bedrock_client)
    calculator = Node1CalculatorTool()

    # 1. Process Message Extractions (Filter sent_at <= request_date)
    message_facts = []
    events_summary = [{"event_id": e["event_id"], "category": e["category"], "description": e["description"]} for e in user_events]

    for msg in user_messages:
        msg_date = msg.get("sent_at", "").split("T")[0]
        if msg_date <= request_date:
            fact_res = message_tool.extract_message(msg, events_summary)
            fact_res["sent_at"] = msg.get("sent_at")
            message_facts.append(fact_res)

    # 2. Process Image OCR Extractions
    ocr_results = []
    for img_info in user_images:
        image_id = img_info["image_id"]
        rel_event_id = img_info.get("related_event_id")
        image_path = f"dataset/media/images/{image_id}.png"

        linked_event = {}
        if rel_event_id:
            linked_event = next((e for e in user_events if e["event_id"] == rel_event_id), {})

        # Related messages for this image
        rel_msgs = [m.get("message_text") for m in user_messages if m.get("related_event_id") == rel_event_id]

        ocr_res = ocr_tool.extract_image(
            image_id=image_id,
            image_path=image_path,
            linked_event=linked_event,
            related_messages=rel_msgs
        )
        ocr_results.append(ocr_res)

    # 3. Calculate Updated Record
    past_rec, updated_rec, change_list = calculator.reconcile_records(
        user_profile=user_profile,
        user_events=user_events,
        message_facts=message_facts,
        ocr_results=ocr_results,
        request_date=request_date
    )

    return {
        "past_record": past_rec,
        "updated_record": updated_rec,
        "change_list": change_list
    }
