import gurobipy as gp
from gurobipy import GRB
import random

# Problem data
num_nurses = 6
num_days = 7
num_shifts = 3

nurses = range(num_nurses)
days = range(num_days)
shifts = range(num_shifts)

# Random preference scores: P[i][j][k] represents nurse i's preference for day j, shift k
P = [[[random.randint(0, 10) for k in shifts] for j in days] for i in nurses]

# Create the model
model = gp.Model("Nurse_Scheduling")

# Decision variables: n[i,j,k] = 1 if nurse i works shift k on day j
n = model.addVars(nurses, days, shifts, vtype=GRB.BINARY, name="n")

# Constraint 1: Each shift must be covered by exactly one nurse
for j in days:
    for k in shifts:
        model.addConstr(gp.quicksum(n[i, j, k] for i in nurses) == 1)

# Constraint 2: Each nurse works at most 5 shifts in the week
for i in nurses:
    model.addConstr(gp.quicksum(n[i, j, k] for j in days for k in shifts) <= 5)

# Constraint 3: Each nurse works at most one shift per day
for i in nurses:
    for j in days:
        model.addConstr(gp.quicksum(n[i, j, k] for k in shifts) <= 1)

# Constraint 4: No night shift (k=2) followed by morning shift (k=0) the next day
for i in nurses:
    for j in range(num_days - 1):
        model.addConstr(n[i, j, 2] + n[i, j + 1, 0] <= 1)

# Objective: Maximize total preference score
model.setObjective(
    gp.quicksum(n[i, j, k] * P[i][j][k] for i in nurses for j in days for k in shifts),
    GRB.MAXIMIZE
)

# Solve the model
model.optimize()

# Display schedule
if model.status == GRB.OPTIMAL:
    print("\nOptimal Nurse Schedule:\n")
    for i in nurses:
        for j in days:
            for k in shifts:
                if n[i, j, k].X > 0.5:
                    shift_name = ["Morning", "Evening", "Night"][k]
                    print(f"Nurse {i + 1} works on Day {j + 1} ({shift_name} shift)")
