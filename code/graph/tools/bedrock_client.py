import os
import json
import base64
import urllib.request
import ssl
from typing import Dict, Any, Optional, List

class BedrockClient:
    """
    AWS Bedrock Converse API Client supporting single bearer token (AWS VeriToken),
    custom region, SSL verification toggle, and token usage accounting.
    """

    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "bedrock")
        self.bearer_token = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.ssl_verify = os.getenv("AWS_SSL_VERIFY", "false").lower() in ("true", "1", "yes")
        self.model_id = os.getenv("AWS_BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        
        # Centralized Token Usage Tracker
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0

    def call_converse(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Sends a converse call to AWS Bedrock Runtime via HTTP REST API.
        Handles text and image blocks in Anthropic/Bedrock converse payload format.
        """
        self.total_calls += 1

        if not self.bearer_token:
            # Mock / Fallback mode when API token is not yet provided by user
            return {
                "text": '{"status": "needs_review", "chosen_amount": null, "notes": "No AWS_BEARER_TOKEN_BEDROCK set"}',
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }

        endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com/model/{self.model_id}/converse"

        payload: Dict[str, Any] = {
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature
            }
        }

        if system_prompt:
            payload["system"] = [{"text": system_prompt}]

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(endpoint, data=data, headers=headers, method="POST")

        context = None
        if not self.ssl_verify:
            context = ssl._create_unverified_context()

        try:
            with urllib.request.urlopen(req, context=context) as response:
                resp_bytes = response.read()
                resp_json = json.loads(resp_bytes.decode("utf-8"))

                # Usage Extraction
                usage = resp_json.get("usage", {})
                in_tok = usage.get("inputTokens", 0)
                out_tok = usage.get("outputTokens", 0)
                self.total_input_tokens += in_tok
                self.total_output_tokens += out_tok

                # Output Extraction
                output_message = resp_json.get("output", {}).get("message", {})
                content_blocks = output_message.get("content", [])
                text_out = "".join([b.get("text", "") for b in content_blocks if "text" in b])

                return {
                    "text": text_out,
                    "usage": {"input_tokens": in_tok, "output_tokens": out_tok}
                }
        except Exception as e:
            return {
                "text": f'{{"status": "error", "error": "{str(e)}"}}',
                "usage": {"input_tokens": 0, "output_tokens": 0}
            }

    def get_usage_stats(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens
        }
