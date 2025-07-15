import json
from .model import solve_dc_opf


def run_dc_opf(config: str) -> str:
    data = json.loads(config)
    result = solve_dc_opf(data["adn"])
    return json.dumps({"result": result})
