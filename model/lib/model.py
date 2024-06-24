import pyomo.environ as pyo
from . import results_summary

_model = None
_global_data = None
_teachers_data = None
_students_data = None

#region Indexation
def format_psi_index(i, j, xi, k):
    return f'{i}_{j}_{xi}_{k}'

def format_omega_index(i, j, xi, k):
    return f'{i}_{j}_{xi}_{k}'

def format_sigma_index(i, j):
    return f'{i}_{j}'

def psi(i, j, xi, k):
    return _model.psi[format_psi_index(i, j, xi, k)]

def omega(i, j, xi, k):
    return _model.omega[format_omega_index(i, j, xi, k)]

def sigma(i, j):
    return _model.sigma[format_sigma_index(i, j)]
#endregion Indexation

#region Constants
def Phi(t):
    if t == 'min':
        return _global_data.min_periods_per_teacher
    elif t == 'max':
        return _global_data.max_periods_per_teacher

def L_max():
    return _global_data.max_students_per_class
#endregion Constants

#region Sets
def Xi(j):
    return _global_data.courses_sections[j]

def cart(sets, ravel=False):
    res = sets[0]
    for i in range(1, len(sets)):
        new = []
        for a in res:
            for b in sets[i]:
                if ravel:
                    new_a = [a]
                    if isinstance(a, (set, tuple)):
                        new_a = list(a)
                    new_b = [b]
                    if isinstance(b, (set, tuple)):
                        new_b = list(b)
                    new.append(tuple(new_a + new_b))
                else:
                    new.append((a, b))
        res = new
    return res

def T():
    return list(_teachers_data.teachers.items())

def S():
    return list(_students_data.students.items())

def P():
    return _global_data.periods

def C():
    return _global_data.all_courses

def V(j):
    res = []
    for i, CT_i in T():
        if j in CT_i:
            res.append(i)
    return res

def K():
    res = []
    for i, CS_i in S():
        res.extend(cart([[i], CS_i]))
    return res

def W(j):
    res = []
    for i, CS_i in S():
        if j in CS_i:
            res.append(i)
    return res

def Y():
    res = []
    for i in _global_data.all_courses:
        res.extend(cart([[i], Xi(i), P()]))
    return res

def D():
    res = []
    for i in _global_data.all_courses:
        res.extend(cart([[i], Xi(i)]))
    return res
#endregion Sets

#region Model creation
def _set_psi_variables():
    indices = []
    for i, CT_i in T():
        for j in CT_i:
            indices.extend(cart([[i], [j], Xi(j), P()], ravel=True))
    indices = list(map(lambda t: format_psi_index(*t), indices))
    _model.psi = pyo.Var(indices, within=pyo.Binary)

def _set_omega_variables():
    indices = []
    for i, CS_i in S():
        for j in CS_i:
            indices.extend(cart([[i], [j], Xi(j), P()], ravel=True))
    indices = list(map(lambda t: format_omega_index(*t), indices))
    _model.omega = pyo.Var(indices, within=pyo.Binary)

def _set_sigma_variables():
    indices = []
    for i, j in K():
        indices.append((i, j))
    indices = list(map(lambda t: format_sigma_index(*t), indices))
    _model.sigma = pyo.Var(indices, within=pyo.Binary)

def _set_objective():
    z = 0
    for i, j in K():
        z += sigma(i, j)
    _model.z = pyo.Objective(expr=z, sense=pyo.minimize)

def _set_constraint_1():
    T_dict = {i: CT_i for i, CT_i in T()}

    def lhs(i):
        variables = []
        CT_i = T_dict[i]
        for j in CT_i:
            for t in cart([[i], [j], Xi(j), P()], ravel=True):
                variables.append(_model.psi[format_psi_index(*t)])
        return sum(variables)
    
    const_indices = list(T_dict.keys())
    _model.teacher_periods_lb = pyo.Constraint(const_indices, rule=lambda _, i: lhs(i) >= Phi('min'))
    _model.teacher_periods_ub = pyo.Constraint(const_indices, rule=lambda _, i: lhs(i) <= Phi('max'))

def _set_constraint_2():
    TxP_dict = {f'{i}_{k}': (i, CT_i, k) for ((i, CT_i), k) in cart([T(), P()])}

    def lhs(idx):
        variables = []
        i, CT_i, k = TxP_dict[idx]
        for j in CT_i:
            for t in cart([[i], [j], Xi(j), [k]], ravel=True):
                variables.append(_model.psi[format_psi_index(*t)])
        return sum(variables)

    const_indices = list(TxP_dict.keys())
    _model.teacher_in_period = pyo.Constraint(const_indices, rule=lambda _, idx: lhs(idx) <= 1)

def _set_constraint_3():
    Y_dict = {f'{j}_{xi}_{k}': (j, xi, k) for ((j, xi), k) in Y()}

    def lhs(idx):
        variables = []
        j, xi, k = Y_dict[idx]
        for i in V(j):
            variables.append(_model.psi[format_psi_index(i, j, xi, k)])
        return sum(variables)

    const_indices = list(Y_dict.keys())
    _model.teachers_overlapping = pyo.Constraint(const_indices, rule=lambda _, idx: lhs(idx) <= 1)

def _set_constraint_4():
    D_dict = {f'{j}_{xi}': (j, xi) for j, xi in D()}

    def lhs(idx):
        variables = []
        j, xi = D_dict[idx]
        for t in cart([V(j), [j], [xi], P()], ravel=True):
            variables.append(_model.psi[format_psi_index(*t)])
        return sum(variables)

    const_indices = list(D_dict.keys())
    _model.total_sections = pyo.Constraint(const_indices, rule=lambda _, idx: lhs(idx) <= 1)

def _set_constraint_5():
    K_dict = {f'{i}_{j}': (i, j) for i, j in K()}

    def lhs(idx):
        i, j = K_dict[idx]
        variables = [_model.sigma[format_sigma_index(i, j)]]
        for xi, k in cart([Xi(j), P()]):
            variables.append(_model.omega[format_omega_index(i, j, xi, k)])
        return sum(variables)

    const_indices = list(K_dict.keys())
    _model.students_classes_fulfillment = pyo.Constraint(const_indices, rule=lambda _, idx: lhs(idx) == 1)

def _set_constraint_6():
    SxP_dict = {f'{i}_{k}': (i, CS_i, k) for ((i, CS_i), k) in cart([S(), P()])}

    def lhs(idx):
        variables = []
        i, CS_i, k = SxP_dict[idx]
        for j in CS_i:
            for t in cart([[i], [j], Xi(j), [k]], ravel=True):
                variables.append(_model.omega[format_omega_index(*t)])
        return sum(variables)

    const_indices = list(SxP_dict.keys())
    _model.student_in_period = pyo.Constraint(const_indices, rule=lambda _, idx: lhs(idx) == 1)

def _set_constraint_7():
    Y_dict = {f'{j}_{xi}_{k}': (j, xi, k) for ((j, xi), k) in Y()}

    def lhs(idx):
        variables = []
        j, xi, k = Y_dict[idx]
        for i in W(j):
            variables.append(_model.omega[format_omega_index(i, j, xi, k)])
        return sum(variables)

    def rhs(idx):
        variables = []
        j, xi, k = Y_dict[idx]
        for i in V(j):
            variables.append(_model.psi[format_psi_index(i, j, xi, k)])
        return sum(variables)

    const_indices = list(Y_dict.keys())
    _model.max_students_if_has_teacher = pyo.Constraint(const_indices, rule=lambda _, idx: lhs(idx) <= L_max() * rhs(idx))
#endregion Model creation

def initialize(global_data, teachers_data, students_data):
    global _model
    global _global_data
    global _teachers_data
    global _students_data

    _global_data = global_data
    _teachers_data = teachers_data
    _students_data = students_data

    model = pyo.ConcreteModel()
    _model = model

    _set_psi_variables()
    _set_omega_variables()
    _set_sigma_variables()
    _set_objective()
    _set_constraint_1()
    _set_constraint_2()
    _set_constraint_3()
    _set_constraint_4()
    _set_constraint_5()
    _set_constraint_6()
    _set_constraint_7()

    # model.write('lp.lp', io_options={'symbolic_solver_labels': True})


# def show():
#     indices = []
#     for i, CT_i in T():
#         for j in CT_i:
#             indices.extend(cart([[i], [j], Xi(j), P()], ravel=True))
#     indices = list(map(lambda t: (t, format_psi_index(*t)), indices))
#     for (i, j, xi, k), idx in indices:
#         if _model.psi[idx]() < .8:
#             continue
#         print(f'{i} {j} {xi} {k}: {_model.psi[idx]()}')

#     print()

#     indices = []
#     for i, CS_i in S():
#         for j in CS_i:
#             indices.extend(cart([[i], [j], Xi(j), P()], ravel=True))
#     indices = list(map(lambda t: (t, format_omega_index(*t)), indices))
#     for (i, j, xi, k), idx in indices:
#         if _model.omega[idx]() < .8:
#             continue
#         print(f'{i} {j} {xi} {k}: {_model.omega[idx]()}')

#     print()

#     indices = []
#     for i, j in K():
#         indices.append((i, j))
#     indices = list(map(lambda t: (t, format_sigma_index(*t)), indices))
#     for (i, j), idx in indices:
#         # if idx in _model.psi:
#         if _model.sigma[idx]() < .8:
#             continue
#         print(f'{i} {j}: {_model.sigma[idx]()}')

def solve():
    solver = pyo.SolverFactory('cbc', executable='../exe/Cbc/bin/cbc.exe')
    solver.options['LogFile'] = 'log.log'

    status = solver.solve(_model, options={"threads": 8})

    print(status)

    teachers_summary = results_summary.get_teachers_scheduling_summary_text(
        _model.psi, _global_data, _teachers_data)

    students_summary = results_summary.get_students_scheduling_summary_text(
        _model.psi, _model.omega, _global_data, _students_data, _teachers_data)

    students_missed_classes = results_summary.get_students_missed_classes(
        _model.sigma, _students_data)

    return teachers_summary, students_summary, students_missed_classes