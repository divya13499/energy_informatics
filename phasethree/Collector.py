import collections
import json
import mosaik_api_v3

META = {
    'type': 'event-based',
    'models': {
        'Monitor': {
            'public': True,
            'any_inputs': True,
            'params': [],
            'attrs': [],
        },
    },
    "extra_methods": [
        "get_final_data"
    ]
}

class Collector(mosaik_api_v3.Simulator):
    def __init__(self):
        super().__init__(META)
        self.eid = None
        self.data = collections.defaultdict(lambda: collections.defaultdict(dict))
        self.data_out_path = None

    def init(self, sid, time_resolution, data_out):
        self.data_out_path = data_out
        return self.meta

    def create(self, num, model):
        if num > 1 or self.eid is not None:
            raise RuntimeError('Can only create one instance of Monitor.')
        self.eid = 'Monitor'
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs, max_advance):
        for entity_id, attrs in inputs.items():
            for attr, values in attrs.items():
                for src, value in values.items():
                    self.data[src][attr][time] = value
        
        print(f"[Collector] Step time {time}, inputs received: {inputs}")
        return None

    def finalize(self):
        print('Collected data:')
        for sim, sim_data in sorted(self.data.items()):
            print(f'- {sim}:')
            for attr, values in sorted(sim_data.items()):
                vals = [values[key] for key in values]
                print(f'  - {attr}: {vals}')

        output_file = self.data_out_path or 'output_data.json'
        with open(output_file, 'w') as f:
            json.dump(self.data, f, indent=4, default=str)
        print(f'Data written to {output_file}')


if __name__ == '__main__':
    mosaik_api_v3.start_simulation(Collector())
