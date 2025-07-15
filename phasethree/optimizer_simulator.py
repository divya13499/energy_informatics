import mosaik_api
import json
from phaseone import run_dc_opf

META = {
    'type': 'time-based',
    'models': {
        'PSS': {
            'public': True,
            'params': ['bus', 'E_PSS_max_wh', 'E_PSS_init_wh', 'P_PSS_max_w'],
            'attrs': ['p_ch_w', 'p_dis_w', 'p_total_w'],
        },
        'Load': {
            'public': True,
            'params': ['bus'],
            'attrs': ['load_p'],
        },
        'Generator': {
            'public': True,
            'params': ['bus'],
            'attrs': ['generator_p'],
        },
    },
}

class OptimizerSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.eid_prefix = 'Optimizer'
        self.entities = {}
        self.next_eid = 0

    def init(self, sid, time_resolution, **sim_params):
        self.sid = sid
        return self.meta

    def create(self, num, model, **model_params):
        entities = []
        for _ in range(num):
            eid = f'{self.eid_prefix}-{self.next_eid}'
            self.next_eid += 1

            # Initialize outputs only if applicable
            outputs = {}
            if model == 'PSS':
                outputs = {'p_ch_w': 0.0, 'p_dis_w': 0.0, 'p_total_w': 0.0}
            elif model == 'Load':
                outputs = {'load_p': 0.0}
            elif model == 'Generator':
                outputs = {'generator_p': 0.0}

            self.entities[eid] = {
                'model': model,
                'params': model_params,
                'outputs': outputs,
            }
            entities.append({'eid': eid, 'type': model})
        return entities

    def step(self, time, inputs, max_advance=None):
        for eid, data in self.entities.items():
            if data['model'] == 'PSS':
                config_dict = {
                    'adn': {
                        'bus': [],
                        'bss': [
                            {
                                'bus_id': data['params']['bus'],
                                'E_BSS_max_wh': data['params']['E_PSS_max_wh'],
                                'E_BSS_init_wh': data['params']['E_PSS_init_wh'],
                                'P_BSS_max_w': data['params']['P_PSS_max_w'],
                            }
                        ],
                        'line': [],
                        'costs': {
                            'import_now': 1.0,
                            'export_now': 1.0,
                            'import_next': 1.0,
                            'export_next': 1.0,
                        },
                        'energy_imbalance_next_W': 0.0
                    }
                }

                config_str = json.dumps(config_dict)
                result_json = run_dc_opf(config_str)
                result = json.loads(result_json)['result']['bss'][0]
                data['outputs']['p_ch_w'] = result['P_BSS_ch_w']
                data['outputs']['p_dis_w'] = result['P_BSS_dis_w']
                data['outputs']['p_total_w'] = result['P_BSS_dis_w'] - result['P_BSS_ch_w']

            elif data['model'] == 'Load':
                # Dynamically vary load: e.g., sinusoidal pattern over a day
                data['outputs']['load_p'] = 400.0 + 100.0 * ((time % 86400) / 86400)  # simulate ramp

            elif data['model'] == 'Generator':
                # Dynamically vary generation
                data['outputs']['generator_p'] = 500.0 + 100.0 * ((time % 86400) / 43200)  # simulate cycle

        print(f"[step] {self.sid} at time {time}")
        return time + 900  # 15-minute steps



    def get_data(self, outputs):
        print(f"[get_data] Outputs requested: {outputs}")
        data = {}
        for eid, attrs in outputs.items():
            entity = self.entities[eid]
            data[eid] = {}
            for attr in attrs:
                value = entity['outputs'].get(attr, 0.0)
                data[eid][attr] = value
        print(f"[get_data] Returning: {data}")
        return data


def main():
    mosaik_api.start_simulation(OptimizerSim())

if __name__ == '__main__':
    main()
