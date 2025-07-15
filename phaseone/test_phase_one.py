import json
from phaseone import run_dc_opf

test_config = {
  "adn": {
    "bus": [
      {"id": 0, "P_G_w": None, "P_D_w": None, "slack": True},
      {"id": 1, "P_G_w": 3000, "P_D_w": 1500, "slack": False},
      {"id": 2, "P_G_w": None, "P_D_w": 3500, "slack": False},
      {"id": 3, "P_G_w": 5500, "P_D_w": 500, "slack": False}
    ],
    "bss": [
      {"bus_id": 1, "P_BSS_max_w": 3000, "E_BSS_max_wh": 10000, "E_BSS_init_wh": 9100},
      {"bus_id": 3, "P_BSS_max_w": 3000, "E_BSS_max_wh": 10000, "E_BSS_init_wh": 9400}
    ],
    "line": [
      {"from_bus_id": 0, "to_bus_id": 1, "b_siemens": 9, "P_line_max_w": 15000},
      {"from_bus_id": 1, "to_bus_id": 2, "b_siemens": 7, "P_line_max_w": 15000},
      {"from_bus_id": 0, "to_bus_id": 3, "b_siemens": 4, "P_line_max_w": 15000}
    ],
    "costs": {
      "import_now": 50,
      "import_next": 60,
      "export_now": 40,
      "export_next": 45
    },
    "energy_imbalance_next_W": 1000
  }
}

if __name__ == "__main__":
    config_str = json.dumps(test_config)
    result = run_dc_opf(config_str)
    print(json.dumps(json.loads(result), indent=2))
