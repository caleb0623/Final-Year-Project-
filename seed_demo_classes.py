"""Create dummy classes for the coming week so lecturers have current classes when testing.

    python seed_demo_classes.py            # today + next 4 days
    python seed_demo_classes.py --days 7

Uses the same courses/lecturers as the migrated data and enrols every student. Safe to re-run:
a class with the same date, time and course is not created twice.
"""
import argparse
import re
from datetime import date, timedelta

import postgres_store as store

# (time, course, class type, lecturer) for each day
TIMETABLE = [
    ("08:00:00", "BACS3021", "L", "L00001"),
    ("10:00:00", "BACS3023", "T", "L00001"),
    ("14:00:00", "BACS3025", "L", "L00002"),
]


def next_class_id():
    numbers = [int(match.group(1)) for record in store.list_records("class")
               if (match := re.fullmatch(r"C(\d+)", record["classID"]))]
    return f"C{max(numbers, default=0) + 1:010d}"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=5)
    args = parser.parse_args()

    store.init_store()
    lecturers = {record["lecturerID"] for record in store.list_records("lecturer")}
    students = [record["studentID"] for record in store.list_records("Student")]
    existing = {(record.get("classDate"), record.get("classTime"), record.get("courseID"))
                for record in store.list_records("class")}

    created = 0
    for offset in range(args.days):
        day = (date.today() + timedelta(days=offset)).isoformat()
        for class_time, course, class_type, lecturer in TIMETABLE:
            if lecturer not in lecturers or (day, class_time, course) in existing:
                continue
            class_id = next_class_id()
            store.save_record("class", {
                "classID": class_id, "classDate": day, "classTime": class_time,
                "classType": class_type, "courseID": course, "lecturerID": lecturer,
            })
            for student_id in students:
                store.save_record("classDetails", {"classID": class_id, "studentID": student_id},
                                  record_id=f"DEMO-{class_id}-{student_id}")
            created += 1
            print(f"{class_id}  {day} {class_time}  {course} ({class_type})  {lecturer}  {len(students)} students")
    print(f"Created {created} demo class(es).")


if __name__ == "__main__":
    main()
