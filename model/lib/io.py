import pandas as pd
import numpy as np

def _pre_process_teachers_df(df):
    df.columns = df.loc[2].values
    df = df.drop([0, 1, 2]).reset_index(drop=True)

    #TEMPORARY
    df.loc[4, 'COURSE 1'] = 'JAPANESE 1'
    df.loc[0, 'COURSE 5'] = np.nan

    return df

def _pre_process_students_df(df):
    return df

def get_teachers_df(path):
    df = pd.read_excel(path, sheet_name='Teachers')
    df = _pre_process_teachers_df(df)
    return df

def get_students_df(path):
    df = pd.read_excel(path, sheet_name='Students')
    df = _pre_process_students_df(df)
    return df

def write_results(teachers_summary, students_summary, students_missed_classes):
    with open('../teachers.txt', 'w') as f:
        for name, texts in teachers_summary.items():
            print(f'{name}', file=f)
            print('\n'.join(texts), file=f)
            print('\n', file=f)

    with open('../students.txt', 'w') as f:
        for name, texts in students_summary.items():
            print(f'{name}', file=f)
            print('\n'.join(texts), file=f)
            if name in students_missed_classes:
                print(f"Missed classes: {', '.join(students_missed_classes[name])}", file=f)
            print('\n', file=f)