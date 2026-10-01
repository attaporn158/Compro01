from datetime import datetime
import os
import shutil
import struct
import subprocess
from typing import List, Tuple
import unicodedata

STUDENT_FILE = "students.dat"
COURSE_FILE = "courses.dat"
ENROLLMENT_FILE = "enrollments.dat"

STUDENT_STRUCT = struct.Struct("<q90s90s90si")
COURSE_STRUCT = struct.Struct("<20s90sI90s")
ENROLLMENT_STRUCT = struct.Struct("<q20s10s")

REPORT_FILE = "Registration_report.txt"


def pack_string(s: str, max_bytes: int) -> bytes:
    encoded = s.strip().encode("utf-8")
    if len(encoded) > max_bytes:
        encoded = (
            encoded[:max_bytes].decode("utf-8", errors="ignore").encode("utf-8")
        )
    return encoded.ljust(max_bytes, b"\x00")


def unpack_string(b: bytes) -> str:
    return b.decode("utf-8", errors="ignore").rstrip("\x00").strip()


def clean_thai_str(text):
    return unicodedata.normalize("NFC", str(text))


def display_width(text):

    text = clean_thai_str(text)
    width = 0

    for ch in text:
        category = unicodedata.category(ch)

 
        if category in ("Mn", "Me", "Cf"):
            continue

        width += 1

    return width


def fit_to_width(text, width):
 
    text = clean_thai_str(text)

    result = []
    current_width = 0

    for ch in text:
        category = unicodedata.category(ch)

        if category in ("Mn", "Me", "Cf"):
            char_width = 0
        else:
            char_width = 1

        if current_width + char_width > width:
            break

        result.append(ch)
        current_width += char_width

    return "".join(result), current_width


def pad_str(s, width, align="left"):
   
    text, current_width = fit_to_width(s, width)

    padding = width - current_width

    if align == "right":
        return (" " * padding) + text

    elif align == "center":
        left = padding // 2
        right = padding - left
        return (" " * left) + text + (" " * right)

    else:
        return text + (" " * padding)


def read_file(filename: str, struct_def: struct.Struct) -> List[Tuple]:
    records = []
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(struct_def.size)
                if not chunk:
                    break
                if len(chunk) == struct_def.size:
                    records.append(struct_def.unpack(chunk))
    return records


def write_file(filename: str, struct_def: struct.Struct, records: List[Tuple]):
    with open(filename, "wb") as f:
        for rec in records:
            f.write(struct_def.pack(*rec))
        f.flush()
        os.fsync(f.fileno())

def append_record(
    filename: str, struct_def: struct.Struct, record: Tuple
) -> None:
    with open(filename, "ab") as f:
        f.write(struct_def.pack(*record))
        f.flush()
        os.fsync(f.fileno())


# --- Add ---

def add_student():
    print("\n --- Add Student ---")
    try:
        student_id = int(input("Student ID: ").strip())
    except ValueError:
        print("[Error] Student ID must be a number.")
        return

    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    if any(s[0] == student_id for s in students):
        print("[Error] Student ID already exists.")
        return

    name = input("Name: ").strip()
    faculty = input("Faculty: ").strip()
    major = input("Major: ").strip()

    try:
        year = int(input("Year (1-8): ").strip())
        if not (1 <= year <= 8):
            print("[Error] Year must be between 1 and 8.")
            return
    except ValueError:
        print("[Error] Year must be a number.")
        return

    record = (
        student_id,
        pack_string(name, 90),
        pack_string(faculty, 90),
        pack_string(major, 90),
        year,
    )
    append_record(STUDENT_FILE, STUDENT_STRUCT, record)
    print("Student data saved successfully.")


def add_course():
    print("\n --- Add Course ---")
    course_id = input("Course ID: ").strip()
    if not course_id:
        print("[Error] Course ID cannot be empty.")
        return

    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    if any(unpack_string(c[0]).upper() == course_id.upper() for c in courses):
        print("[Error] Course ID already exists.")
        return

    name = input("Course Name: ").strip()

    try:
        credits = int(input("Credits (1-10): ").strip())
        if not (1 <= credits <= 10):
            print("[Error] Credits must be between 1 and 10.")
            return
    except ValueError:
        print("[Error] Credits must be a number.")
        return

    instructor_name = input("Instructor Name: ").strip()

    record = (
        pack_string(course_id, 20),
        pack_string(name, 90),
        credits,
        pack_string(instructor_name, 90),
    )
    append_record(COURSE_FILE, COURSE_STRUCT, record)
    print("Course data saved successfully.")


def add_enrollment():
    print("\n --- Enrollment ---")
    try:
        student_id = int(input("Student ID: ").strip())
    except ValueError:
        print("[Error] Student ID must be a number.")
        return

    course_id = input("Course ID: ").strip()
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)

    if not any(s[0] == student_id for s in students):
        print("[Error] Student ID not found in system.")
        return
    if not any(unpack_string(c[0]).upper() == course_id.upper() for c in courses):
        print("[Error] Course ID not found in system.")
        return

    for i, e in enumerate(enrollments):
        if (
            e[0] == student_id
            and unpack_string(e[1]).upper() == course_id.upper()
        ):
            status = unpack_string(e[2])
            if status == "Enrolled":
                print("[Error] Student has already enrolled in this course.")
                return
            elif status == "Dropped":
                enrollments[i] = (
                    student_id,
                    pack_string(course_id, 20),
                    pack_string("Enrolled", 10),
                )
                write_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT, enrollments)
                print(
                    "Enrollment status updated to 'Enrolled' successfully."
                )
                return

    record = (
        student_id,
        pack_string(course_id, 20),
        pack_string("Enrolled", 10),
    )
    append_record(ENROLLMENT_FILE, ENROLLMENT_STRUCT, record)
    print("Enrollment data saved successfully.")


def menu_add():
    while True:
        print("\n==========================================")
        print("  1) Add ")
        print("==========================================")
        print("1. Add Student (เพิ่มข้อมูลนักศึกษา)")
        print("2. Add Course (เพิ่มข้อมูลรายวิชา)")
        print("3. Add Enrollment (ลงทะเบียนเรียน)")
        print("0. Back to Main Menu")
        choice = input("Select sub-menu [0-3]: ").strip()

        if choice == "1":
            add_student()
        elif choice == "2":
            add_course()
        elif choice == "3":
            add_enrollment()
        elif choice == "0":
            break
        else:
            print("Invalid option.")


# --- Update ---

def update_student():
    print("\n --- Update Student ---")
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    try:
        student_id = int(input("Enter Student ID to update: ").strip())
    except ValueError:
        print("[Error] Student ID must be a number.")
        return

    for i, s in enumerate(students):
        if s[0] == student_id:
            curr_name = unpack_string(s[1])
            curr_fac = unpack_string(s[2])
            curr_major = unpack_string(s[3])
            print("(Press Enter to keep current value)")
            name = input(f"New Name [{curr_name}]: ").strip() or curr_name
            faculty = input(f"New Faculty [{curr_fac}]: ").strip() or curr_fac
            major = input(f"New Major [{curr_major}]: ").strip() or curr_major

            year_in = input(f"New Year [{s[4]}]: ").strip()
            if year_in:
                try:
                    year = int(year_in)
                    if not (1 <= year <= 8):
                        print("[Error] Year must be between 1 and 8.")
                        return
                except ValueError:
                    print("[Error] Year must be a number.")
                    return
            else:
                year = s[4]

            students[i] = (
                student_id,
                pack_string(name, 90),
                pack_string(faculty, 90),
                pack_string(major, 90),
                year,
            )
            write_file(STUDENT_FILE, STUDENT_STRUCT, students)
            print("Student data updated successfully.")
            return

    print("Student ID not found.")


def update_course():
    print("\n --- Update Course ---")
    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    course_id = input("Enter Course ID to update: ").strip()

    for i, c in enumerate(courses):
        if unpack_string(c[0]).upper() == course_id.upper():
            curr_name = unpack_string(c[1])
            curr_inst = unpack_string(c[3])
            print("(Press Enter to keep current value)")
            name = input(f"New Course Name [{curr_name}]: ").strip() or curr_name

            cred_in = input(f"New Credits [{c[2]}]: ").strip()
            if cred_in:
                try:
                    credits = int(cred_in)
                    if not (1 <= credits <= 10):
                        print("[Error] Credits must be between 1 and 10.")
                        return
                except ValueError:
                    print("[Error] Credits must be a number.")
                    return
            else:
                credits = c[2]

            inst_name = (
                input(f"New Instructor Name [{curr_inst}]: ").strip()
                or curr_inst
            )

            courses[i] = (
                pack_string(course_id, 20),
                pack_string(name, 90),
                credits,
                pack_string(inst_name, 90),
            )
            write_file(COURSE_FILE, COURSE_STRUCT, courses)
            print("Course data updated successfully.")
            return

    print("Course ID not found.")


def menu_update():
    while True:
        print("\n==========================================")
        print("  2) Update ")
        print("==========================================")
        print("1. Update Student Data")
        print("2. Update Course Data")
        print("0. Back to Main Menu")
        choice = input("Select sub-menu [0-2]: ").strip()

        if choice == "1":
            update_student()
        elif choice == "2":
            update_course()
        elif choice == "0":
            break
        else:
            print("Invalid option.")


# --- Delete / Drop ---

def delete_student():
    print("\n --- Delete Student Permanently ---")
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    try:
        student_id = int(input("Enter Student ID to delete: ").strip())
    except ValueError:
        print("[Error] Student ID must be a number.")
        return

    new_students = [s for s in students if s[0] != student_id]
    if len(new_students) < len(students):
        write_file(STUDENT_FILE, STUDENT_STRUCT, new_students)

        enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)
        new_enrollments = [e for e in enrollments if e[0] != student_id]
        write_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT, new_enrollments)

        print("Student and associated enrollment data deleted successfully.")
    else:
        print("Student ID not found.")


def delete_course():
    print("\n --- Delete Course Permanently ---")
    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    course_id = input("Enter Course ID to delete: ").strip()

    new_courses = [
        c for c in courses if unpack_string(c[0]).upper() != course_id.upper()
    ]
    if len(new_courses) < len(courses):
        write_file(COURSE_FILE, COURSE_STRUCT, new_courses)

        enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)
        new_enrollments = [
            e
            for e in enrollments
            if unpack_string(e[1]).upper() != course_id.upper()
        ]
        write_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT, new_enrollments)

        print("Course and associated enrollment data deleted successfully.")
    else:
        print("Course ID not found.")

def drop_enrollment():
    print("\n --- Drop Course ---")
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)
    try:
        student_id = int(input("Student ID: ").strip())
    except ValueError:
        print("[Error] Student ID must be a number.")
        return
    course_id = input("Course ID: ").strip()

    updated = False
    for i, e in enumerate(enrollments):
        if (
            e[0] == student_id
            and unpack_string(e[1]).upper() == course_id.upper()
        ):
            if unpack_string(e[2]) == "Dropped":
                print("[Notice] Student has already dropped this course.")
                return
            enrollments[i] = (
                student_id,
                pack_string(course_id, 20),
                pack_string("Dropped", 10),
            )
            updated = True
            break

    if updated:
        write_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT, enrollments)
        print("Course dropped successfully (Status changed to Dropped).")
    else:
        print("Enrollment record not found.")

def menu_delete():
    while True:
        print("\n==========================================")
        print("  3) Delete/Drop ")
        print("==========================================")
        print("1. Delete Student")
        print("2. Delete Course")
        print("3. Drop Course Enrollment")
        print("0. Back to Main Menu")
        choice = input("Select sub-menu [0-3]: ").strip()

        if choice == "1":
            delete_student()
        elif choice == "2":
            delete_course()
        elif choice == "3":
            drop_enrollment()
        elif choice == "0":
            break
        else:
            print("Invalid option.")


# --- View & Search ---

def search_student_courses():
    try:
        student_id = int(input("\nEnter Student ID: ").strip())
    except ValueError:
        print("[Error] Student ID must be a number.")
        return

    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)

    student = next((s for s in students if s[0] == student_id), None)
    if not student:
        print("Student ID not found.")
        return

    print(
        f"\n--- Courses Enrolled by: {unpack_string(student[1])} (ID: {student_id}) ---"
    )
    st_enrolls = [e for e in enrollments if e[0] == student_id]

    if not st_enrolls:
        print("No courses enrolled.")
        return

    total_credits = 0
    for e in st_enrolls:
        c_id = unpack_string(e[1])
        status = unpack_string(e[2])
        course = next(
            (c for c in courses if unpack_string(c[0]).upper() == c_id.upper()),
            None,
        )
        c_name = unpack_string(course[1]) if course else "Unknown"
        c_cred = course[2] if course else 0
        inst_name = unpack_string(course[3]) if course else "Unknown"

        if status == "Enrolled":
            total_credits += c_cred

        print(
            f"- [{pad_str(c_id, 10)}] {pad_str(c_name, 30)} | Credits: {c_cred} | Instructor: {pad_str(inst_name, 20)} | Status: {status}"
        )

    print(
        "--------------------------------------------------------------------------------"
    )
    print(f"Total Enrolled Credits: {total_credits} Credits")


def search_course_students():
    course_id = input("\nEnter Course ID: ").strip()
    if not course_id:
        print("[Error] Course ID cannot be empty.")
        return

    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)

    course = next(
        (c for c in courses if unpack_string(c[0]).upper() == course_id.upper()),
        None,
    )
    if not course:
        print("Course ID not found.")
        return

    print(
        f"\n--- Students Enrolled in Course: {unpack_string(course[1])} ({course_id.upper()}) ---"
    )
    c_enrolls = [
        e
        for e in enrollments
        if unpack_string(e[1]).upper() == course_id.upper()
    ]

    if not c_enrolls:
        print("No students enrolled in this course.")
        return

    for e in c_enrolls:
        s_id = e[0]
        status = unpack_string(e[2])
        student = next((s for s in students if s[0] == s_id), None)
        s_name = unpack_string(student[1]) if student else "Unknown"
        print(
            f"- Student ID: {pad_str(str(s_id), 15)} | Name: {pad_str(s_name, 25)} | Status: {status}"
        )

def search_instructor_courses():
    inst_name_search = input("\nEnter Instructor Name: ").strip().lower()
    if not inst_name_search:
        print("[Error] Instructor Name cannot be empty.")
        return

    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)

    inst_courses = [
        c for c in courses if inst_name_search in unpack_string(c[3]).lower()
    ]

    if not inst_courses:
        print("No courses found for this instructor.")
        return

    print(
        f"\n================================================================================"
    )
    print(
        f" Courses & Enrolled Students Taught by Instructor matching: '{inst_name_search}'"
    )
    print(
        f"================================================================================"
    )

    total_credits = 0
    for c in inst_courses:
        c_id = unpack_string(c[0])
        c_name = unpack_string(c[1])
        c_cred = c[2]
        inst_name = unpack_string(c[3])
        total_credits += c_cred

        print(
            f"\nCourse: [{c_id}] {c_name} | Credits: {c_cred} | Instructor: {inst_name}"
        )
        print("  Enrolled Students:")

        c_enrolls = [
            e
            for e in enrollments
            if unpack_string(e[1]).upper() == c_id.upper()
        ]

        if not c_enrolls:
            print("    (No students enrolled in this course)")
        else:
            for e in c_enrolls:
                s_id = e[0]
                status = unpack_string(e[2])
                student = next((s for s in students if s[0] == s_id), None)
                s_name = unpack_string(student[1]) if student else "Unknown"
                s_dept = unpack_string(student[3]) if student else "Unknown"
                print(
                    f"    - ID: {pad_str(str(s_id), 13)} | Name: {pad_str(s_name, 22)} | Dept: {pad_str(s_dept, 15)} | Status: {status}"
                )

    print(
        "\n--------------------------------------------------------------------------------"
    )
    print(f"Total Teaching Credits for Instructor: {total_credits} Credits")


def view_all():
    print("\n================ All Students ================")
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    if not students:
        print("No student records found.")
    for s in students:
        print(
            f"ID: {pad_str(str(s[0]), 15)} | Name: {pad_str(unpack_string(s[1]), 25)} | Faculty: {pad_str(unpack_string(s[2]), 12)} | Major: {pad_str(unpack_string(s[3]), 12)} | Year: {s[4]}"
        )

    print("\n================ All Courses ================")
    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    if not courses:
        print("No course records found.")
    for c in courses:
        print(
            f"ID: {pad_str(unpack_string(c[0]), 12)} | Name: {pad_str(unpack_string(c[1]), 30)} | Credits: {c[2]} | Instructor: {unpack_string(c[3])}"
        )

    print("\n================ All Enrollments ================")
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)
    if not enrollments:
        print("No enrollment records found.")
    for e in enrollments:
        print(
            f"Student ID: {pad_str(str(e[0]), 15)} | Course ID: {pad_str(unpack_string(e[1]), 12)} | Status: {unpack_string(e[2])}"
        )

def menu_view():
    while True:
        print("\n==========================================")
        print("  4) View & Search ")
        print("==========================================")
        print(
            "1. Search Courses by Student ID (ค้นหาวิชาตามรหัสนักศึกษา + รวมหน่วยกิต)"
        )
        print("2. Search Students by Course ID (ค้นหานักศึกษาตามรหัสวิชา)")
        print(
            "3. Search Courses & Students by Instructor (ค้นหาวิชาและนักศึกษาตามชื่ออาจารย์)"
        )
        print("4. View All Records (แสดงข้อมูลทั้งหมด)")
        print("0. Back to Main Menu")
        choice = input("Select sub-menu [0-4]: ").strip()

        if choice == "1":
            search_student_courses()
        elif choice == "2":
            search_course_students()
        elif choice == "3":
            search_instructor_courses()
        elif choice == "4":
            view_all()
        elif choice == "0":
            break
        else:
            print("Invalid option.")


# --- Generate Report ---

def generate_report():
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)
    now_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    w = [18, 30, 8, 10, 10, 12, 30, 40, 10, 10]
    LINE_WIDTH = sum(w) + (len(w) * 3) + 1  

    headers = [
        "Stud.ID", "Name", "Faculty", "Major", 
        "Year", "Course ID", "Course Name", "Instructor", "Credits", "Status"
    ]

    def draw_border():
        return "+" + "+".join("-" * (width + 2) for width in w) + "+"

    def draw_row(values):
        cells = []
        for i, width in enumerate(w):
            value = values[i] if i < len(values) else ""
            value = str(value)
            cells.append(pad_str(value, width))
        return "| " + " | ".join(cells) + " |"

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
      
        f.write("=" * LINE_WIDTH + "\n")
        f.write("REGISTRATION SYSTEM - SUMMARY REPORT".center(LINE_WIDTH) + "\n")
        f.write("=" * LINE_WIDTH + "\n")
        f.write(f" Generated At : {now_str}\n")
        f.write(" App Version  : 1.0\n")
        f.write(" Encoding     : UTF-8 (fixed-length)\n")
        f.write("=" * LINE_WIDTH + "\n\n")

      
        f.write("ALL STUDENTS & ENROLLMENT DETAILS\n")
        f.write(draw_border() + "\n")
        f.write(draw_row(headers) + "\n")
        f.write(draw_border() + "\n")

        for s in students:
            stud_id = s[0]
            name = unpack_string(s[1])
            faculty = unpack_string(s[2])
            major = unpack_string(s[3])
            year = s[4]

            stud_enroll = [e for e in enrollments if e[0] == stud_id]

            if stud_enroll:
                for idx, e in enumerate(stud_enroll):
                    course_id = unpack_string(e[1])
                    status = unpack_string(e[2]) if len(e) > 2 else "Enrolled"

                    course = next((c for c in courses if unpack_string(c[0]).upper() == course_id.upper()), None)
                    course_name = unpack_string(course[1]) if course else "Unknown"
                    instructor = unpack_string(course[3]) if course else "Unknown"
                    credits = course[2] if course else 0

                    if idx == 0:
                        row_vals = [stud_id, name, faculty, major, year, course_id, course_name, instructor, credits, status]
                    else:
                        row_vals = ["", "", "", "", "", course_id, course_name, instructor, credits, status]

                    f.write(draw_row(row_vals) + "\n")
            else:
                f.write(draw_row([stud_id, name, faculty, major, year, "-", "-", "-", "-", "-"]) + "\n")

            f.write(draw_border() + "\n")

        
        total_enrolled = sum(1 for e in enrollments if unpack_string(e[2]).lower() == "enrolled")
        total_dropped = sum(1 for e in enrollments if unpack_string(e[2]).lower() == "dropped")

        f.write("\n\n" + "=" * LINE_WIDTH + "\n")
        f.write("SYSTEM STATISTICAL SUMMARY\n")
        f.write("-" * LINE_WIDTH + "\n")
        f.write(f"  * Total Students    : {len(students)} Person(s)\n")
        f.write(f"  * Total Courses     : {len(courses)} Course(s)\n")
        f.write(f"  * Total Enrollments : {len(enrollments)} Record(s)\n")
        f.write(f"    - Active Enrolled : {total_enrolled}\n")
        f.write(f"    - Dropped         : {total_dropped}\n")
        f.write("-" * LINE_WIDTH + "\n\n")

     
        faculty_courses = {}
        for s in students:
            fac = unpack_string(s[2])
            if fac:
                stud_enroll = [e for e in enrollments if e[0] == s[0]]
                faculty_courses[fac] = faculty_courses.get(fac, 0) + len(stud_enroll)

        f.write("COURSES ENROLLED BY FACULTY\n")
        f.write("-" * LINE_WIDTH + "\n")
        for fac, count in faculty_courses.items():
            f.write(f"  * {pad_str(fac, 25)} : {count} Enrollment(s)\n")
        f.write("-" * LINE_WIDTH + "\n\n")

    
        instructor_credits = {}
        for c in courses:
            inst = unpack_string(c[3])
            cred = c[2]
            if inst:
                instructor_credits[inst] = instructor_credits.get(inst, 0) + cred

        f.write("CREDITS TAUGHT BY INSTRUCTOR\n")
        f.write("-" * LINE_WIDTH + "\n")
        for inst, creds in instructor_credits.items():
            f.write(f"  * {pad_str(inst, 45)} : {creds} Credit(s)\n")
        f.write("=" * LINE_WIDTH + "\n")

  
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        desktop_file = os.path.join(desktop, REPORT_FILE)
        shutil.copyfile(REPORT_FILE, desktop_file)

        if os.name == "nt":
            subprocess.Popen(["notepad.exe", desktop_file])
        elif os.name == "posix":
            opener = "open" if "DARWIN" in os.uname().sysname.upper() else "xdg-open"
            subprocess.Popen([opener, desktop_file])
    except Exception:
        pass

    print(f"\n[Success] Report generated successfully: {REPORT_FILE}")

INSTRUCTOR_REPORT_FILE = "Instructor_report.txt"

def generate_instructor_report():
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)
    now_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

 
    instructors = {}
    for c in courses:
        inst_name = unpack_string(c[3]) or "Unassigned"
        if inst_name not in instructors:
            instructors[inst_name] = []
        instructors[inst_name].append(c)

   
    w = [8, 25, 65, 45, 35, 10]
    LINE_WIDTH = sum(w) + (len(w) * 3) + 1  

    headers = ["No.", "Student ID", "Student Name", "Faculty", "Major", "Year"]

    def draw_border():
        return "+" + "+".join("-" * (width + 2) for width in w) + "+"

    def draw_row(values):
        cells = []
        for i, width in enumerate(w):
            value = values[i] if i < len(values) else ""
            value = str(value)
            cells.append(pad_str(value, width))
        return "| " + " | ".join(cells) + " |"

    with open(INSTRUCTOR_REPORT_FILE, "w", encoding="utf-8") as f:
        
        f.write("=" * LINE_WIDTH + "\n")
        f.write("INSTRUCTOR TEACHING & ENROLLMENT REPORT".center(LINE_WIDTH) + "\n")
        f.write("=" * LINE_WIDTH + "\n")
        f.write(f" Generated At      : {now_str}\n")
        f.write(f" Total Instructors : {len(instructors)}\n")
        f.write("=" * LINE_WIDTH + "\n\n\n")

        for inst_name, inst_courses in instructors.items():
           
            f.write(" " + "=" * (LINE_WIDTH - 2) + "\n")
            f.write(f"  INSTRUCTOR: {inst_name}\n")
            f.write(" " + "=" * (LINE_WIDTH - 2) + "\n\n")

            total_inst_credits = sum(c[2] for c in inst_courses)
            total_inst_students = 0

            for c in inst_courses:
                c_id = unpack_string(c[0])
                c_name = unpack_string(c[1])
                c_cred = c[2]

                c_enrolls = [
                    e for e in enrollments 
                    if unpack_string(e[1]).upper() == c_id.upper() and unpack_string(e[2]).lower() == "enrolled"
                ]
                student_count = len(c_enrolls)
                total_inst_students += student_count

              
                f.write(f"  [Course] {c_id} - {c_name}\n")
                f.write(f"  Credits: {c_cred}  |  Enrolled Students: {student_count} person(s)\n\n")

                if not c_enrolls:
                    f.write("    (No active enrolled students)\n\n")
                else:
                    
                    f.write(draw_border() + "\n")
                    f.write(draw_row(headers) + "\n")
                    f.write(draw_border() + "\n")

                    for idx, e in enumerate(c_enrolls, 1):
                        s_id = e[0]
                        student = next((s for s in students if s[0] == s_id), None)
                        s_name = unpack_string(student[1]) if student else "Unknown"
                        s_faculty = unpack_string(student[2]) if student else "Unknown"
                        s_dept = unpack_string(student[3]) if student else "Unknown"
                        s_year = student[4] if student else "-"

                        row_vals = [idx, s_id, s_name, s_faculty, s_dept, s_year]
                        f.write(draw_row(row_vals) + "\n")

                    f.write(draw_border() + "\n\n")

          
            f.write("  " + "-" * (LINE_WIDTH - 4) + "\n")
            f.write(f"  >> SUMMARY FOR {inst_name.upper()}\n")
            f.write(f"     * Total Courses Taught    : {len(inst_courses)} Course(s)\n")
            f.write(f"     * Total Credits Taught    : {total_inst_credits} Credit(s)\n")
            f.write(f"     * Total Enrolled Students : {total_inst_students} Person(s)\n")
            f.write("  " + "-" * (LINE_WIDTH - 4) + "\n\n\n")

    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        desktop_file = os.path.join(desktop, INSTRUCTOR_REPORT_FILE)
        shutil.copyfile(INSTRUCTOR_REPORT_FILE, desktop_file)

        if os.name == "nt":
            subprocess.Popen(["notepad.exe", desktop_file])
        elif os.name == "posix":
            opener = "open" if "DARWIN" in os.uname().sysname.upper() else "xdg-open"
            subprocess.Popen([opener, desktop_file])
    except Exception:
        pass

    print(f"[Success] Instructor Report generated successfully: {INSTRUCTOR_REPORT_FILE}")

STUDENT_REPORT_FILE = "Student_report.txt"

def generate_student_report():
    students = read_file(STUDENT_FILE, STUDENT_STRUCT)
    courses = read_file(COURSE_FILE, COURSE_STRUCT)
    enrollments = read_file(ENROLLMENT_FILE, ENROLLMENT_STRUCT)
    now_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    print("\n--- Generate Student Individual Report ---")
    try:
        search_id = int(input("Enter Student ID: ").strip())
    except ValueError:
        print("[Error] Invalid Student ID format.")
        return

    
    student = next((s for s in students if s[0] == search_id), None)
    if not student:
        print(f"[Error] Student ID '{search_id}' not found.")
        return

    stud_id = student[0]
    s_name = unpack_string(student[1])
    s_faculty = unpack_string(student[2])
    s_dept = unpack_string(student[3])
    s_year = student[4]


    stud_enrolls = [e for e in enrollments if e[0] == stud_id]

    w = [8, 25, 75, 55, 12, 15]
   
    LINE_WIDTH = sum(w) + (len(w) * 3) + 1 

    headers = ["No.", "Course ID", "Course Name", "Instructor", "Credits", "Status"]

    def draw_border():
        return "+" + "+".join("-" * (width + 2) for width in w) + "+"

    def draw_row(values):
        cells = []
        for i, width in enumerate(w):
            value = values[i] if i < len(values) else ""
            value = str(value)
            cells.append(pad_str(value, width))
        return "| " + " | ".join(cells) + " |"

    with open(STUDENT_REPORT_FILE, "w", encoding="utf-8") as f:
       
        f.write("=" * LINE_WIDTH + "\n")
        f.write("INDIVIDUAL STUDENT ENROLLMENT REPORT".center(LINE_WIDTH) + "\n")
        f.write("=" * LINE_WIDTH + "\n")
        f.write(f" Generated At : {now_str}\n")
        f.write("=" * LINE_WIDTH + "\n\n")

        f.write("STUDENT INFORMATION\n")
        f.write("-" * LINE_WIDTH + "\n")
        f.write(f"  Student ID : {stud_id}\n")
        f.write(f"  Name       : {s_name}\n")
        f.write(f"  Faculty    : {s_faculty}\n")
        f.write(f"  Department : {s_dept}\n")
        f.write(f"  Year       : {s_year}\n")
        f.write("-" * LINE_WIDTH + "\n\n")

        f.write("ENROLLED COURSES\n")
        f.write(draw_border() + "\n")
        f.write(draw_row(headers) + "\n")
        f.write(draw_border() + "\n")

        total_credits = 0
        enrolled_count = 0
        dropped_count = 0

        if not stud_enrolls:
            empty_msg = ["-", "-", "No registration record found", "-", "-", "-"]
            f.write(draw_row(empty_msg) + "\n")
        else:
            for idx, e in enumerate(stud_enrolls, 1):
                c_id = unpack_string(e[1])
                status = unpack_string(e[2]) if len(e) > 2 else "Enrolled"

                course = next((c for c in courses if unpack_string(c[0]).upper() == c_id.upper()), None)
                c_name = unpack_string(course[1]) if course else "Unknown"
                c_cred = course[2] if course else 0
                instructor = unpack_string(course[3]) if course else "Unknown"

                if status.lower() == "enrolled":
                    total_credits += c_cred
                    enrolled_count += 1
                elif status.lower() == "dropped":
                    dropped_count += 1

                row_vals = [idx, c_id, c_name, instructor, c_cred, status]
                f.write(draw_row(row_vals) + "\n")

        f.write(draw_border() + "\n\n")

        f.write("SUMMARY\n")
        f.write("-" * LINE_WIDTH + "\n")
        f.write(f"  * Total Active Courses : {enrolled_count} Course(s)\n")
        f.write(f"  * Total Dropped        : {dropped_count} Course(s)\n")
        f.write(f"  * Total Credits        : {total_credits} Credit(s)\n")
        f.write("=" * LINE_WIDTH + "\n")
    
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        desktop_file = os.path.join(desktop, STUDENT_REPORT_FILE)
        shutil.copyfile(STUDENT_REPORT_FILE, desktop_file)

        if os.name == "nt":
            subprocess.Popen(["notepad.exe", desktop_file])
        elif os.name == "posix":
            opener = "open" if "DARWIN" in os.uname().sysname.upper() else "xdg-open"
            subprocess.Popen([opener, desktop_file])
    except Exception:
        pass

    print(f"\n[Success] Individual Student Report generated successfully: {STUDENT_REPORT_FILE}")

    
# --- Main Menu ---

def main():
    while True:
        print("\n==========================================")
        print("  Registration System")
        print("==========================================")
        print("1) Add ")
        print("2) Update ")
        print("3) Delete/Drop ")
        print("4) View & Search ")
        print("5) Generate Summary Report (รวมนักศึกษาทั้งหมด)")
        print("6) Generate Instructor Report (รายงานอาจารย์ผู้สอน)")
        print("7) Generate Student Report (รายงานรายบุคคลนักศึกษา)")
        print("0) Exit")
        choice = input("Select option [0-7]: ").strip()
        if choice == "1":
            menu_add()
        elif choice == "2":
            menu_update()
        elif choice == "3":
            menu_delete()
        elif choice == "4":
            menu_view()
        elif choice == "5":
            generate_report()
        elif choice == "6":
            generate_instructor_report()
        elif choice == "7":
            generate_student_report()
        elif choice == "0":
            print("\nThe program has been closed.")
            break
        else:
            print("Invalid option. Please select [0-7].")

if __name__ == "__main__":
    main()
 