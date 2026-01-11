# API Documentation

This directory contains the auto-generated OpenAPI specification for the Antigravity Backend API.

## File Contents

- `openapi.json`: The raw OpenAPI 3.1.0 specification in JSON format.

## How to Regenerate

To regenerate the `openapi.json` file (e.g., after adding new endpoints), run the following command from the `backend` directory:

```bash
uv run python extract_openapi.py
```

This will update `agent_thoughts/openapi.json` with the latest API schema.
