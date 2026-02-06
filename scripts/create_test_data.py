"""
سكريبت إنشاء بيانات وهمية للاختبار
S-ACM - Smart Academic Content Management System
"""

import os
import sys
import django
from datetime import date, timedelta

# إعداد Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Role, Permission, RolePermission, Major, Level, Semester
from apps.courses.models import Course, CourseMajor, InstructorCourse, LectureFile

User = get_user_model()


def create_roles():
    """إنشاء الأدوار الأساسية"""
    print("إنشاء الأدوار...")
    
    roles_data = [
        {'display_name': 'مسؤول النظام', 'code': 'admin', 'description': 'صلاحيات كاملة للنظام', 'is_system': True},
        {'display_name': 'مدرس', 'code': 'instructor', 'description': 'إدارة المقررات والملفات', 'is_system': True},
        {'display_name': 'طالب', 'code': 'student', 'description': 'الوصول للمقررات والملفات', 'is_system': True},
    ]
    
    for role_data in roles_data:
        role, created = Role.objects.get_or_create(
            code=role_data['code'],
            defaults=role_data
        )
        if created:
            print(f"  ✓ تم إنشاء الدور: {role.display_name}")
        else:
            print(f"  - الدور موجود: {role.display_name}")
    
    return Role.objects.all()


def create_permissions():
    """إنشاء الصلاحيات"""
    print("\nإنشاء الصلاحيات...")
    
    permissions_data = [
        # صلاحيات المستخدمين
        {'display_name': 'عرض المستخدمين', 'code': 'view_users', 'category': 'users'},
        {'display_name': 'إنشاء مستخدم', 'code': 'create_user', 'category': 'users'},
        {'display_name': 'تعديل مستخدم', 'code': 'edit_user', 'category': 'users'},
        {'display_name': 'حذف مستخدم', 'code': 'delete_user', 'category': 'users'},
        # صلاحيات المقررات
        {'display_name': 'عرض المقررات', 'code': 'view_courses', 'category': 'courses'},
        {'display_name': 'إنشاء مقرر', 'code': 'create_course', 'category': 'courses'},
        {'display_name': 'تعديل مقرر', 'code': 'edit_course', 'category': 'courses'},
        {'display_name': 'حذف مقرر', 'code': 'delete_course', 'category': 'courses'},
        # صلاحيات الملفات
        {'display_name': 'رفع ملفات', 'code': 'upload_files', 'category': 'files'},
        {'display_name': 'تحميل ملفات', 'code': 'download_files', 'category': 'files'},
        {'display_name': 'حذف ملفات', 'code': 'delete_files', 'category': 'files'},
        # صلاحيات الذكاء الاصطناعي
        {'display_name': 'استخدام AI', 'code': 'use_ai', 'category': 'ai'},
        # صلاحيات النظام
        {'display_name': 'عرض التقارير', 'code': 'view_reports', 'category': 'system'},
        {'display_name': 'إدارة الإعدادات', 'code': 'manage_settings', 'category': 'system'},
    ]
    
    for perm_data in permissions_data:
        perm, created = Permission.objects.get_or_create(
            code=perm_data['code'],
            defaults=perm_data
        )
        if created:
            print(f"  ✓ تم إنشاء الصلاحية: {perm.display_name}")
    
    return Permission.objects.all()


def assign_permissions_to_roles():
    """تعيين الصلاحيات للأدوار"""
    print("\nتعيين الصلاحيات للأدوار...")
    
    admin_role = Role.objects.get(code='admin')
    instructor_role = Role.objects.get(code='instructor')
    student_role = Role.objects.get(code='student')
    
    # المسؤول يحصل على جميع الصلاحيات
    for perm in Permission.objects.all():
        RolePermission.objects.get_or_create(role=admin_role, permission=perm)
    print(f"  ✓ تم تعيين جميع الصلاحيات للمسؤول")
    
    # المدرس
    instructor_perms = ['view_courses', 'edit_course', 'upload_files', 'download_files', 'delete_files', 'use_ai']
    for perm_code in instructor_perms:
        perm = Permission.objects.filter(code=perm_code).first()
        if perm:
            RolePermission.objects.get_or_create(role=instructor_role, permission=perm)
    print(f"  ✓ تم تعيين صلاحيات المدرس")
    
    # الطالب
    student_perms = ['view_courses', 'download_files', 'use_ai']
    for perm_code in student_perms:
        perm = Permission.objects.filter(code=perm_code).first()
        if perm:
            RolePermission.objects.get_or_create(role=student_role, permission=perm)
    print(f"  ✓ تم تعيين صلاحيات الطالب")


def create_majors():
    """إنشاء التخصصات"""
    print("\nإنشاء التخصصات...")
    
    majors_data = [
        {'major_name': 'علوم الحاسب', 'description': 'تخصص علوم الحاسب'},
        {'major_name': 'نظم المعلومات', 'description': 'تخصص نظم المعلومات'},
        {'major_name': 'هندسة البرمجيات', 'description': 'تخصص هندسة البرمجيات'},
        {'major_name': 'الذكاء الاصطناعي', 'description': 'تخصص الذكاء الاصطناعي'},
    ]
    
    for major_data in majors_data:
        major, created = Major.objects.get_or_create(
            major_name=major_data['major_name'],
            defaults=major_data
        )
        if created:
            print(f"  ✓ تم إنشاء التخصص: {major.major_name}")
    
    return Major.objects.all()


def create_levels():
    """إنشاء المستويات"""
    print("\nإنشاء المستويات...")
    
    levels_data = [
        {'level_name': 'المستوى الأول', 'level_number': 1},
        {'level_name': 'المستوى الثاني', 'level_number': 2},
        {'level_name': 'المستوى الثالث', 'level_number': 3},
        {'level_name': 'المستوى الرابع', 'level_number': 4},
        {'level_name': 'المستوى الخامس', 'level_number': 5},
        {'level_name': 'المستوى السادس', 'level_number': 6},
        {'level_name': 'المستوى السابع', 'level_number': 7},
        {'level_name': 'المستوى الثامن', 'level_number': 8},
    ]
    
    for level_data in levels_data:
        level, created = Level.objects.get_or_create(
            level_number=level_data['level_number'],
            defaults=level_data
        )
        if created:
            print(f"  ✓ تم إنشاء المستوى: {level.level_name}")
    
    return Level.objects.all()


def create_semesters():
    """إنشاء الفصول الدراسية"""
    print("\nإنشاء الفصول الدراسية...")
    
    today = date.today()
    
    semesters_data = [
        {
            'name': 'الفصل الأول 2024-2025',
            'academic_year': '2024-2025',
            'semester_number': 1,
            'start_date': date(2024, 9, 1),
            'end_date': date(2025, 1, 15),
            'is_current': False
        },
        {
            'name': 'الفصل الثاني 2024-2025',
            'academic_year': '2024-2025',
            'semester_number': 2,
            'start_date': date(2025, 1, 20),
            'end_date': date(2025, 6, 1),
            'is_current': False
        },
        {
            'name': 'الفصل الأول 2025-2026',
            'academic_year': '2025-2026',
            'semester_number': 1,
            'start_date': date(2025, 9, 1),
            'end_date': date(2026, 1, 15),
            'is_current': True
        },
    ]
    
    for sem_data in semesters_data:
        semester, created = Semester.objects.get_or_create(
            name=sem_data['name'],
            defaults=sem_data
        )
        if created:
            print(f"  ✓ تم إنشاء الفصل: {semester.name}")
    
    return Semester.objects.all()


def create_users():
    """إنشاء المستخدمين"""
    print("\nإنشاء المستخدمين...")
    
    admin_role = Role.objects.get(code='admin')
    instructor_role = Role.objects.get(code='instructor')
    student_role = Role.objects.get(code='student')
    
    cs_major = Major.objects.get(major_name='علوم الحاسب')
    level_1 = Level.objects.get(level_number=1)
    
    users_data = [
        {
            'academic_id': 'admin001',
            'id_card_number': '1000000001',
            'email': 'admin@sacm.edu',
            'password': 'admin123',
            'full_name': 'مدير النظام',
            'role': admin_role,
            'is_staff': True,
            'is_superuser': True,
            'account_status': 'active',
        },
        {
            'academic_id': 'inst001',
            'id_card_number': '1000000002',
            'email': 'instructor1@sacm.edu',
            'password': 'inst123',
            'full_name': 'أحمد المدرس',
            'role': instructor_role,
            'account_status': 'active',
        },
        {
            'academic_id': 'inst002',
            'id_card_number': '1000000003',
            'email': 'instructor2@sacm.edu',
            'password': 'inst123',
            'full_name': 'محمد العلي',
            'role': instructor_role,
            'account_status': 'active',
        },
        {
            'academic_id': 'std001',
            'id_card_number': '1000000004',
            'email': 'student1@sacm.edu',
            'password': 'student123',
            'full_name': 'خالد الطالب',
            'role': student_role,
            'major': cs_major,
            'level': level_1,
            'account_status': 'active',
        },
        {
            'academic_id': 'std002',
            'id_card_number': '1000000005',
            'email': 'student2@sacm.edu',
            'password': 'student123',
            'full_name': 'سارة الطالبة',
            'role': student_role,
            'major': cs_major,
            'level': level_1,
            'account_status': 'active',
        },
    ]
    
    for user_data in users_data:
        password = user_data.pop('password')
        
        user, created = User.objects.get_or_create(
            academic_id=user_data['academic_id'],
            defaults=user_data
        )
        
        if created:
            user.set_password(password)
            user.save()
            print(f"  ✓ تم إنشاء المستخدم: {user.full_name} ({user.role.display_name})")
        else:
            print(f"  - المستخدم موجود: {user.full_name}")
    
    return User.objects.all()


def create_courses():
    """إنشاء المقررات"""
    print("\nإنشاء المقررات...")
    
    level_1 = Level.objects.get(level_number=1)
    level_2 = Level.objects.get(level_number=2)
    level_3 = Level.objects.get(level_number=3)
    
    current_semester = Semester.objects.get(is_current=True)
    
    cs_major = Major.objects.get(major_name='علوم الحاسب')
    is_major = Major.objects.get(major_name='نظم المعلومات')
    
    courses_data = [
        {
            'course_code': 'CS101',
            'course_name': 'مقدمة في البرمجة',
            'description': 'مقرر تأسيسي في أساسيات البرمجة باستخدام Python',
            'level': level_1,
            'semester': current_semester,
            'credit_hours': 3,
            'majors': [cs_major, is_major],
        },
        {
            'course_code': 'CS201',
            'course_name': 'هياكل البيانات',
            'description': 'دراسة هياكل البيانات الأساسية والخوارزميات',
            'level': level_2,
            'semester': current_semester,
            'credit_hours': 3,
            'majors': [cs_major],
        },
        {
            'course_code': 'CS301',
            'course_name': 'قواعد البيانات',
            'description': 'تصميم وإدارة قواعد البيانات العلائقية',
            'level': level_3,
            'semester': current_semester,
            'credit_hours': 3,
            'majors': [cs_major, is_major],
        },
        {
            'course_code': 'CS302',
            'course_name': 'هندسة البرمجيات',
            'description': 'مبادئ وممارسات هندسة البرمجيات',
            'level': level_3,
            'semester': current_semester,
            'credit_hours': 3,
            'majors': [cs_major],
        },
        {
            'course_code': 'IS201',
            'course_name': 'نظم المعلومات الإدارية',
            'description': 'مقدمة في نظم المعلومات الإدارية',
            'level': level_2,
            'semester': current_semester,
            'credit_hours': 3,
            'majors': [is_major],
        },
    ]
    
    for course_data in courses_data:
        majors = course_data.pop('majors')
        
        course, created = Course.objects.get_or_create(
            course_code=course_data['course_code'],
            defaults=course_data
        )
        
        if created:
            # إضافة التخصصات
            for major in majors:
                CourseMajor.objects.get_or_create(course=course, major=major)
            print(f"  ✓ تم إنشاء المقرر: {course.course_code} - {course.course_name}")
        else:
            print(f"  - المقرر موجود: {course.course_code}")
    
    return Course.objects.all()


def assign_instructors_to_courses():
    """تعيين المدرسين للمقررات"""
    print("\nتعيين المدرسين للمقررات...")
    
    instructor1 = User.objects.get(academic_id='inst001')
    instructor2 = User.objects.get(academic_id='inst002')
    
    # تعيين المدرسين
    assignments = [
        ('CS101', instructor1),
        ('CS201', instructor1),
        ('CS301', instructor2),
        ('CS302', instructor2),
        ('IS201', instructor1),
    ]
    
    for course_code, instructor in assignments:
        course = Course.objects.get(course_code=course_code)
        ic, created = InstructorCourse.objects.get_or_create(
            course=course,
            instructor=instructor,
        )
        if created:
            print(f"  ✓ تم تعيين {instructor.full_name} للمقرر {course_code}")


def create_lecture_files():
    """إنشاء ملفات وهمية"""
    print("\nإنشاء ملفات المحاضرات...")
    
    instructor1 = User.objects.get(academic_id='inst001')
    
    cs101 = Course.objects.get(course_code='CS101')
    cs201 = Course.objects.get(course_code='CS201')
    
    files_data = [
        {
            'course': cs101,
            'title': 'المحاضرة 1: مقدمة في البرمجة',
            'description': 'مقدمة عامة عن البرمجة ولغة Python',
            'file_type': 'Lecture',
            'content_type': 'external_link',
            'external_link': 'https://www.youtube.com/watch?v=example1',
            'uploader': instructor1,
            'is_visible': True,
        },
        {
            'course': cs101,
            'title': 'المحاضرة 2: المتغيرات وأنواع البيانات',
            'description': 'شرح المتغيرات وأنواع البيانات في Python',
            'file_type': 'Lecture',
            'content_type': 'external_link',
            'external_link': 'https://www.youtube.com/watch?v=example2',
            'uploader': instructor1,
            'is_visible': True,
        },
        {
            'course': cs101,
            'title': 'ملخص الوحدة الأولى',
            'description': 'ملخص شامل للوحدة الأولى',
            'file_type': 'Summary',
            'content_type': 'external_link',
            'external_link': 'https://drive.google.com/file/example',
            'uploader': instructor1,
            'is_visible': True,
        },
        {
            'course': cs101,
            'title': 'الواجب الأول',
            'description': 'واجب على المتغيرات وأنواع البيانات',
            'file_type': 'Assignment',
            'content_type': 'external_link',
            'external_link': 'https://drive.google.com/file/assignment1',
            'uploader': instructor1,
            'is_visible': True,
        },
        {
            'course': cs201,
            'title': 'المحاضرة 1: مقدمة في هياكل البيانات',
            'description': 'مقدمة عن هياكل البيانات وأهميتها',
            'file_type': 'Lecture',
            'content_type': 'external_link',
            'external_link': 'https://www.youtube.com/watch?v=ds1',
            'uploader': instructor1,
            'is_visible': True,
        },
    ]
    
    for file_data in files_data:
        lf, created = LectureFile.objects.get_or_create(
            course=file_data['course'],
            title=file_data['title'],
            defaults=file_data
        )
        if created:
            print(f"  ✓ تم إنشاء الملف: {lf.title}")


def main():
    """تنفيذ السكريبت الرئيسي"""
    print("=" * 60)
    print("إنشاء البيانات الوهمية لمشروع S-ACM")
    print("=" * 60)
    
    create_roles()
    create_permissions()
    assign_permissions_to_roles()
    create_majors()
    create_levels()
    create_semesters()
    create_users()
    create_courses()
    assign_instructors_to_courses()
    create_lecture_files()
    
    print("\n" + "=" * 60)
    print("✓ تم إنشاء جميع البيانات الوهمية بنجاح!")
    print("=" * 60)
    
    print("\nبيانات تسجيل الدخول:")
    print("-" * 40)
    print("المسؤول:  admin001 / admin123")
    print("المدرس 1: inst001 / inst123")
    print("المدرس 2: inst002 / inst123")
    print("الطالب 1: std001 / student123")
    print("الطالب 2: std002 / student123")


if __name__ == '__main__':
    main()
