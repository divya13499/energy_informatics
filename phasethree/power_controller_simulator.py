import mosaik_api

META = {
    'api_version': '3.0',
    'type': 'time-based',
    'models': {
        'Controller': {
            'public': True,
            'params': [],
            'attrs': ['dummy_output'],
        }
    },
}

class ControllerSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(META)
        self.entities = {}
        self.eid_prefix = 'Controller'

    def init(self, sid, time_resolution, **sim_params):
        self.sid = sid
        return self.meta

    def create(self, num, model, **model_params):
        entities = []
        for i in range(num):
            eid = f'{self.eid_prefix}-{i}'
            self.entities[eid] = {'dummy_output': 0.0}
            entities.append({'eid': eid, 'type': model})
        return entities

    def step(self, time, inputs, max_advance=None):
        print(f"[step] {self.sid} at time {time}")
        return time + 60  # 1-minute timestep

    def get_data(self, outputs):
        print(f"[get_data] Outputs requested: {outputs}")
        data = {}
        for eid, attrs in outputs.items():
            model = self.entities[eid]
            data[eid] = {}
            for attr in attrs:
                if attr == 'summed_output':
                    data[eid][attr] = model.summed_output  # Or whatever variable you use
                elif attr == 'current_value':
                    data[eid][attr] = model.current_value  # Same here
        print(f"[get_data] Returning: {data}")
        return data


def main():
    mosaik_api.start_simulation(ControllerSim())

if __name__ == '__main__':
    main()
