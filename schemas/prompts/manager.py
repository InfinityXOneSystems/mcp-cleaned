import yaml
from pathlib import Path
import jsonschema
import os
import logging

logger = logging.getLogger(__name__)
PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> dict:
    path = PROMPT_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data


def prompt_requires_approval(name: str) -> bool:
    p = load_prompt(name)
    return bool(p.get('approval_required', False))


def validate_output_shape(prompt: dict, output: dict) -> bool:
    # basic validation against output_shape types
    shape = prompt.get('output_shape', {})
    # build a simple json schema
    props = {}
    for k, t in shape.items():
        if t == 'string' or t == 'str':
            props[k] = {"type":"string"}
        elif t in ('number','float','int'):
            props[k] = {"type":"number"}
        elif t == 'integer':
            props[k] = {"type":"integer"}
        else:
            props[k] = {"type":"string"}
    schema = {"type":"object","properties":props,"required":list(shape.keys())}
    try:
        jsonschema.validate(instance=output, schema=schema)
        return True
    except Exception as e:
        logger.debug(f"Output validation failed: {e}")
        return False


def dry_run_prompt(name: str, input_signals: dict) -> dict:
    # For now, this maps to stubbed functions in intelligence_endpoints
    # This avoids calling external LLMs until enabled
    from intelligence_endpoints import llm_stub_arrival, summarize_business_from_url
    if name == 'arrival_v1':
        return llm_stub_arrival(input_signals)
    if name == 'mirror_business_v1':
        url = input_signals.get('url')
        return summarize_business_from_url(url or 'https://example.com')
    if name == 'pipeline_shadow_v1':
        # call pipeline stub
        from intelligence_endpoints import pipeline_shadow as ps
        return {'lost_estimate': 0.0, 'fix':'simulate','confidence':0.5}
    return {}
