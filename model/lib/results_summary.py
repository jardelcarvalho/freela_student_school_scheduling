def get_teachers_scheduling_summary_text(psi, global_data, teachers_data):
    scheduling = {}
    for i, courses in teachers_data.teachers.items():
        scheduling[i] = [('Lunch', '', global_data.lunch_period)]
        free_periods = set(global_data.periods)
        for j in courses:    
            for xi in global_data.courses_sections[j]:
                for k in global_data.periods:
                    if psi[f'{i}_{j}_{xi}_{k}']() > .5:
                        scheduling[i].append((j, xi, k))
                        free_periods -= {k}
        for k in free_periods:
            scheduling[i].append(('Free Period', '', k))

    def fmt_fun(t):
        if t[0] in ('Lunch', 'Free Period'):
            return f'Period {t[-1]}: {t[0]}'
        return f'Period {t[-1]}: {t[0]} - Section {t[1]}'

    texts = {}
    for name, periods in scheduling.items():
        ordered = sorted(periods, key=lambda t: t[-1])
        formated = list(map(fmt_fun, ordered))
        texts[name] = formated

    return texts
                    
def _build_teacher_search_tree(psi, global_data, teachers_data):
    tree = {}
    for i, courses in teachers_data.teachers.items():
        for j in courses:
            for xi in global_data.courses_sections[j]:
                for k in global_data.periods:
                    if psi[f'{i}_{j}_{xi}_{k}']() > .5:
                        if k not in tree:
                            tree[k] = {}
                        if j not in tree[k]:
                            tree[k][j] = {}
                        tree[k][j][xi] = i
    return tree

def get_students_scheduling_summary_text(psi, omega, global_data, students_data, teachers_data):
    tree = _build_teacher_search_tree(psi, global_data, teachers_data)

    scheduling = {}
    for i, courses in students_data.students.items():
        scheduling[i] = [('Lunch', '', global_data.lunch_period, '')]
        free_periods = set(global_data.periods)
        for j in courses:    
            for xi in global_data.courses_sections[j]:
                for k in global_data.periods:
                    if omega[f'{i}_{j}_{xi}_{k}']() > .5:
                        scheduling[i].append((j, xi, k, tree[k][j][xi]))
                        free_periods -= {k}
        for k in free_periods:
            scheduling[i].append(('Free Period', '', k, ''))

    def fmt_fun(t):
        if t[0] in ('Lunch', 'Free Period'):
            return f'Period {t[-2]}: {t[0]}'
        return f'Period {t[-2]}: {t[0]} - Section {t[1]} - {t[-1]}'

    texts = {}
    for name, periods in scheduling.items():
        ordered = sorted(periods, key=lambda t: t[-2])
        formated = list(map(fmt_fun, ordered))
        texts[name] = formated

    return texts

def get_students_missed_classes(sigma, students_data):
    res = {}
    for i, courses in students_data.students.items():
        for j in courses:
            if sigma[f'{i}_{j}']() > .5:
                if i not in res:
                    res[i] = []
                res[i].append(j)
    return res