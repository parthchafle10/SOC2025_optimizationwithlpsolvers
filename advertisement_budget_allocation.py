import gurobipy as gp
from gurobipy import GRB

# Setup
channels = ['social', 'tv', 'newspaper', 'banners']
n = len(channels)

min_spend = [10000, 30000, 5000, 5000]
max_spend = [40000, 60000, 20000, 30000]

# Piecewise utility breakpoints and values (example: convex, diminishing)
breakpoints = [
    [0, 10000, 20000, 40000],       # social
    [0, 30000, 45000, 60000],       # tv
    [0, 5000, 12000, 20000],        # newspaper
    [0, 5000, 15000, 30000]         # banners
]
reach = [
    [0, 1500, 2500, 3200],          # social
    [0, 2800, 3900, 4500],          # tv
    [0, 900, 1400, 1800],           # newspaper
    [0, 800, 1300, 1700]            # banners
]

model = gp.Model("ad_budget")

# Variables
x = model.addVars(n, name="x", lb=0)
y = model.addVars(n, vtype=GRB.BINARY, name="y")
u = model.addVars(n, name="u")

# Objective
model.setObjective(gp.quicksum(u[i] for i in range(n)), GRB.MAXIMIZE)

# Total budget constraint
model.addConstr(gp.quicksum(x[i] for i in range(n)) == 100000)

# Channel constraints
for i in range(n):
    model.addConstr(x[i] >= min_spend[i] * y[i])
    model.addConstr(x[i] <= max_spend[i] * y[i])
    # PWL function for reach
    model.addGenConstrPWL(x[i], u[i], breakpoints[i], reach[i])

# TV constraint: If used, at least ₹30,000
model.addConstr(x[1] >= 30000 * y[1])

# Max 3 channels constraint
model.addConstr(gp.quicksum(y[i] for i in range(n)) <= 3)

# Solve
model.optimize()

# Results
if model.status == GRB.OPTIMAL:
    print("Optimal Budget Allocation:")
    for i in range(n):
        if x[i].X > 0:
            print(f"  {channels[i]}: ₹{x[i].X:.2f}, Reach: {u[i].X:.1f}")
    print(f"Total Reach: {sum(u[i].X for i in range(n)):.1f}")
