import pandas as pd

class GlobalData:
    def __init__(self, num_periods, lunch_period, min_periods_per_teacher, max_periods_per_teacher, max_students_per_class, sections_per_course):
        #TODO: Do some assertions here
        self.num_periods = num_periods
        self.lunch_period = lunch_period
        self.periods = list(set(range(1, num_periods + 1)) - {lunch_period})
        self.min_periods_per_teacher = min_periods_per_teacher
        self.max_periods_per_teacher = max_periods_per_teacher
        self.max_students_per_class = max_students_per_class
        self.courses_sections = {course: list(range(1, sections_per_course[course] + 1)) 
                                 for course in sections_per_course}
        self.all_courses = None

class TeachersData:
    def __init__(self, df):
        self.teachers = self.get_teachers_dict(df)
        
    def get_teachers_dict(self, df):
        d = {}
        for i, name in enumerate(df['Teacher Name']):
            if name in df:
                raise Exception(f"Duplicated teacher name '{name}'")
            d[name] = []
            for course in df.columns[1:]:
                if pd.isna(df.loc[i, course]):
                    continue
                d[name].append(df.loc[i, course])
            if len(d[name]) == 0:
                print(f"Warning: Teacher '{name}' has 0 courses")
        return d
    
class StudentsData:
    def __init__(self, df):
        self.students = self.get_students_dict(df)
        
    def get_students_dict(self, df):
        d = {}
        for i, name in enumerate(df['STUDENT']):
            if name in df:
                raise Exception(f"Duplicated student name '{name}'")
            d[name] = []
            for course in df.columns[2:]:
                if pd.isna(df.loc[i, course]):
                    continue
                d[name].append(df.loc[i, course])
            if len(d[name]) == 0:
                print(f"Warning: Student '{name}' has 0 courses")
        return d

def _validate_courses(teachers_data, students_data, global_data):
    teachers_courses = set()
    for courses in teachers_data.teachers.values():
        teachers_courses |= set(courses)
    for name, courses in students_data.students.items():
        for c in courses:
            if c not in teachers_courses:
                raise Exception(f"Student '{name}' has an invalid course '{c}'")
    for c in global_data.courses_sections:
        if c not in teachers_courses:
            raise Exception(f"Courses sections has an invalid course '{c}'")
                
def _post_process_global_data(teachers_data, global_data):
    teachers_courses = set()
    for courses in teachers_data.teachers.values():
        teachers_courses |= set(courses)
    for c in teachers_courses:
        if c not in global_data.courses_sections:
            global_data.courses_sections[c] = [1]
    global_data.all_courses = teachers_courses

def get_data_objects(teachers_df, students_df, num_periods, lunch_period, min_periods_per_teacher, max_periods_per_teacher, max_students_per_class, sections_per_course):
    gd = GlobalData(num_periods, lunch_period, min_periods_per_teacher, max_periods_per_teacher, max_students_per_class, sections_per_course)
    td = TeachersData(teachers_df)
    sd = StudentsData(students_df)

    _validate_courses(td, sd, gd)
    _post_process_global_data(td, gd)

    return gd, td, sd