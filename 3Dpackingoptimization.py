import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

def get_input_data():
    # Prompt ULD dimensions
    print("Enter ULD dimensions (in cm):")
    ULD_L = float(input("Length: "))
    ULD_W = float(input("Width: "))
    ULD_H = float(input("Height: "))

    # Prompt number of boxes
    n_boxes = int(input("\nEnter number of boxes: "))
    boxes = {}

    print("\nEnter box details:")
    for i in range(n_boxes):
        print(f"Box {i}:")
        l = float(input("  Length: "))
        w = float(input("  Width : "))
        h = float(input("  Height: "))
        weight = float(input("  Weight: "))
        priority = int(input("  Priority (1 = must pack, 0 = optional): "))
        boxes[i] = (l, w, h, weight, priority)

    return ULD_L, ULD_W, ULD_H, boxes

def run_3d_packing(ULD_L, ULD_W, ULD_H, boxes, objective_type="volume"):
    n = list(boxes.keys())
    orientations = list(set(permutations([0, 1, 2])))
    num_orient = len(orientations)

    model = gp.Model("ULD_3D_Packing")

    b = model.addVars(n, vtype=GRB.BINARY, name="is_packed")
    r = model.addVars(n, range(num_orient), vtype=GRB.BINARY, name="rotation")
    x = model.addVars(n, lb=0, ub=ULD_L, name="x")
    y = model.addVars(n, lb=0, ub=ULD_W, name="y")
    z = model.addVars(n, lb=0, ub=ULD_H, name="z")

    # Rotation handling
    lenx, leny, lenz = {}, {}, {}
    for i in n:
        l, w, h = boxes[i][:3]
        perms = list(permutations((l, w, h)))
        for o, (lx, ly, lz) in enumerate(perms):
            lenx[i, o] = lx
            leny[i, o] = ly
            lenz[i, o] = lz

    # Rotation selection
    for i in n:
        model.addConstr(gp.quicksum(r[i, o] for o in range(num_orient)) == b[i])

    # ULD boundary constraints
    for i in n:
        model.addConstr(
            gp.quicksum(x[i] + lenx[i, o] * r[i, o] for o in range(num_orient)) <= ULD_L)
        model.addConstr(
            gp.quicksum(y[i] + leny[i, o] * r[i, o] for o in range(num_orient)) <= ULD_W)
        model.addConstr(
            gp.quicksum(z[i] + lenz[i, o] * r[i, o] for o in range(num_orient)) <= ULD_H)

    # Non-overlap constraints
    M = 1e5
    for i in n:
        for j in n:
            if i >= j:
                continue
            for o1 in range(num_orient):
                for o2 in range(num_orient):
                    delta_x = model.addVar(vtype=GRB.BINARY)
                    delta_y = model.addVar(vtype=GRB.BINARY)
                    delta_z = model.addVar(vtype=GRB.BINARY)
                    model.addConstr(delta_x + delta_y + delta_z >= r[i, o1] + r[j, o2] - 1)

                    lx_i, ly_i, lz_i = lenx[i, o1], leny[i, o1], lenz[i, o1]
                    lx_j, ly_j, lz_j = lenx[j, o2], leny[j, o2], lenz[j, o2]

                    model.addConstr(x[i] + lx_i <= x[j] + M * (1 - delta_x))
                    model.addConstr(x[j] + lx_j <= x[i] + M * (1 - delta_x))
                    model.addConstr(y[i] + ly_i <= y[j] + M * (1 - delta_y))
                    model.addConstr(y[j] + ly_j <= y[i] + M * (1 - delta_y))
                    model.addConstr(z[i] + lz_i <= z[j] + M * (1 - delta_z))
                    model.addConstr(z[j] + lz_j <= z[i] + M * (1 - delta_z))

    # Priority constraints
    for i in n:
        if boxes[i][4] == 1:
            model.addConstr(b[i] == 1)

    # Objective
    if objective_type == "count":
        model.setObjective(gp.quicksum(b[i] for i in n), GRB.MAXIMIZE)
    elif objective_type == "volume":
        model.setObjective(
            gp.quicksum(boxes[i][0] * boxes[i][1] * boxes[i][2] * b[i] for i in n),
            GRB.MAXIMIZE)
    elif objective_type == "weight":
        model.setObjective(
            gp.quicksum(boxes[i][3] * b[i] for i in n), GRB.MAXIMIZE)

    model.Params.OutputFlag = 1
    model.optimize()

    # Output results
    if model.status == GRB.OPTIMAL:
    print("\n Packing result:")
    for i in n:
        if b[i].X > 0.5:
            chosen_rot = [o for o in range(num_orient) if r[i, o].X > 0.5][0]
            dims = (lenx[i, chosen_rot], leny[i, chosen_rot], lenz[i, chosen_rot])
            print(f"Box {i}: at ({x[i].X:.1f}, {y[i].X:.1f}, {z[i].X:.1f}) with dims {dims}")
else:
    print(" Model was infeasible or no optimal solution found.")

if __name__ == "__main__":
    # Choose either manual input or hardcoded test
    use_manual_input = True  # Set to False to use default example

    if use_manual_input:
        ULD_L, ULD_W, ULD_H, boxes = get_input_data()
    else:
        # Sample ULD and boxes
        ULD_L, ULD_W, ULD_H = 317.5, 223.5, 162.5
        boxes = {
            0: (40, 40, 40, 10, 1),
            1: (50, 50, 20, 8, 0),
            2: (30, 30, 30, 5, 0),
            3: (20, 60, 20, 6, 1),
            4: (70, 30, 40, 12, 0),
        }

    print("\nChoose objective:")
    print("1 = Maximize number of boxes")
    print("2 = Maximize total volume")
    print("3 = Maximize total weight")
    obj_choice = input("Choice (1/2/3): ")
    objective_map = {"1": "count", "2": "volume", "3": "weight"}
    obj_type = objective_map.get(obj_choice, "volume")

    run_3d_packing(ULD_L, ULD_W, ULD_H, boxes, objective_type=obj_type)

