import gurobipy as gp
from gurobipy import GRB

# Sets
products = range(4)
periods = range(5)

# Sample data (replace with real values)
m_time = [3, 4, 2, 5]
m_mat = [5, 3, 4, 6]
setup_cost = [100, 120, 90, 150]
prod_cost = [20, 22, 18, 25]
storage_cost = [2, 2, 1, 3]
capacity_time = [100, 90, 110, 95, 105]
capacity_mat = [200, 180, 190, 170, 210]
demand = [
    [10, 15, 12, 14, 13],  # product 0
    [8, 12, 10, 9, 11],    # product 1
    [14, 13, 15, 12, 10],  # product 2
    [7, 9, 8, 10, 6]       # product 3
]

BigM = max(max(row) for row in demand) * 2

model = gp.Model("ProductionPlanning")

# Decision variables
x = model.addVars(products, periods, vtype=GRB.CONTINUOUS, name="Produce")
y = model.addVars(products, periods, vtype=GRB.BINARY, name="Setup")
inv = model.addVars(products, range(len(periods) + 1), vtype=GRB.CONTINUOUS, name="Inventory")

# Initial inventory = 0
for i in products:
    model.addConstr(inv[i, 0] == 0)

# Inventory and demand constraints
for i in products:
    for t in periods:
        model.addConstr(inv[i, t] + x[i, t] == demand[i][t] + inv[i, t + 1])

# Capacity constraints
for t in periods:
    model.addConstr(gp.quicksum(m_time[i] * x[i, t] for i in products) <= capacity_time[t])
    model.addConstr(gp.quicksum(m_mat[i] * x[i, t] for i in products) <= capacity_mat[t])

# Setup constraints
for i in products:
    for t in periods:
        model.addConstr(x[i, t] <= BigM * y[i, t])

# Objective
model.setObjective(
    gp.quicksum(prod_cost[i] * x[i, t] + setup_cost[i] * y[i, t] + storage_cost[i] * inv[i, t + 1]
                for i in products for t in periods),
    GRB.MINIMIZE
)

model.optimize()

# Results
if model.status == GRB.OPTIMAL:
    print("\nOptimal Production Plan:\n")
    for t in periods:
        print(f"Period {t+1}:")
        for i in products:
            if x[i, t].X > 0.01:
                print(f"  Produce {x[i, t].X:.1f} units of Product {i+1}, Setup: {int(y[i, t].X)}")
        print()
