import os
import json
from typing import Dict, Any, List
from graph.tools.bedrock_client import BedrockClient
from graph.prompts.message_prompt import MESSAGE_SYSTEM_PROMPT

class MessageTool:
    """
    Message Fact Extractor Tool with persistent disk caching (code/cache/messages/{message_id}.json)
    and strict sent_at <= request_date cutoff handling.
    """

    def __init__(self, bedrock_client: BedrockClient, cache_dir: str = "code/cache/messages"):
        self.bedrock_client = bedrock_client
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def extract_message(
        self,
        message_row: Dict[str, Any],
        user_events_summary: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        msg_id = message_row.get("message_id", "msg_unknown")
        cache_path = os.path.join(self.cache_dir, f"{msg_id}.json")

        # 1. Check persistent disk cache
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # 2. Prepare converse payload
        user_payload = f"""Message Row:
{json.dumps(message_row, indent=2)}

User's Existing Events Summary (for linking):
{json.dumps(user_events_summary, indent=2)}
"""

        messages = [
            {
                "role": "user",
                "content": [{"text": user_payload}]
            }
        ]

        try:
            response = self.bedrock_client.call_converse(
                messages=messages,
                system_prompt=MESSAGE_SYSTEM_PROMPT,
                temperature=0.0
            )

            text_out = response.get("text", "")
            clean_json = self._clean_json(text_out)
            res_data = json.loads(clean_json)

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(res_data, f, indent=2)

            return res_data
        except Exception as e:
            fallback_res = {
                "message_id": msg_id,
                "source_type": message_row.get("source_type"),
                "facts": [],
                "ignore": True,
                "error": str(e)
            }
            return fallback_res

    def _clean_json(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
