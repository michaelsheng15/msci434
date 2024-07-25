import gurobipy as gp
from gurobipy import GRB

# Sets
Retailers = ['R1', 'R2', 'R3']
Suppliers = ['S1', 'S2']
Warehouses = ['W1']

# Parameters
p = 25  # Unit product price
c = 10  # Unit production cost
c_st = {('S1', 'W1'): 5, ('S2', 'W1'): 8, ('W1', 'R1'): 6, ('W1', 'R2'): 7, ('W1', 'R3'): 9}  # Transportation costs
b_r = {'R1': 100, 'R2': 150, 'R3': 200}  # Demand for each retailer
m_s = {'S1': 250, 'S2': 300}  # Maximum supply capacity of each supplier
m_td = {'W1': 450}  # Maximum transshipment quantity through the warehouse

# Create the model
model = gp.Model("SupplyChainWithWarehouseOptimization")

# Decision variables
x_sw = model.addVars(Suppliers, Warehouses, name="x_sw", vtype=GRB.CONTINUOUS, lb=0)  # Quantity shipped to warehouse
x_wr = model.addVars(Warehouses, Retailers, name="x_wr", vtype=GRB.CONTINUOUS, lb=0)  # Quantity shipped from warehouse
s_f = model.addVars(Suppliers, name="s_f", vtype=GRB.CONTINUOUS, lb=0)  # Production quantity of suppliers

# Objective: Maximize profit
model.setObjective(
    gp.quicksum(p * b_r[r] for r in Retailers) -
    gp.quicksum(c_st[s, w] * x_sw[s, w] for s in Suppliers for w in Warehouses) -  # Costs from suppliers to warehouse
    gp.quicksum(c_st[w, r] * x_wr[w, r] for w in Warehouses for r in Retailers) -  # Costs from warehouse to retailers
    gp.quicksum(c * s_f[f] for f in Suppliers),  # Production costs
    GRB.MAXIMIZE
)

# Constraints
# Supply must meet or exceed demand
model.addConstr(
    gp.quicksum(s_f[f] for f in Suppliers) >= gp.quicksum(b_r[r] for r in Retailers), "SupplyDemandBalance"
)

# Flow conservation for suppliers (Supply to Warehouse)
for f in Suppliers:
    model.addConstr(
        gp.quicksum(x_sw[f, w] for w in Warehouses) == s_f[f], f"FlowConservation_{f}"
    )

# Supply capacity constraints
for f in Suppliers:
    model.addConstr(
        s_f[f] <= m_s[f], f"SupplyCapacity_{f}"
    )

# Demand fulfillment at the retailer level
for r in Retailers:
    model.addConstr(
        gp.quicksum(x_wr[w, r] for w in Warehouses) == b_r[r], f"DemandFulfillment_{r}"
    )

# Transshipment conservation at the warehouse level
for w in Warehouses:
    model.addConstr(
        gp.quicksum(x_sw[s, w] for s in Suppliers) == gp.quicksum(x_wr[w, r] for r in Retailers), f"WarehouseBalance_{w}"
    )

# Transshipment capacity at the warehouse
for w in Warehouses:
    model.addConstr(
        gp.quicksum(x_wr[w, r] for r in Retailers) <= m_td[w], f"TransshipmentCapacity_{w}"
    )

# Optimize the model
model.optimize()

# Check if the model found an optimal solution
if model.status == GRB.OPTIMAL:
    print(f"Optimal Total Profit: {model.objVal}")

    # Print the optimal shipment quantities
    print("\nOptimal shipment quantities:")
    for f in Suppliers:
        for w in Warehouses:
            print(f"  From {f} to {w}: {x_sw[f, w].x} units")
    for w in Warehouses:
        for r in Retailers:
            print(f"  From {w} to {r}: {x_wr[w, r].x} units")
else:
    print("No optimal solution found.")