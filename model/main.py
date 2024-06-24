import lib.io
import lib.data
import lib.model

if __name__ == '__main__':
    sections_per_course = {
        'GLOBAL 9': 2,
        'HEALTH': 2,
        'ALGEBRA I': 2,
        'RESTORATIVE JUSTICE 1': 2,
        'ENGLISH 9': 2,
        'PE 1': 2,
        'CIVICS': 2,
        'LIVING ENVIRONMENT': 2
    }

    # import os
    # print(os.getcwd())
    # exit(0)

    gd, td, sd = lib.data.get_data_objects(
        lib.io.get_teachers_df('../specification/SAMPLE MASTER1.xlsx')[:], 
        lib.io.get_students_df('../specification/SAMPLE MASTER1.xlsx')[:20], 
        8, 
        5, 
        0, 
        5, 
        34, 
        sections_per_course)

    lib.model.initialize(gd, td, sd)

    import time
    start = time.time()

    teachers_summary, students_summary, students_missed_classes = lib.model.solve()

    print('Total time:', time.time() - start)

    lib.io.write_results(teachers_summary, students_summary, students_missed_classes)