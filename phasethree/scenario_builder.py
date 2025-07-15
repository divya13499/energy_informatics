import mosaik
import json
import os
import optimizer_simulator


def create_scenario(base_dir):
    sim_config = {
        'CSV': {'python': 'mosaik_csv:CSV'},
        'PyPower': {'python': 'mosaik_components.mosaik_pypower.mosaik:PyPower'},
        'Optimizer': {'python': 'optimizer_simulator:OptimizerSim'},
        'Controller': {'python': 'power_controller_simulator:ControllerSim'},
        'PSS': {'python': 'pss_simulator:PSSSimulator'},
        'Collector': {'python': 'Collector:Collector'},
    }

    world = mosaik.World(sim_config)

    # Load asset description file
    with open(os.path.join(base_dir, 'asset_description.json'), 'r') as f:
        assets = json.load(f)

    # Start simulators
    csv_sim = world.start(
    'CSV',
    datafile=os.path.join(base_dir, 'data_power.csv'),
    sim_start='01.01.2016 00:00',         # Simulation start time (edit if needed)
    date_format='%d.%m.%Y %H:%M',         # Format of timestamps in CSV (edit if needed)
    delimiter=',',                        # Use ';' if your CSV uses semicolons
    type='time-based'                     # Tells the simulator to use timestamps
)

    pypower_sim = world.start('PyPower', step_size=60)
    optimizer_sim = world.start('Optimizer')
    controller_sim = world.start('Controller')
    pss_sim = world.start('PSS')
    collector_sim = world.start('Collector', data_out='output_data.json')
    monitor = collector_sim.Monitor.create(1)[0]



    #monitored_data = {'monitored data': {}}

    # Create and connect Load and Generator
    for idx, load in enumerate(assets['loads']):
        l = optimizer_sim.Load.create(1, bus=load['bus'])[0]
        g = optimizer_sim.Generator.create(1, bus=load['bus'])[0]
       # monitored_data['monitored data'][l.eid] = ['load_p']
        world.connect(l, monitor, 'load_p')
       # monitored_data['monitored data'][g.eid] = ['generator_p']
        world.connect(g, monitor, 'generator_p')

    # Create and connect PSS and Controller
    for idx, pss in enumerate(assets.get('pss', [])):
        p = optimizer_sim.PSS.create(1,
            bus=pss['bus'],
            E_PSS_max_wh=pss['E_PSS_max_wh'],
            E_PSS_init_wh=pss['E_PSS_init_wh'],
            P_PSS_max_w=pss['P_PSS_max_w'])[0]

        pc = controller_sim.PowerController.create(1,
            K_p=pss['K_p'],
            K_i=pss['K_i'],
            K_d=pss['K_d'])[0]

        turbine = pss_sim.PSS.create(1,
            nominal_power=pss['P_PSS_max_w'],
            pressure_wave_runtime=pss['pressure_wave_runtime'],
            initial_stored_energy_wh=pss['E_PSS_init_wh'])[0]

        world.connect(p, pc, ('p_total_w', 'process_value'))
        world.connect(pc, turbine, ('summed_output', 'valve_opening'))

       # monitored_data['monitored data'][p.eid] = ['p_ch_w', 'p_dis_w', 'p_total_w']
        world.connect(p, monitor, 'p_ch_w', 'p_dis_w', 'p_total_w')
       # monitored_data['monitored data'][pc.eid] = ['summed_output', 'current_value']
        world.connect(pc, monitor, 'summed_output', 'current_value')
       # monitored_data['monitored data'][turbine.eid] = ['turbine_generation', 'stored_energy_wh']
        world.connect(turbine, monitor, 'turbine_generation', 'stored_energy_wh')
    
    return world#, monitored_data
