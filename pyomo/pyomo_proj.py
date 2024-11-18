import pyomo.environ as pyo

model = pyo.AbstractModel(name='HW4_ΣΑΜΑΡΑΣ') # Δημιουργία Μοντέλου

model.p = pyo.Param(within=pyo.NonNegativeIntegers) # Αριθμός περιόδων
model.P = pyo.RangeSet(1, model.p) # Σύνολο χρονικών περιόδων από 1 ως p
model.T = pyo.Set() # Σύνολο που περιέχει τα προϊόντα (ποδήλατα)
model.C = pyo.Param(model.T, within=pyo.NonNegativeReals) # Μοναδιαίο κόστος κάθε ποδηλάτου
model.MH = pyo.Param(model.T, within=pyo.NonNegativeReals) # Ώρες για την κατασκευή κάθε ποδηλάτου
model.AH = pyo.Param(model.T, within=pyo.NonNegativeReals) # Ώρες για την συναρμολόγηση κάθε ποδηλάτου
model.SI = pyo.Param(model.T, within=pyo.NonNegativeIntegers) # Αρχικό απόθεμα προϊόντος
model.FI = pyo.Param(model.T, within=pyo.NonNegativeIntegers) # Τελικό απόθεμα προϊόντος
model.LU = pyo.Param(within=pyo.NonNegativeIntegers) # Αριθμός εργατοωρών που χρησιμοποιούνται
model.LV = pyo.Param(within=pyo.NonNegativeIntegers) # Επιτρεπόμενη διακύμανση εργατοωρών μεταξύ περιόδων
model.HC = pyo.Param(within=pyo.NonNegativeReals) # Ποσοστιαίο κόστος διατήρησης αποθέματος
model.D = pyo.Param(model.P, model.T, within=pyo.NonNegativeReals) # Μηνιαία ζήτηση κάθε τύπου ποδηλάτου

# Μεταβλητές
model.X = pyo.Var(model.T, model.P, within=pyo.NonNegativeIntegers)
model.I = pyo.Var(model.T, model.P, within=pyo.NonNegativeIntegers)

# Αντικειμενική συνάρτηση: Ελαχιστοποίηση του συνολικού κόστους
def total_cost_rule(model):
    production_cost = sum(model.C[t] * model.X[t, p] for p in model.P for t in model.T)
    holding_cost = sum(model.HC * model.C[t] * model.I[t, p] for p in model.P for t in model.T)
    return production_cost + holding_cost

model.TotalCost = pyo.Objective(rule=total_cost_rule)


# Περιορισμός ζήτησης
def demand_constraint_rule(model, j, t):
    if j == 1:
        return model.X[t, 1] - model.I[t, 1] == model.D[1, t] - model.SI[t]
    else:
        return model.X[t, j] + model.I[t, j - 1] - model.I[t, j] == model.D[j, t]

model.DemandsConstraint = pyo.Constraint(model.P, model.T, rule=demand_constraint_rule)


# Μέγιστες επιτρεπτές εργατοώρες
def max_labour_hours_rule(model):
    return sum((model.MH[t] + model.AH[t]) * model.X[t, 1] for t in model.T) <= model.LU + model.LV

model.MaxLabourHours = pyo.Constraint(rule=max_labour_hours_rule)



# Ελάχιστες απαιτούμενες εργατοώρες
def min_labour_hours_rule(model):
    return sum((model.MH[t] + model.AH[t]) * model.X[t, 1] for t in model.T) >= model.LU - model.LV

model.MinLabourHours = pyo.Constraint(rule=min_labour_hours_rule)


# Διακύμανση εργατοωρών μεταξύ περιόδων (θετική διαφορά)
def labour_variation_rule_positive(model, j):
    if j == 1:
        return pyo.Constraint.Skip
    else:
        return sum((model.MH[t] + model.AH[t]) * (model.X[t, j] - model.X[t, j - 1]) for t in model.T) <= model.LV


# Διακύμανση εργατοωρών μεταξύ περιόδων (αρνητική διαφορά)
def labour_variation_rule_negative(model, j):
    if j == 1:
        return pyo.Constraint.Skip
    else:
        return sum((model.MH[t] + model.AH[t]) * (model.X[t, j] - model.X[t, j - 1]) for t in model.T) >= -model.LV

model.LabourVariationPositive = pyo.Constraint(model.P, rule=labour_variation_rule_positive)
model.LabourVariationNegative = pyo.Constraint(model.P, rule=labour_variation_rule_negative)


# Τελικό απόθεμα να είναι μεγαλύτερο ή ίσο από τον στόχο
def final_inventory_rule(model, t):
    return model.I[t, model.p] >= model.FI[t]

model.FinalInventory = pyo.Constraint(model.T, rule=final_inventory_rule)
