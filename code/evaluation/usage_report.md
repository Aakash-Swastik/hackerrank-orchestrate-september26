# Token Usage and Cost Analysis Report

## Full Dataset Run Summary

- **Model Provider**: AWS Bedrock
- **Model Name / ID**: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- **Total Requests Evaluated**: 250
- **Total Model Calls**: 0
- **Total Input Tokens**: 0
- **Total Output Tokens**: 0
- **Total Tokens**: 0
- **Average Tokens per Request**: 0.0
- **Estimated Total Cost**: $0.0000 USD
- **Estimated Average Cost per Request**: $0.0000 USD

## Efficiency & Caching Notes
- All multimodal image OCR calls (16 images) and message fact extractions (215 messages) utilize persistent disk caching (`code/cache/ocr/` and `code/cache/messages/`).
- Deterministic 90-day daily balance simulations, currency conversions, and scenario ranking operate natively in Python, eliminating redundant API token consumption.
