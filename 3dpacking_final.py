import gurobipy as gp
from gurobipy import GRB

def run_3d_packing(ULD_L, ULD_W, ULD_H, boxes, objective_type=1):
    n = len(boxes)
    
    model = gp.Model("3D_Box_Packing")
    model.setParam('OutputFlag', 1)

    # Variables
    b = [model.addVar(vtype=GRB.BINARY, name=f"b_{i}") for i in range(n)]  # whether box i is packed
    x = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"x_{i}") for i in range(n)]
    y = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"y_{i}") for i in range(n)]
    z = [model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f"z_{i}") for i in range(n)]

    L = [box['length'] for box in boxes]
    W = [box['width'] for box in boxes]
    H = [box['height'] for box in boxes]
    P = [box['priority'] for box in boxes]
    weight = [box['weight'] for box in boxes]

    # Fit within ULD dimensions
    for i in range(n):
        model.addConstr(x[i] + L[i] * b[i] <= ULD_L)
        model.addConstr(y[i] + W[i] * b[i] <= ULD_W)
        model.addConstr(z[i] + H[i] * b[i] <= ULD_H)

    # No overlap constraint
    M = max(ULD_L, ULD_W, ULD_H)
    for i in range(n):
        for j in range(i + 1, n):
            delta = [model.addVar(vtype=GRB.BINARY, name=f"delta_{i}_{j}_{d}") for d in range(3)]
            model.addConstr(x[i] + L[i] <= x[j] + M * (1 - delta[0]) + M * (2 - b[i] - b[j]))
            model.addConstr(x[j] + L[j] <= x[i] + M * delta[0] + M * (2 - b[i] - b[j]))

            model.addConstr(y[i] + W[i] <= y[j] + M * (1 - delta[1]) + M * (2 - b[i] - b[j]))
            model.addConstr(y[j] + W[j] <= y[i] + M * delta[1] + M * (2 - b[i] - b[j]))

            model.addConstr(z[i] + H[i] <= z[j] + M * (1 - delta[2]) + M * (2 - b[i] - b[j]))
            model.addConstr(z[j] + H[j] <= z[i] + M * delta[2] + M * (2 - b[i] - b[j]))

            model.addConstr(gp.quicksum(delta[d] for d in range(3)) >= b[i] + b[j] - 1)

    # Objective
    if objective_type == 1:
        model.setObjective(gp.quicksum((P[i] * 1000 + (1 - P[i])) * b[i] for i in range(n)), GRB.MAXIMIZE)
    elif objective_type == 2:
        model.setObjective(gp.quicksum(L[i] * W[i] * H[i] * b[i] for i in range(n)), GRB.MAXIMIZE)
    elif objective_type == 3:
        model.setObjective(gp.quicksum(weight[i] * b[i] for i in range(n)), GRB.MAXIMIZE)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        print("\nOptimal Packing Found:")
        for i in range(n):
            if b[i].X > 0.5:
                print(f"Box {i} packed at (x={x[i].X}, y={y[i].X}, z={z[i].X})")
    else:
        print("\nModel is infeasible or no optimal solution found.")

# Example usage:
if __name__ == '__main__':
    '''ULD_L = 10
    ULD_W = 10
    ULD_H = 10

    boxes = [
        {'length': 4, 'width': 4, 'height': 4, 'weight': 4, 'priority': 1},
        {'length': 8, 'width': 8, 'height': 8, 'weight': 8, 'priority': 1},
        {'length': 2, 'width': 2, 'height': 2, 'weight': 2, 'priority': 0},
    ]'''
    print("Enter ULD dimensions (in cm):")
    ULD_L = int(input("Length: "))
    ULD_W = int(input("Width: "))
    ULD_H = int(input("Height: "))

    num_boxes = int(input("\nEnter number of boxes: "))
    boxes = []
    print("\nEnter box details:")
    for i in range(num_boxes):
        print(f"Box {i}:")
        l = int(input("  Length: "))
        w = int(input("  Width : "))
        h = int(input("  Height: "))
        wt = int(input("  Weight: "))
        prio = int(input("  Priority (1 = must pack, 0 = optional): "))
        boxes.append({"length": l, "width": w, "height": h, "weight": wt, "priority": prio})

    print("\nChoose objective:")
    print("1 = Maximize number of boxes")
    print("2 = Maximize total volume")
    print("3 = Maximize total weight")
    objective = int(input("Choice (1/2/3): "))

    run_3d_packing(ULD_L, ULD_W, ULD_H, boxes, objective_type=1)
