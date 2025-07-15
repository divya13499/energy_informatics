from pyomo.environ import *
from .utils import build_ptdf_matrix


def solve_dc_opf(adn_config):
    model = ConcreteModel()

    # ==== Sets ====
    buses = [bus["id"] for bus in adn_config["bus"]]
    model.B = Set(initialize=buses)

    slack_bus = next(bus["id"] for bus in adn_config["bus"] if bus["slack"])
    gen = {bus["id"]: bus["P_G_w"] or 0 for bus in adn_config["bus"]}
    load = {bus["id"]: bus["P_D_w"] or 0 for bus in adn_config["bus"]}

    bss_list = adn_config.get("bss", [])
    bss_buses = [bss["bus_id"] for bss in bss_list]
    model.BSS = Set(initialize=bss_buses)

    bss_params = {bss["bus_id"]: bss for bss in bss_list}
    lines = adn_config["line"]
    costs = adn_config["costs"]
    delta_ps = adn_config["energy_imbalance_next_W"]

    # === Parameters ===
    model.P_G = Param(model.B, initialize=gen)
    model.P_D = Param(model.B, initialize=load)

    # ==== Decision Variables ====
    model.P_Im = Var(within=NonNegativeReals)
    model.P_Ex = Var(within=NonNegativeReals)

    model.PCh = Var(model.BSS, within=NonNegativeReals)
    model.PDis = Var(model.BSS, within=NonNegativeReals)
    model.M = Var(model.BSS, within=Binary)

    model.theta = Var(model.B, initialize=0)
    model.P_line = Var(range(len(lines)), within=Reals)

    # ==== Battery constraints ====
    def battery_constraints(m, i):
        bss = bss_params[i]
        Pmax = bss["P_BSS_max_w"]
        Emax = bss["E_BSS_max_wh"]
        Einit = bss["E_BSS_init_wh"]

        return [
            m.PCh[i] <= Pmax * m.M[i],
            m.PDis[i] <= Pmax * (1 - m.M[i]),
            Einit + 0.25 * m.PCh[i] - 0.25 * m.PDis[i] <= Emax,
            Einit + 0.25 * m.PCh[i] - 0.25 * m.PDis[i] >= 0
        ]

    model.battery_cons = ConstraintList()
    for i in model.BSS:
        for con in battery_constraints(model, i):
            model.battery_cons.add(con)

    # ==== Power flow constraints (DC + PTDF) ====
    PTDF, line_map = build_ptdf_matrix(buses, lines, slack_bus)

    for idx, (from_bus, to_bus) in line_map.items():
        susceptance = next(l["b_siemens"] for l in lines if l["from_bus_id"] == from_bus and l["to_bus_id"] == to_bus)
        model.P_line[idx] = susceptance * (model.theta[from_bus] - model.theta[to_bus])

    for i, line in enumerate(lines):
        Pmax = line["P_line_max_w"]
        model.add_component(f"line_flow_limit_{i}", Constraint(expr=abs(model.P_line[i]) <= Pmax))

    # ==== Nodal power balance ====
    def node_balance(m, i):
        gen_i = m.P_G[i]
        load_i = m.P_D[i]
        ch = m.PCh[i] if i in model.BSS else 0
        dis = m.PDis[i] if i in model.BSS else 0

        if i == slack_bus:
            return (
                m.P_Im - m.P_Ex + sum(model.P_line[j] for j, (f, t) in line_map.items() if t == i)
                - sum(model.P_line[j] for j, (f, t) in line_map.items() if f == i)
                == gen_i - load_i + dis - ch
            )
        else:
            return (
                sum(model.P_line[j] for j, (f, t) in line_map.items() if t == i)
                - sum(model.P_line[j] for j, (f, t) in line_map.items() if f == i)
                == gen_i - load_i + dis - ch
            )

    model.node_bal = Constraint(model.B, rule=node_balance)

    # ==== Future power imbalance ====
    model.future_balance = Constraint(
        expr=delta_ps == model.P_Im - model.P_Ex - sum(model.PCh[i] - model.PDis[i] for i in model.BSS)
    )

    # ==== Objective ====
    cost_now = costs["import_now"] * model.P_Im - costs["export_now"] * model.P_Ex
    cost_next = costs["import_next"] * delta_ps if delta_ps >= 0 else -costs["export_next"] * (-delta_ps)
    model.obj = Objective(expr=cost_now + cost_next, sense=minimize)

    # ==== Solve ====
    solver = SolverFactory("glpk")
    results = solver.solve(model, tee=False)

    if (results.solver.status != SolverStatus.ok) or (results.solver.termination_condition != TerminationCondition.optimal):
        raise RuntimeError("Solver did not converge")

    return {
        "objective_value_w": value(model.obj),
        "bss": [
            {
                "bus_id": i,
                "P_BSS_ch_w": value(model.PCh[i]),
                "P_BSS_dis_w": value(model.PDis[i]),
            } for i in model.BSS
        ]
    }
