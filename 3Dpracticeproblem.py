import gurobipy as gp
from gurobipy import GRB
from itertools import permutations

#Setup
model=gp.Model("3D_packing_optimization")
boxes={
    0:(40,40,40),
    1:(50,50,20),
    2:(30,30,30),
    3:(20,60,20),
    4:(70,30,40),
}
n=list(boxes.keys())
orientations=list(set(permutations([0,1,2])))
num_orient=6

#Size of the ULD
ULD_L,ULD_W,ULD_H=100,100,100

#Whether box is packed or not
b=model.addVars(n,vtype=GRB.BINARY,name="b")
weights=[10,1,1,1,10]

#Position of bottom left corner of each box
x=model.addVars(n,lb=0,ub=ULD_L,name="x")
y=model.addVars(n,lb=0,ub=ULD_W,name="y")
z=model.addVars(n,lb=0,ub=ULD_H,name="z")

#Orientation of each box
r=model.addVars(n,range(num_orient),vtype=GRB.BINARY,name="r")

#Constraints
for i in n:
    model.addConstr(gp.quicksum(r[i, o] for o in range(num_orient)) == b[i], name=f"orient_{i}")
lenx,leny,lenz={},{},{}
for i in n:
    for o, perm in enumerate(permutations(boxes[i])):
        lx, ly, lz = perm
        lenx[i, o] = lx
        leny[i, o] = ly
        lenz[i, o] = lz

for i in n:
    model.addConstr(
        gp.quicksum((x[i] + lenx[i, o] * r[i, o]) for o in range(num_orient)) <= ULD_L
    )
    model.addConstr(
        gp.quicksum((y[i] + leny[i, o] * r[i, o]) for o in range(num_orient)) <= ULD_W
    )
    model.addConstr(
        gp.quicksum((z[i] + lenz[i, o] * r[i, o]) for o in range(num_orient)) <= ULD_H
    )


M = 1000  # Big-M constant large enough to "disable" constraints when needed

for i in n:
    for j in n:
        if i >= j:
            continue  # Avoid duplicate pairs and self-pairing

        # Only apply non-overlap constraints if both boxes are packed
        for o1 in range(num_orient):
            for o2 in range(num_orient):
                # Only apply if this orientation pair is selected
                # Binary indicators
                delta_x = model.addVar(vtype=GRB.BINARY, name=f"delta_x_{i}_{j}_{o1}_{o2}")
                delta_y = model.addVar(vtype=GRB.BINARY, name=f"delta_y_{i}_{j}_{o1}_{o2}")
                delta_z = model.addVar(vtype=GRB.BINARY, name=f"delta_z_{i}_{j}_{o1}_{o2}")

                # One of the relative positions must be true if both orientations selected
                model.addConstr(delta_x + delta_y + delta_z >= r[i, o1] + r[j, o2] - 1)

                # Constraints for each spatial separation
                lx_i, ly_i, lz_i = lenx[i, o1], leny[i, o1], lenz[i, o1]
                lx_j, ly_j, lz_j = lenx[j, o2], leny[j, o2], lenz[j, o2]

                model.addConstr(x[i] + lx_i <= x[j] + M * (1 - delta_x))
                model.addConstr(x[j] + lx_j <= x[i] + M * (1 - delta_x))

                model.addConstr(y[i] + ly_i <= y[j] + M * (1 - delta_y))
                model.addConstr(y[j] + ly_j <= y[i] + M * (1 - delta_y))

                model.addConstr(z[i] + lz_i <= z[j] + M * (1 - delta_z))
                model.addConstr(z[j] + lz_j <= z[i] + M * (1 - delta_z))

    
# Objective: Maximize number of boxes packed
model.setObjective(gp.quicksum(b[i] for i in n), GRB.MAXIMIZE)

model.optimize()

# Output result
for i in n:
    if b[i].X > 0.5:
        chosen_rot = [o for o in range(num_orient) if r[i, o].X > 0.5][0]
        dims = (lenx[i, chosen_rot], leny[i, chosen_rot], lenz[i, chosen_rot])
        print(f"Box {i} packed at ({x[i].X:.1f}, {y[i].X:.1f}, {z[i].X:.1f}) with dims {dims}")
