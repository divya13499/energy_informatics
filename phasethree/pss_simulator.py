import mosaik_api_v3
import math
import matplotlib.pyplot as plt

META = {
    "type": "time-based",
    "models": {
        "PSS": {
            "public": True,
            "params": ["nominal_power", "pressure_wave_runtime", "initial_stored_energy_wh"],
            "attrs": ["valve_opening", "pump_operation", "total_output", "turbine_generation", "stored_energy_wh"],
        }
    }
}


class PSSSimulator(mosaik_api_v3.Simulator):

    def __init__(self):
        super().__init__(META)
        self.eid_prefix = "PSS_"
        self.entities = {}  # Maps EIDS to PSS instances
        self.time = -1

    def init(self, sid, time_resolution=1.0, eid_prefix=None):
        if float(time_resolution) != 1:
            raise ValueError("Unsupported Time resolution")
        
        if eid_prefix is not None:
            self.eid_prefix = eid_prefix
        
        self.sid = sid
        return self.meta

    def create(self, num, model, **model_params):
        wave_rt = model_params["pressure_wave_runtime"]
        nominal_power = model_params["nominal_power"]
        energy = model_params["initial_stored_energy_wh"]
        next_eid = len(self.entities)
        entities = []

        for i in range(next_eid, next_eid + num):
            model_instance = PSS(wave_rt, nominal_power, energy)
            eid = "%s%d" % (self.eid_prefix, i)
            self.entities[eid] = model_instance
            entities.append({"eid": eid, "type": model})
        return entities



    def step(self, time, inputs, max_advance):
        delta = time - self.time
        # Check for new delta and do step for each model instance
        for eid, model_instance in list(self.entities.items()):
            if eid in inputs:
                attrs = inputs[eid]
                assert len(attrs["valve_opening"].keys()) == 1
                assert len(attrs["pump_operation"].keys()) == 1
                input_signal = list(attrs["valve_opening"].values())[0]
                pump_operation = list(attrs["valve_opening"].values())[0]
                transfer_function_time = delta
                if input_signal == model_instance.last_input:
                    transfer_function_time += model_instance.last_time
                model_instance.compute_at_time(transfer_function_time, input_signal)
                model_instance.compute_storage_change(pump_operation, delta)
        self.time = time
        print(f"[step] {self.sid} at time {time}")
        return time + 1


    def get_data(self, outputs):
        print(f"[get_data] Outputs requested: {outputs}")
        data = {}
        for eid, attrs in list(outputs.items()):
            model = self.entities[eid]
            # data["time"] = self.time
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta["models"]["PSS"]["attrs"]:
                    raise ValueError("Unknown output attribute %s" % attr)
                if attr == "total_output":
                    data[eid][attr] = -model.get_value() + model.pump_operation
                if attr == "stored_energy_wh":
                    data[eid][attr] = model.get_energy()
                if attr == "turbine_generation":
                    data[eid][attr] = model.get_value()
        print(f"[get_data] Returning: {data}")
        return data



class PSS():
    
    def __init__(self, pressure_wave_runtime, nominal_power, energy):
        self.pressure_wave_runtime = pressure_wave_runtime
        self.nominal_power = nominal_power
        self.last_input = None
        self.last_time = None
        self.value = 0
        self.energy = energy
        self.pump_operation = 0

    def compute_at_time(self, time, input):
        # output = (self.pressure_wave_runtime + 4) * t / self.pressure_wave_runtime + (self.pressure_wave_runtime - 2) * (1-math.exp(-1 / self.pressure_wave_runtime * t)) / self.pressure_wave_runtime / self.pressure_wave_runtime
        time_scale = 1000
        t = time * time_scale
        output = 1 - 3 * math.exp(-1/self.pressure_wave_runtime * t) 
        scaled_output = output * input / self.nominal_power
        self.last_time = time
        self.last_input = input
        self.value = self.value + scaled_output * self.nominal_power

    def compute_storage_change(self, pump_operation, delta):
        # delta in seconds
        delta_in_h = delta / 3600
        self.energy -= self.value * delta_in_h  
        self.energy -= pump_operation * delta_in_h  

    def get_value(self):
        return self.value
    
    def get_energy(self):
        return self.energy


if __name__ == "__main__":
    testee = PSS(1/400, 1)
    output = []
    output_sum = []
    times = []
    for i in range(1, 1000):
        output.append(testee.compute_at_time(i, 1))
        times.append(i)
    print(output)
    plt.plot(times, output)
    plt.show()