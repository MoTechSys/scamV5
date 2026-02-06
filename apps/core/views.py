"""
Views لتطبيق core
S-ACM - Smart Academic Content Management System
"""

from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
import logging

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """الصفحة الرئيسية"""
    template_name = 'core/home.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:dashboard_redirect')
        return super().get(request, *args, **kwargs)


@login_required
def dashboard_redirect(request):
    """
    توجيه المستخدم إلى لوحة التحكم الموحدة
    Dashboard is now unified and permission-based - no role redirects needed
    """
    return redirect('core:dashboard')


class AboutView(TemplateView):
    """صفحة عن النظام"""
    template_name = 'core/about.html'


class ContactView(TemplateView):
    """صفحة التواصل"""
    template_name = 'core/contact.html'


# =============================================================================
# Custom Error Handlers
# =============================================================================

def custom_404(request, exception=None):
    """
    صفحة خطأ 404 مخصصة
    Page Not Found
    """
    logger.warning(
        f"404 Error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}"
    )
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    """
    صفحة خطأ 500 مخصصة
    Internal Server Error
    """
    logger.error(
        f"500 Error: {request.path} - User: {request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'}"
    )
    return render(request, 'errors/500.html', status=500)


def custom_403(request, exception=None):
    """
    صفحة خطأ 403 مخصصة
    Permission Denied
    """
    logger.warning(
        f"403 Error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}"
    )
    return render(request, 'errors/403.html', status=403)


def custom_400(request, exception=None):
    """
    صفحة خطأ 400 مخصصة
    Bad Request
    """
    logger.warning(
        f"400 Error: {request.path} - User: {request.user if request.user.is_authenticated else 'Anonymous'}"
    )
    return render(request, 'errors/400.html', status=400)


# =============================================================================
# Health Check Endpoint
# =============================================================================

def health_check(request):
    """
    نقطة نهاية للتحقق من صحة التطبيق
    Used by Docker, Kubernetes, and load balancers
    """
    from django.http import JsonResponse
    from django.db import connection
    
    health_status = {
        'status': 'healthy',
        'database': 'connected',
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['database'] = f'error: {str(e)}'
        logger.error(f"Health check failed - Database error: {e}")
        return JsonResponse(health_status, status=503)
    
    return JsonResponse(health_status, status=200)


# =============================================================================
# Legacy Class-Based Views (for backwards compatibility)
# =============================================================================

class Error404View(TemplateView):
    """صفحة خطأ 404"""
    template_name = 'errors/404.html'


class Error500View(TemplateView):
    """صفحة خطأ 500"""
    template_name = 'errors/500.html'


# =============================================================================
# Unified Dashboard Views
# =============================================================================

class UnifiedDashboardView(LoginRequiredMixin, TemplateView):
    """
    لوحة التحكم الموحدة - المبنية على الصلاحيات
    تعرض محتوى مختلف بناءً على صلاحيات المستخدم (has_perm) وليس دوره
    """
    template_name = 'dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # بيانات مشتركة لجميع المستخدمين
        context['current_semester'] = self._get_current_semester()
        context['recent_activities'] = self._get_recent_activities(user)
        
        # === Permission-Based Context Building ===
        context['stats'] = self._build_permission_based_stats(user)
        context['widgets'] = self._build_permission_based_widgets(user)
        context['quick_actions'] = self._build_quick_actions(user)
        context['recent_files'] = self._get_recent_files(user)
        context['my_courses'] = self._get_user_courses(user)
        
        return context
    
    def _build_permission_based_stats(self, user):
        """بناء الإحصائيات بناءً على الصلاحيات"""
        from apps.accounts.models import User
        from apps.courses.models import Course, LectureFile
        from django.utils import timezone
        from datetime import timedelta
        
        stats = {}
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Total Users - only if can view users
        if user.has_perm('accounts.view_user'):
            stats['total_users'] = User.objects.count()
            stats['active_users'] = User.objects.filter(last_login__date__gte=week_ago).count()
            stats['pending_users'] = User.objects.filter(account_status='pending').count()
        
        # All Courses - only if can view all courses
        if user.has_perm('courses.view_course'):
            stats['total_courses'] = Course.objects.count()
        
        # Total Files - only if can view all files
        if user.has_perm('courses.view_lecturefile'):
            stats['total_files'] = LectureFile.objects.count()
        
        # My Courses (for instructors/students) - always shown
        my_courses = self._get_user_courses(user)
        stats['my_courses'] = my_courses.count() if hasattr(my_courses, 'count') else len(my_courses)
        
        # My Files (for uploaders)
        if user.has_perm('courses.add_lecturefile'):
            stats['my_files'] = LectureFile.objects.filter(uploader=user).count()
        
        return stats
    
    def _build_permission_based_widgets(self, user):
        """بناء الـ widgets بناءً على الصلاحيات"""
        widgets = []
        
        # Users widget
        if user.has_perm('accounts.view_user'):
            widgets.append({
                'type': 'users',
                'title': 'إجمالي المستخدمين',
                'icon': 'bi-people',
                'color': 'primary',
            })
        
        # Courses widget
        if user.has_perm('courses.view_course'):
            widgets.append({
                'type': 'courses',
                'title': 'جميع المقررات',
                'icon': 'bi-book',
                'color': 'success',
            })
        
        # Files widget
        if user.has_perm('courses.view_lecturefile'):
            widgets.append({
                'type': 'files',
                'title': 'إجمالي الملفات',
                'icon': 'bi-file-earmark',
                'color': 'info',
            })
        
        return widgets
    
    def _build_quick_actions(self, user):
        """بناء الإجراءات السريعة بناءً على الصلاحيات"""
        actions = []
        
        # Upload file action
        if user.has_perm('courses.add_lecturefile'):
            actions.append({
                'title': 'رفع ملف',
                'url': 'courses:file_upload',
                'icon': 'bi-upload',
                'color': 'success'
            })
        
        # Add user action
        if user.has_perm('accounts.add_user'):
            actions.append({
                'title': 'إضافة مستخدم',
                'url': 'accounts:admin_user_create',
                'icon': 'bi-person-plus',
                'color': 'primary'
            })
        
        # Add course action
        if user.has_perm('courses.add_course'):
            actions.append({
                'title': 'إضافة مقرر',
                'url': 'courses:admin_course_create',
                'icon': 'bi-book',
                'color': 'success'
            })
        
        # Reports action
        if user.has_perm('reports.view_report') or user.has_perm('accounts.view_user'):
            actions.append({
                'title': 'التقارير',
                'url': 'reports:index',
                'icon': 'bi-bar-chart',
                'color': 'info'
            })
        
        # Settings action
        if user.has_perm('core.change_setting'):
            actions.append({
                'title': 'الإعدادات',
                'url': 'core:settings',
                'icon': 'bi-gear',
                'color': 'secondary'
            })
        
        # My courses (for everyone)
        actions.append({
            'title': 'مقرراتي',
            'url': 'courses:course_list',
            'icon': 'bi-book',
            'color': 'primary'
        })
        
        return actions
    
    def _get_user_courses(self, user):
        """الحصول على مقررات المستخدم"""
        from apps.courses.models import Course
        
        # If user can view all courses (admin)
        if user.has_perm('courses.view_course'):
            return Course.objects.all()[:6]
        
        # If instructor
        if hasattr(user, 'instructor_courses'):
            instructor_courses = Course.objects.filter(instructor_courses__instructor=user)
            if instructor_courses.exists():
                return instructor_courses[:6]
        
        # If student
        if hasattr(user, 'enrolled_courses'):
            return user.enrolled_courses.all()[:6]
        
        # Fallback: courses matching user's level/major
        if hasattr(user, 'level') and user.level:
            return Course.objects.filter(level=user.level)[:6]
        
        return Course.objects.none()
    
    def _get_recent_files(self, user):
        """الحصول على آخر الملفات بناءً على الصلاحيات"""
        from apps.courses.models import LectureFile
        
        # Admin: see all files
        if user.has_perm('courses.view_lecturefile'):
            return LectureFile.objects.order_by('-upload_date')[:5]
        
        # Instructor: see own uploaded files
        if user.has_perm('courses.add_lecturefile'):
            return LectureFile.objects.filter(uploader=user).order_by('-upload_date')[:5]
        
        # Student: see visible files from enrolled courses
        my_courses = self._get_user_courses(user)
        if my_courses:
            return LectureFile.objects.filter(
                course__in=my_courses,
                is_visible=True
            ).order_by('-upload_date')[:5]
        
        return []
    
    def _get_current_semester(self):
        """الحصول على الفصل الدراسي الحالي"""
        try:
            from apps.courses.models import Semester
            return Semester.objects.filter(is_current=True).first()
        except:
            return None
    
    def _get_recent_activities(self, user, limit=5):
        """الحصول على آخر النشاطات"""
        try:
            from apps.accounts.models import UserActivity
            
            if hasattr(user, 'is_admin') and user.is_admin():
                return UserActivity.objects.all().order_by('-timestamp')[:limit]
            else:
                return UserActivity.objects.filter(user=user).order_by('-timestamp')[:limit]
        except:
            return []
    
    def _get_admin_data(self):
        """بيانات لوحة تحكم المسؤول"""
        from django.utils import timezone
        from datetime import timedelta
        from apps.accounts.models import User
        from apps.courses.models import Course, LectureFile
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        return {
            'stats': {
                'total_users': User.objects.count(),
                'total_courses': Course.objects.count(),
                'total_files': LectureFile.objects.count(),
                'active_users': User.objects.filter(last_login__date__gte=week_ago).count(),
            },
            'pending_users': User.objects.filter(account_status='pending').count(),
            'recent_users': User.objects.order_by('-date_joined')[:5],
            'recent_files': LectureFile.objects.order_by('-upload_date')[:5],
            'quick_actions': [
                {'title': 'إضافة مستخدم', 'url': 'accounts:user_create', 'icon': 'bi-person-plus', 'color': 'primary'},
                {'title': 'إضافة مقرر', 'url': 'courses:course_create', 'icon': 'bi-book', 'color': 'success'},
                {'title': 'التقارير', 'url': 'reports:index', 'icon': 'bi-bar-chart', 'color': 'info'},
                {'title': 'الإعدادات', 'url': 'settings:index', 'icon': 'bi-gear', 'color': 'secondary'},
            ],
        }
    
    def _get_instructor_data(self, user):
        """بيانات لوحة تحكم المدرس"""
        from django.db.models import Count
        from apps.courses.models import Course, LectureFile
        
        my_courses = Course.objects.filter(instructor_courses__instructor=user)
        
        return {
            'stats': {
                'my_courses': my_courses.count(),
                'my_files': LectureFile.objects.filter(uploader=user).count(),
                'total_students': 0,  # يمكن حسابها لاحقاً
                'downloads_count': 0,
            },
            'my_courses': my_courses[:6],
            'recent_files': LectureFile.objects.filter(uploader=user).order_by('-upload_date')[:5],
            'quick_actions': [
                {'title': 'رفع ملف', 'url': 'courses:file_upload_select', 'icon': 'bi-upload', 'color': 'success'},
                {'title': 'مقرراتي', 'url': 'courses:my_courses', 'icon': 'bi-book', 'color': 'primary'},
            ],
        }
    
    def _get_student_data(self, user):
        """بيانات لوحة تحكم الطالب"""
        from apps.courses.models import Course, LectureFile
        
        my_courses = user.enrolled_courses.all() if hasattr(user, 'enrolled_courses') else Course.objects.none()
        
        return {
            'stats': {
                'my_courses': my_courses.count(),
                'available_files': LectureFile.objects.filter(
                    course__in=my_courses,
                    is_visible=True
                ).count() if my_courses.exists() else 0,
                'downloads_count': 0,
            },
            'my_courses': my_courses[:6],
            'recent_files': LectureFile.objects.filter(
                course__in=my_courses,
                is_visible=True
            ).order_by('-upload_date')[:5] if my_courses.exists() else [],
            'quick_actions': [
                {'title': 'مقرراتي', 'url': 'courses:my_courses', 'icon': 'bi-book', 'color': 'primary'},
                {'title': 'تلخيص ذكي', 'url': 'ai_features:summarize_select', 'icon': 'bi-stars', 'color': 'info'},
            ],
        }


@login_required
def unified_dashboard(request):
    """
    View function للوحة التحكم الموحدة
    """
    view = UnifiedDashboardView.as_view()
    return view(request)


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    صفحة الملف الشخصي
    """
    template_name = 'profile/view.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # إحصائيات المستخدم
        try:
            from apps.courses.models import Course, LectureFile
            
            if hasattr(user, 'enrolled_courses'):
                context['my_courses'] = user.enrolled_courses.all()[:6]
                context['my_courses_count'] = user.enrolled_courses.count()
            elif hasattr(user, 'is_instructor') and user.is_instructor():
                context['my_courses'] = Course.objects.filter(instructor_courses__instructor=user)[:6]
                context['my_courses_count'] = Course.objects.filter(instructor_courses__instructor=user).count()
            
            if hasattr(user, 'is_instructor') and user.is_instructor():
                context['my_files_count'] = LectureFile.objects.filter(uploader=user).count()
        except:
            pass
        
        # آخر النشاطات
        try:
            from apps.accounts.models import UserActivity
            context['my_activities'] = UserActivity.objects.filter(user=user).order_by('-timestamp')[:10]
        except:
            context['my_activities'] = []
        
        # الفصل الحالي
        try:
            from apps.courses.models import Semester
            context['current_semester'] = Semester.objects.filter(is_current=True).first()
        except:
            pass
        
        # اسم الدور
        if hasattr(user, 'role') and user.role:
            context['user_role'] = user.role.role_name
        elif hasattr(user, 'is_admin') and user.is_admin():
            context['user_role'] = 'مسؤول'
        elif hasattr(user, 'is_instructor') and user.is_instructor():
            context['user_role'] = 'مدرس'
        else:
            context['user_role'] = 'طالب'
        
        return context


@login_required
def profile_view(request):
    """View function للملف الشخصي"""
    view = ProfileView.as_view()
    return view(request)


# =============================================================================
# Admin Management Views
# =============================================================================

class UsersListView(LoginRequiredMixin, TemplateView):
    """
    صفحة قائمة المستخدمين
    """
    template_name = 'admin_panel/users/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.accounts.models import User, Role, Major, Level
        
        # جلب المستخدمين
        users = User.objects.all().select_related('role', 'major', 'level')
        
        # تطبيق الفلاتر
        q = self.request.GET.get('q')
        if q:
            users = users.filter(
                models.Q(full_name__icontains=q) |
                models.Q(academic_id__icontains=q) |
                models.Q(email__icontains=q)
            )
        
        role_id = self.request.GET.get('role')
        if role_id:
            users = users.filter(role_id=role_id)
        
        major_id = self.request.GET.get('major')
        if major_id:
            users = users.filter(major_id=major_id)
        
        status = self.request.GET.get('status')
        if status == 'active':
            users = users.filter(is_active=True)
        elif status == 'inactive':
            users = users.filter(is_active=False, is_activated=True)
        elif status == 'pending':
            users = users.filter(is_activated=False)
        
        context['users'] = users
        context['total_users'] = users.count()
        
        # إحصائيات
        context['stats'] = {
            'total': User.objects.count(),
            'students': User.objects.filter(role__role_name='طالب').count(),
            'instructors': User.objects.filter(role__role_name='مدرس').count(),
            'admins': User.objects.filter(role__role_name='مسؤول').count(),
        }
        
        # بيانات الفلاتر
        try:
            context['roles'] = Role.objects.all()
        except:
            context['roles'] = []
        
        try:
            context['majors'] = Major.objects.all()
        except:
            context['majors'] = []
        
        try:
            context['levels'] = Level.objects.all()
        except:
            context['levels'] = []
        
        return context


class RolesListView(LoginRequiredMixin, TemplateView):
    """
    صفحة قائمة الأدوار
    """
    template_name = 'admin_panel/roles/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.accounts.models import Role
            context['roles'] = Role.objects.all()
        except:
            context['roles'] = []
        return context


class ReportsView(LoginRequiredMixin, TemplateView):
    """
    صفحة التقارير
    """
    template_name = 'reports/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    """
    صفحة الإعدادات
    """
    template_name = 'settings/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class AuditLogsView(LoginRequiredMixin, TemplateView):
    """
    صفحة سجل المراجعة
    """
    template_name = 'audit_logs/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.accounts.models import UserActivity, User
            context['logs'] = UserActivity.objects.all().select_related('user').order_by('-timestamp')[:100]
            context['users'] = User.objects.all()
        except:
            context['logs'] = []
            context['users'] = []
        return context


class StatisticsView(LoginRequiredMixin, TemplateView):
    """
    صفحة الإحصائيات
    """
    template_name = 'statistics/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            from apps.accounts.models import User
            from apps.courses.models import Course, LectureFile
            
            context['stats'] = {
                'total_users': User.objects.count(),
                'active_courses': Course.objects.filter(is_active=True).count(),
                'total_files': LectureFile.objects.count(),
                'ai_operations': 0,  # يمكن حسابها لاحقاً
            }
            
            # المقررات الأكثر نشاطاً
            context['top_courses'] = Course.objects.annotate(
                files_count=models.Count('files')
            ).order_by('-files_count')[:5]
            
            # آخر النشاطات
            try:
                from apps.accounts.models import UserActivity
                context['recent_activities'] = UserActivity.objects.all().order_by('-timestamp')[:10]
            except:
                context['recent_activities'] = []
        except Exception as e:
            context['stats'] = {}
            context['top_courses'] = []
            context['recent_activities'] = []
        
        return context
