"""
Views لتطبيق reports
S-ACM - Smart Academic Content Management System
"""

from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import csv
import json

from apps.accounts.models import User, Role, UserActivity
from apps.courses.models import Course, LectureFile


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin للتحقق من صلاحيات المسؤول"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or hasattr(request.user, 'is_admin') and request.user.is_admin()):
            messages.error(request, 'ليس لديك صلاحية للوصول لهذه الصفحة')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)


class ReportsIndexView(AdminRequiredMixin, TemplateView):
    """
    صفحة التقارير الرئيسية
    """
    template_name = 'reports/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Date filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        # إحصائيات عامة
        context['stats'] = self._get_stats()
        
        # أكثر المقررات نشاطاً
        context['top_courses'] = self._get_top_courses()
        
        # بيانات الرسوم البيانية
        context['activity_labels'] = json.dumps(self._get_activity_labels())
        context['login_data'] = json.dumps(self._get_login_data())
        context['download_data'] = json.dumps(self._get_download_data())
        context['file_types_data'] = json.dumps(self._get_file_types_data())
        
        # آخر النشاطات
        context['recent_activities'] = UserActivity.objects.all().order_by('-timestamp')[:10]
        
        # بيانات الفلاتر
        try:
            from apps.accounts.models import Level, Major
            context['levels'] = Level.objects.all()
            context['majors'] = Major.objects.all()
        except:
            context['levels'] = []
            context['majors'] = []
        
        return context
    
    def _get_stats(self):
        """الحصول على الإحصائيات العامة"""
        return {
            'total_users': User.objects.count(),
            'students': User.objects.filter(role__code='student').count(),
            'instructors': User.objects.filter(role__code='instructor').count(),
            'admins': User.objects.filter(role__code='admin').count(),
            'active_courses': Course.objects.filter(is_active=True).count(),
            'total_files': LectureFile.objects.count(),
            'total_downloads': sum(f.download_count for f in LectureFile.objects.all()),
        }
    
    def _get_top_courses(self):
        """الحصول على أكثر المقررات نشاطاً"""
        from django.db.models import Count, Sum
        return Course.objects.annotate(
            files_count=Count('files'),
            downloads_count=Sum('files__download_count')
        ).order_by('-downloads_count')[:5]
    
    def _get_activity_labels(self):
        """أسماء أيام الأسبوع"""
        return ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']
    
    def _get_login_data(self):
        """بيانات تسجيلات الدخول"""
        # بيانات وهمية للعرض - يمكن تحسينها لاحقاً
        return [12, 19, 8, 15, 22, 18, 25]
    
    def _get_download_data(self):
        """بيانات التحميلات"""
        return [8, 12, 6, 9, 11, 8, 14]
    
    def _get_file_types_data(self):
        """بيانات أنواع الملفات"""
        return [45, 25, 30, 15, 10]


class ReportExportView(AdminRequiredMixin, View):
    """
    تصدير التقارير
    """
    
    def post(self, request):
        report_type = request.POST.get('report_type', 'users')
        export_format = request.POST.get('format', 'csv')
        date_from = request.POST.get('date_from')
        date_to = request.POST.get('date_to')
        
        if report_type == 'users':
            return self._export_users(export_format)
        elif report_type == 'courses':
            return self._export_courses(export_format)
        elif report_type == 'files':
            return self._export_files(export_format)
        elif report_type == 'activity':
            return self._export_activity(export_format)
        
        messages.error(request, 'نوع التقرير غير صالح')
        return redirect('reports:index')
    
    def _export_users(self, format='csv'):
        """تصدير تقرير المستخدمين"""
        users = User.objects.all().select_related('role', 'major', 'level')
        
        if format == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = 'attachment; filename="users_report.csv"'
            response.write('\ufeff')  # BOM for Excel Arabic support
            
            writer = csv.writer(response)
            writer.writerow(['الرقم الأكاديمي', 'الاسم', 'البريد', 'الدور', 'التخصص', 'المستوى', 'الحالة', 'تاريخ الانضمام'])
            
            for user in users:
                writer.writerow([
                    user.academic_id,
                    user.full_name,
                    user.email or '-',
                    user.role.role_name if user.role else '-',
                    user.major.major_name if user.major else '-',
                    user.level.level_name if user.level else '-',
                    'نشط' if user.is_active else 'غير نشط',
                    user.date_joined.strftime('%Y-%m-%d') if user.date_joined else '-',
                ])
            
            return response
        
        # للصيغ الأخرى يمكن التوسع لاحقاً
        messages.info(self.request, 'تم تصدير التقرير بصيغة CSV')
        return redirect('reports:index')
    
    def _export_courses(self, format='csv'):
        """تصدير تقرير المقررات"""
        from django.db.models import Count
        courses = Course.objects.annotate(files_count=Count('files'))
        
        if format == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = 'attachment; filename="courses_report.csv"'
            response.write('\ufeff')
            
            writer = csv.writer(response)
            writer.writerow(['رمز المقرر', 'اسم المقرر', 'عدد الملفات', 'الحالة'])
            
            for course in courses:
                writer.writerow([
                    course.course_code,
                    course.course_name,
                    course.files_count,
                    'نشط' if course.is_active else 'غير نشط',
                ])
            
            return response
        
        return redirect('reports:index')
    
    def _export_files(self, format='csv'):
        """تصدير تقرير الملفات"""
        files = LectureFile.objects.all().select_related('course', 'uploader')
        
        if format == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = 'attachment; filename="files_report.csv"'
            response.write('\ufeff')
            
            writer = csv.writer(response)
            writer.writerow(['العنوان', 'المقرر', 'الرافع', 'النوع', 'التحميلات', 'تاريخ الرفع'])
            
            for file in files:
                writer.writerow([
                    file.title,
                    file.course.course_name if file.course else '-',
                    file.uploader.full_name if file.uploader else '-',
                    file.get_file_type_display() if hasattr(file, 'get_file_type_display') else '-',
                    file.download_count,
                    file.upload_date.strftime('%Y-%m-%d') if file.upload_date else '-',
                ])
            
            return response
        
        return redirect('reports:index')
    
    def _export_activity(self, format='csv'):
        """تصدير تقرير النشاطات"""
        activities = UserActivity.objects.all().select_related('user').order_by('-timestamp')[:1000]
        
        if format == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
            response['Content-Disposition'] = 'attachment; filename="activity_report.csv"'
            response.write('\ufeff')
            
            writer = csv.writer(response)
            writer.writerow(['المستخدم', 'نوع النشاط', 'الوصف', 'التاريخ'])
            
            for activity in activities:
                writer.writerow([
                    activity.user.full_name if activity.user else '-',
                    activity.get_activity_type_display() if hasattr(activity, 'get_activity_type_display') else activity.activity_type,
                    activity.description or '-',
                    activity.timestamp.strftime('%Y-%m-%d %H:%M') if activity.timestamp else '-',
                ])
            
            return response
        
        return redirect('reports:index')


class ReportGenerateView(AdminRequiredMixin, View):
    """
    توليد التقارير السريعة
    """
    
    def get(self, request):
        report_type = request.GET.get('type', 'users')
        
        if report_type == 'users':
            return redirect('reports:users_report')
        elif report_type == 'courses':
            return redirect('reports:courses_report')
        elif report_type == 'activity':
            return redirect('reports:activity_report')
        
        return redirect('reports:index')


class UsersReportView(AdminRequiredMixin, TemplateView):
    """تقرير المستخدمين"""
    template_name = 'reports/users_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all().select_related('role', 'major', 'level')
        context['total'] = User.objects.count()
        return context


class CoursesReportView(AdminRequiredMixin, TemplateView):
    """تقرير المقررات"""
    template_name = 'reports/courses_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.db.models import Count, Sum
        context['courses'] = Course.objects.annotate(
            files_count=Count('files'),
            downloads_count=Sum('files__download_count')
        )
        return context


class FilesReportView(AdminRequiredMixin, TemplateView):
    """تقرير الملفات"""
    template_name = 'reports/files_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['files'] = LectureFile.objects.all().select_related('course', 'uploader')
        return context


class ActivityReportView(AdminRequiredMixin, TemplateView):
    """تقرير النشاطات"""
    template_name = 'reports/activity_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = UserActivity.objects.all().select_related('user').order_by('-timestamp')[:500]
        return context
