import numpy as np


def build_ptdf_matrix(buses, lines, slack_bus):
    n = len(buses)
    B = np.zeros((n, n))
    id_map = {bus: idx for idx, bus in enumerate(buses)}
    line_map = {}

    for idx, line in enumerate(lines):
        i = id_map[line["from_bus_id"]]
        j = id_map[line["to_bus_id"]]
        b = line["b_siemens"]

        B[i, i] += b
        B[j, j] += b
        B[i, j] -= b
        B[j, i] -= b

        line_map[idx] = (line["from_bus_id"], line["to_bus_id"])

    # remove slack row and column
    slack_idx = id_map[slack_bus]
    B_reduced = np.delete(np.delete(B, slack_idx, axis=0), slack_idx, axis=1)

    # pseudo-inverse
    B_inv = np.linalg.pinv(B_reduced)

    return B_inv, line_map
