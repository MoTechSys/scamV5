"""
UniCore-style Atomic Permissions Seeder
S-ACM - Smart Academic Content Management System

This command seeds granular permissions that enable dynamic UI based on
django.contrib.auth.models.Permission rather than hardcoded role checks.

Usage:
    python manage.py seed_permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Seeds UniCore-style atomic permissions for dynamic UI'

    def handle(self, *args, **options):
        self.stdout.write('Seeding UniCore permissions...\n')
        
        # Get ContentTypes for each model
        from apps.courses.models import Course, LectureFile
        from apps.accounts.models import User
        
        course_ct = ContentType.objects.get_for_model(Course)
        file_ct = ContentType.objects.get_for_model(LectureFile)
        user_ct = ContentType.objects.get_for_model(User)
        
        # Granular Permission Definitions
        permissions = [
            # === Course Management ===
            (course_ct, 'view_analytics', 'Can view course analytics'),
            (course_ct, 'archive_course', 'Can archive/unarchive courses'),
            (course_ct, 'assign_instructor', 'Can assign instructors to courses'),
            (course_ct, 'manage_enrollments', 'Can manage student enrollments'),
            
            # === File Management ===
            (file_ct, 'download_restricted', 'Can download restricted files'),
            (file_ct, 'bulk_upload', 'Can perform bulk file uploads'),
            (file_ct, 'manage_visibility', 'Can toggle file visibility'),
            
            # === Reports & Analytics ===
            (course_ct, 'export_data', 'Can export data to CSV/Excel'),
            (course_ct, 'view_reports', 'Can access reports dashboard'),
            (course_ct, 'view_audit_logs', 'Can view system audit logs'),
            
            # === AI Features ===
            (file_ct, 'use_ai_summary', 'Can use AI summarization'),
            (file_ct, 'use_ai_questions', 'Can generate AI questions'),
            (file_ct, 'use_premium_ai', 'Can use advanced AI models (GPT-4, Gemini Pro)'),
            
            # === User Management ===
            (user_ct, 'promote_students', 'Can promote students to next level'),
            (user_ct, 'bulk_import', 'Can bulk import users from CSV'),
            (user_ct, 'view_statistics', 'Can view user statistics'),
            
            # === System Administration ===
            (course_ct, 'manage_semesters', 'Can manage academic semesters'),
            (course_ct, 'system_settings', 'Can modify system settings'),
        ]
        
        created_count = 0
        existing_count = 0
        
        for content_type, codename, name in permissions:
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created: {codename}')
            else:
                existing_count += 1
                self.stdout.write(f'  → Exists: {codename}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Successfully seeded UniCore permissions: {created_count} created, {existing_count} already existed'
        ))
        
        # Display summary by category
        self.stdout.write('')
        self.stdout.write('Permission Categories:')
        self.stdout.write('  • Course Management: view_analytics, archive_course, assign_instructor, manage_enrollments')
        self.stdout.write('  • File Management: download_restricted, bulk_upload, manage_visibility')
        self.stdout.write('  • Reports: export_data, view_reports, view_audit_logs')
        self.stdout.write('  • AI Features: use_ai_summary, use_ai_questions, use_premium_ai')
        self.stdout.write('  • User Management: promote_students, bulk_import, view_statistics')
        self.stdout.write('  • System: manage_semesters, system_settings')
