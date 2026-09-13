import os
import json
import base64
from typing import Dict, Any, Optional
from graph.tools.bedrock_client import BedrockClient
from graph.prompts.ocr_prompt import OCR_SYSTEM_PROMPT

class OCRTool:
    """
    Multimodal OCR tool with persistent disk caching (code/cache/ocr/{image_id}.json)
    and context-aware candidate extraction.
    """

    def __init__(self, bedrock_client: BedrockClient, cache_dir: str = "code/cache/ocr"):
        self.bedrock_client = bedrock_client
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def extract_image(
        self,
        image_id: str,
        image_path: str,
        linked_event: Dict[str, Any],
        related_messages: Optional[list] = None
    ) -> Dict[str, Any]:
        cache_path = os.path.join(self.cache_dir, f"{image_id}.json")

        # 1. Check persistent disk cache first
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        # 2. Prepare Bedrock Converse payload with image bytes + context
        if not os.path.exists(image_path):
            fallback_res = {
                "image_id": image_id,
                "related_event_id": linked_event.get("event_id"),
                "extraction_status": "needs_review",
                "selection": {"chosen_amount": None, "selection_reasoning": "Image file missing on disk"}
            }
            return fallback_res

        try:
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()
                base64_image = base64.b64encode(image_bytes).decode("utf-8")

            context_text = f"""Linked Event Details:
{json.dumps(linked_event, indent=2)}

Related Messages:
{json.dumps(related_messages or [], indent=2)}
"""

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": "png",
                                "source": {"bytes": base64_image}
                            }
                        },
                        {
                            "text": context_text
                        }
                    ]
                }
            ]

            response = self.bedrock_client.call_converse(
                messages=messages,
                system_prompt=OCR_SYSTEM_PROMPT,
                temperature=0.0
            )

            # Parse JSON output from model text
            text_out = response.get("text", "")
            clean_json = self._clean_json(text_out)
            res_data = json.loads(clean_json)

            # Save to disk cache
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(res_data, f, indent=2)

            return res_data
        except Exception as e:
            fallback_res = {
                "image_id": image_id,
                "related_event_id": linked_event.get("event_id"),
                "extraction_status": "error",
                "selection": {"chosen_amount": None, "selection_reasoning": f"OCR exception: {str(e)}"}
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
