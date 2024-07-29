import gurobipy as gp
from gurobipy import GRB

suppliers = ['S1', 'S2']
warehouses = ['W1', 'W2']
retailers = ['R1', 'R2', 'R3', 'R4']

# PARAMETERS
p = 25  
c = 10  
h = 0.5

transport_cost_matrix = {
    ('S1', 'W1'): 5, 
    ('S2', 'W1'): 8, 
    ('S1', 'W2'): 7, 
    ('S2', 'W2'): 9,
    ('W1', 'R1'): 6, 
    ('W1', 'R2'): 7, 
    ('W1', 'R3'): 9, 
    ('W1', 'R4'): 10,
    ('W2', 'R1'): 6, 
    ('W2', 'R2'): 5, 
    ('W2', 'R3'): 8, 
    ('W2', 'R4'): 7
}  # transport cost matrix
b_r = {'R1': 100, 'R2': 150, 'R3': 200, 'R4': 180}  # random retailer demand
m_s = {'S1': 350, 'S2': 400}  # max production capacity
m_td = {'W1': 500, 'W2': 350}  # max warehouse capacity

# BUILDING THE MODEL
model = gp.Model("Production & Transportation Optimization Model")

# decision vars
x_sw = model.addVars(suppliers, warehouses, name="x_sw", vtype=GRB.CONTINUOUS, lb=0)  # Q shipped from suppliers to warehouses
x_wr = model.addVars(warehouses, retailers, name="x_wr", vtype=GRB.CONTINUOUS, lb=0)  # Q shipped from warehouses to retailers
s_f = model.addVars(suppliers, name="s_f", vtype=GRB.CONTINUOUS, lb=0)  # amount produced by suppliers

# objective is to maximize profit
model.setObjective(
    gp.quicksum(p * b_r[r] for r in retailers) - # profit
    gp.quicksum(transport_cost_matrix[s, w] * x_sw[s, w] for s in suppliers for w in warehouses) -  # supplier to warehouse transport costs
    gp.quicksum(transport_cost_matrix[w, r] * x_wr[w, r] for w in warehouses for r in retailers) -  # warehouse to retailer transport costs
    gp.quicksum(h * x_sw[s, w] for s in suppliers for w in warehouses) - #warehouse holding cost
    gp.quicksum(c * s_f[f] for f in suppliers),  # cost of production
    GRB.MAXIMIZE
)

# CONSTRAINTS
# Total amount produced must be greater than or equal to total retail demand
model.addConstr(
    gp.quicksum(s_f[f] for f in suppliers) >= gp.quicksum(b_r[r] for r in retailers), "SupplyDemandBalance"
)

# Amount shipped from supplier to warehouse is the total amount produced
for f in suppliers:
    model.addConstr(
        gp.quicksum(x_sw[f, w] for w in warehouses) == s_f[f], f"FlowConservation_{f}"
    )

# Amount produced of each supplier cannot exceed maximum capacity of supplier
for f in suppliers:
    model.addConstr(
        s_f[f] <= m_s[f], f"SupplyCapacity_{f}"
    )

# Amount shipped is equal to the demand of each retailer
for r in retailers:
    model.addConstr(
        gp.quicksum(x_wr[w, r] for w in warehouses) == b_r[r], f"DemandFulfillment_{r}"
    )

# Amount shipped into each warehouse is equal to the amount shipped out of each node
for w in warehouses:
    model.addConstr(
        gp.quicksum(x_sw[s, w] for s in suppliers) == gp.quicksum(x_wr[w, r] for r in retailers), f"WarehouseBalance_{w}"
    )

# Amount shipped into each warehouse is less than or equal to maximum capacity of the warehouse
for w in warehouses:
    model.addConstr(
        gp.quicksum(x_wr[w, r] for r in retailers) <= m_td[w], f"TransshipmentCapacity_{w}"
    )

model.optimize()

if model.status == GRB.OPTIMAL:
    print("\n\nRESULTS:")
    print(f"\nOptimal Total Profit: {model.objVal}")

    print("\nOptimal shipment quantities:")
    for f in suppliers:
        for w in warehouses:
            print(f"  From {f} to {w}: {x_sw[f, w].x} units")
    for w in warehouses:
        for r in retailers:
            print(f"  From {w} to {r}: {x_wr[w, r].x} units")
            
    print("\nOptimal production quantities:")
    for s in suppliers:
        print(f"  Suppliers {s} should produce: {s_f[s].x} units")


else:
    print("No optimal solution found.")