"""
Admin Views - عروض لوحة تحكم المسؤول
S-ACM - Smart Academic Content Management System

هذا الملف يحتوي على Views لوحة تحكم الأدمن:
- لوحة التحكم الرئيسية (Dashboard)
- إدارة المستخدمين (CRUD)
- استيراد المستخدمين بالجملة
- ترقية الطلاب
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db import models
import csv
import io

from .mixins import AdminRequiredMixin
from ..models import User, Role, Major, Level, Semester, UserActivity
from ..forms import UserCreateForm, UserBulkImportForm, StudentPromotionForm, AdminUserEditForm
from apps.core.models import AuditLog


class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """
    لوحة تحكم الأدمن الرئيسية.
    
    تعرض إحصائيات عامة عن النظام:
    - عدد المستخدمين
    - عدد الطلاب والمدرسين
    - الفصل الدراسي الحالي
    - آخر النشاطات
    """
    template_name = 'admin_panel/dashboard.html'
    
    def get_context_data(self, **kwargs):
        """إضافة الإحصائيات للسياق."""
        context = super().get_context_data(**kwargs)
        from ..models import Role
        
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(account_status='active').count()
        context['total_students'] = User.objects.filter(role__code=Role.STUDENT).count()
        context['total_instructors'] = User.objects.filter(role__code=Role.INSTRUCTOR).count()
        context['total_majors'] = Major.objects.filter(is_active=True).count()
        context['current_semester'] = Semester.objects.filter(is_current=True).first()
        context['recent_activities'] = UserActivity.objects.select_related('user').order_by('-activity_time')[:20]
        return context


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    قائمة المستخدمين مع الفلترة والبحث.
    
    الفلترة المتاحة:
        - حسب الدور (Student, Instructor, Admin)
        - حسب التخصص
        - حسب المستوى
        - حسب حالة الحساب
        - البحث بالاسم/الرقم الأكاديمي/البريد
    """
    model = User
    template_name = 'admin_panel/users/list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        """بناء الاستعلام مع الفلترة."""
        queryset = User.objects.select_related('role', 'major', 'level')
        
        # تطبيق الفلاتر
        role = self.request.GET.get('role')
        major = self.request.GET.get('major')
        level = self.request.GET.get('level')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        if role:
            queryset = queryset.filter(role_id=role)
        if major:
            queryset = queryset.filter(major_id=major)
        if level:
            queryset = queryset.filter(level_id=level)
        if status:
            queryset = queryset.filter(account_status=status)
        if search:
            queryset = queryset.filter(
                models.Q(academic_id__icontains=search) |
                models.Q(full_name__icontains=search) |
                models.Q(email__icontains=search)
            )
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        """إضافة خيارات الفلترة للسياق."""
        context = super().get_context_data(**kwargs)
        context['roles'] = Role.objects.all()
        context['majors'] = Major.objects.filter(is_active=True)
        context['levels'] = Level.objects.all()
        return context


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """
    إنشاء مستخدم جديد.
    
    يُستخدم لإضافة مستخدم واحد يدوياً من لوحة التحكم.
    للإضافة الجماعية، استخدم UserBulkImportView.
    """
    model = User
    form_class = UserCreateForm
    template_name = 'admin_panel/users/create.html'
    success_url = reverse_lazy('accounts:admin_user_list')
    
    def form_valid(self, form):
        """حفظ المستخدم وتسجيل العملية."""
        response = super().form_valid(form)
        
        AuditLog.log(
            user=self.request.user,
            action='create',
            model_name='User',
            object_id=self.object.id,
            object_repr=str(self.object),
            request=self.request
        )
        
        messages.success(self.request, f'تم إنشاء المستخدم {self.object.full_name} بنجاح.')
        return response


class UserBulkImportView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    استيراد المستخدمين بالجملة من ملف CSV.
    
    الشكل المتوقع للملف:
        academic_id, id_card_number, full_name, email, role, major, level
    
    الميزات:
        - التحقق من التكرار
        - معالجة الأخطاء سطراً بسطر
        - استخدام bulk_create للأداء المحسّن
        - تخطي المستخدمين الموجودين
    """
    template_name = 'admin_panel/users/import.html'
    
    def get(self, request):
        """عرض نموذج رفع الملف."""
        form = UserBulkImportForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        """معالجة ملف CSV وإنشاء المستخدمين."""
        form = UserBulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded_file))
            
            # تحميل البيانات المرجعية مسبقاً (Caching)
            # دعم البحث بالكود أو اسم العرض
            roles_cache = {}
            for r in Role.objects.all():
                roles_cache[r.code] = r
                roles_cache[r.code.lower()] = r
                roles_cache[r.display_name] = r
            
            majors_cache = {m.major_name: m for m in Major.objects.all()}
            levels_cache = {l.level_name: l for l in Level.objects.all()}
            
            # للتحقق من التكرار
            existing_academic_ids = set(User.objects.values_list('academic_id', flat=True))
            existing_id_cards = set(User.objects.values_list('id_card_number', flat=True))
            
            users_to_create = []
            errors = []
            skipped_count = 0
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    academic_id = row.get('academic_id', '').strip()
                    id_card_number = row.get('id_card_number', '').strip()
                    
                    # التحقق من الحقول المطلوبة
                    if not academic_id or not id_card_number:
                        errors.append(f'السطر {row_num}: الرقم الأكاديمي أو رقم الهوية فارغ')
                        continue
                    
                    # التحقق من التكرار
                    if academic_id in existing_academic_ids:
                        skipped_count += 1
                        continue
                    if id_card_number in existing_id_cards:
                        errors.append(f'السطر {row_num}: رقم الهوية {id_card_number} موجود مسبقاً')
                        continue
                    
                    # الحصول على البيانات المرجعية
                    role_name = row.get('role', 'student').strip()
                    role = roles_cache.get(role_name) or roles_cache.get(role_name.lower())
                    if not role:
                        errors.append(f'السطر {row_num}: الدور "{role_name}" غير موجود. الأدوار المتاحة: student, instructor, admin')
                        continue
                    
                    major = None
                    if row.get('major'):
                        major = majors_cache.get(row['major'].strip())
                        if not major:
                            errors.append(f'السطر {row_num}: التخصص "{row["major"]}" غير موجود')
                            continue
                    
                    level = None
                    if row.get('level'):
                        level = levels_cache.get(row['level'].strip())
                        if not level:
                            errors.append(f'السطر {row_num}: المستوى "{row["level"]}" غير موجود')
                            continue
                    
                    # إنشاء كائن User (بدون حفظ)
                    user = User(
                        academic_id=academic_id,
                        id_card_number=id_card_number,
                        full_name=row.get('full_name', '').strip(),
                        email=row.get('email', '').strip() or None,
                        role=role,
                        major=major,
                        level=level,
                        account_status='inactive'  # يحتاج تفعيل
                    )
                    users_to_create.append(user)
                    
                    # منع التكرار داخل نفس الملف
                    existing_academic_ids.add(academic_id)
                    existing_id_cards.add(id_card_number)
                    
                except Exception as e:
                    errors.append(f'خطأ في السطر {row_num}: {str(e)}')
            
            # الإنشاء الجماعي المحسّن
            created_count = 0
            if users_to_create:
                batch_size = 100
                for i in range(0, len(users_to_create), batch_size):
                    batch = users_to_create[i:i + batch_size]
                    User.objects.bulk_create(batch, ignore_conflicts=True)
                created_count = len(users_to_create)
            
            # تسجيل العملية
            AuditLog.log(
                user=request.user,
                action='import',
                model_name='User',
                changes={
                    'created': created_count,
                    'skipped': skipped_count,
                    'errors': len(errors)
                },
                request=request
            )
            
            # رسائل النتيجة
            if created_count > 0:
                messages.success(request, f'تم استيراد {created_count} مستخدم بنجاح.')
            if skipped_count > 0:
                messages.info(request, f'تم تخطي {skipped_count} مستخدم (موجودين مسبقاً).')
            if errors:
                for error in errors[:5]:
                    messages.warning(request, error)
                if len(errors) > 5:
                    messages.warning(request, f'... و{len(errors) - 5} أخطاء أخرى')
            
            return redirect('accounts:admin_user_list')
        
        return render(request, self.template_name, {'form': form})


class StudentPromotionView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    ترقية الطلاب الجماعية من مستوى لآخر.
    
    الميزات:
        - ترقية حسب المستوى والتخصص
        - معالجة خاصة للمستوى 8 (تخريج)
        - تسجيل العملية في سجل التدقيق
    
    ملاحظة:
        طلاب المستوى 8 يتم تحويلهم إلى حالة "graduated"
        بدلاً من ترقيتهم.
    """
    template_name = 'admin_panel/users/promote.html'
    
    def get(self, request):
        """عرض نموذج الترقية مع الإحصائيات."""
        form = StudentPromotionForm()
        context = {
            'form': form,
            'levels': Level.objects.all().order_by('level_number'),
            'majors': Major.objects.filter(is_active=True),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """معالجة ترقية الطلاب."""
        form = StudentPromotionForm(request.POST)
        if form.is_valid():
            from_level = form.cleaned_data['from_level']
            to_level = form.cleaned_data['to_level']
            major = form.cleaned_data.get('major')
            
            # بناء الاستعلام
            students = User.objects.filter(
                role__code=Role.STUDENT,
                level=from_level,
                account_status='active'
            )
            
            if major:
                students = students.filter(major=major)
            
            # معالجة خاصة للمستوى 8 (الخريجين)
            if from_level.level_number == 8:
                count = students.update(
                    account_status='graduated',
                    level=None
                )
                action_description = f'تم تخريج {count} طالب من {from_level} (تحويلهم إلى خريجين).'
                changes_log = {
                    'action': 'graduation',
                    'from_level': str(from_level),
                    'new_status': 'graduated',
                    'major': str(major) if major else 'all',
                    'count': count
                }
            else:
                # الترقية العادية
                count = students.update(level=to_level)
                action_description = f'تم ترقية {count} طالب من {from_level} إلى {to_level}.'
                changes_log = {
                    'action': 'promotion',
                    'from_level': str(from_level),
                    'to_level': str(to_level),
                    'major': str(major) if major else 'all',
                    'count': count
                }
            
            # تسجيل العملية
            AuditLog.log(
                user=request.user,
                action='promote',
                model_name='User',
                changes=changes_log,
                request=request
            )
            
            messages.success(request, action_description)
            return redirect('accounts:admin_user_list')
        
        return render(request, self.template_name, {'form': form})


class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    عرض تفاصيل المستخدم.
    
    يعرض معلومات شاملة عن المستخدم حسب دوره:
    - للطلاب: عدد التحميلات
    - للمدرسين: عدد الملفات المرفوعة والمقررات المعينة
    """
    template_name = 'admin_panel/users/detail.html'
    
    def get(self, request, pk):
        """عرض تفاصيل المستخدم."""
        user = get_object_or_404(User, pk=pk)
        
        context = {
            'viewed_user': user,
            'activities': UserActivity.objects.filter(user=user).order_by('-activity_time')[:20],
        }
        
        # إحصائيات إضافية حسب الدور
        if user.is_student():
            context['download_count'] = UserActivity.objects.filter(
                user=user, activity_type='download'
            ).count()
        elif user.is_instructor():
            from apps.courses.models import LectureFile, InstructorCourse
            context['uploaded_files'] = LectureFile.objects.filter(
                uploader=user, is_deleted=False
            ).count()
            context['assigned_courses'] = InstructorCourse.objects.filter(
                instructor=user
            ).select_related('course')
        
        return render(request, self.template_name, context)


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """
    تحديث بيانات المستخدم بواسطة الأدمن.
    
    يُستخدم لتعديل بيانات أي مستخدم من لوحة التحكم.
    يتيح للمدير الأعلى التحكم الكامل في:
    - البيانات الأساسية
    - حالة الحساب (تفعيل/إيقاف)
    - تغيير كلمة المرور
    - الدور والصلاحيات
    """
    model = User
    form_class = AdminUserEditForm
    template_name = 'admin_panel/users/edit.html'
    success_url = reverse_lazy('accounts:admin_user_list')
    
    def form_valid(self, form):
        """حفظ التغييرات وتسجيل العملية."""
        response = super().form_valid(form)
        
        AuditLog.log(
            user=self.request.user,
            action='update',
            model_name='User',
            object_id=self.object.id,
            object_repr=str(self.object),
            request=self.request
        )
        
        messages.success(self.request, f'تم تحديث بيانات المستخدم {self.object.full_name} بنجاح.')
        return response


class UserSuspendView(LoginRequiredMixin, AdminRequiredMixin, View):
    """إيقاف حساب مستخدم."""
    
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.account_status = 'suspended'
        user.save()
        
        AuditLog.log(
            user=request.user,
            action='suspend',
            model_name='User',
            object_id=user.id,
            object_repr=str(user),
            request=request
        )
        
        messages.warning(request, f'تم إيقاف حساب {user.full_name}.')
        return redirect('accounts:admin_user_list')


class UserActivateView(LoginRequiredMixin, AdminRequiredMixin, View):
    """تفعيل حساب مستخدم موقوف."""
    
    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.account_status = 'active'
        user.save()
        
        AuditLog.log(
            user=request.user,
            action='activate',
            model_name='User',
            object_id=user.id,
            object_repr=str(user),
            request=request
        )
        
        messages.success(request, f'تم تفعيل حساب {user.full_name}.')
        return redirect('accounts:admin_user_list')


# ========== Role Management Views ==========

class RoleListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    قائمة الأدوار مع إمكانية إنشاء أدوار جديدة.
    """
    model = Role
    template_name = 'admin_panel/roles/list.html'
    context_object_name = 'roles'
    
    def get_queryset(self):
        return Role.objects.annotate(
            users_count=models.Count('users')
        ).order_by('-is_system', 'display_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ..models import Permission
        context['total_permissions'] = Permission.objects.filter(is_active=True).count()
        return context


class RoleCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """
    إنشاء دور جديد.
    """
    model = Role
    fields = ['code', 'display_name', 'description']
    template_name = 'admin_panel/roles/form.html'
    success_url = reverse_lazy('accounts:admin_roles')
    
    def form_valid(self, form):
        form.instance.is_system = False  # الأدوار المخصصة ليست نظامية
        response = super().form_valid(form)
        
        AuditLog.log(
            user=self.request.user,
            action='create',
            model_name='Role',
            object_id=self.object.id,
            object_repr=str(self.object),
            request=self.request
        )
        
        messages.success(self.request, f'تم إنشاء الدور "{self.object.display_name}" بنجاح.')
        return response


class RoleUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """
    تعديل دور موجود.
    """
    model = Role
    fields = ['display_name', 'description', 'is_active']
    template_name = 'admin_panel/roles/form.html'
    success_url = reverse_lazy('accounts:admin_roles')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        AuditLog.log(
            user=self.request.user,
            action='update',
            model_name='Role',
            object_id=self.object.id,
            object_repr=str(self.object),
            request=self.request
        )
        
        messages.success(self.request, f'تم تحديث الدور "{self.object.display_name}" بنجاح.')
        return response


class RolePermissionsView(LoginRequiredMixin, AdminRequiredMixin, View):
    """
    إدارة صلاحيات الدور - تعيين/إزالة الصلاحيات.
    """
    template_name = 'admin_panel/roles/permissions.html'
    
    def get(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        from ..models import Permission, RolePermission
        
        # جميع الصلاحيات مجمعة حسب الفئة
        all_permissions = Permission.objects.filter(is_active=True).order_by('category', 'display_name')
        
        # الصلاحيات المعيّنة لهذا الدور
        assigned_perm_ids = set(
            RolePermission.objects.filter(role=role).values_list('permission_id', flat=True)
        )
        
        # تجميع الصلاحيات حسب الفئة
        permissions_by_category = {}
        for perm in all_permissions:
            cat = perm.get_category_display()
            if cat not in permissions_by_category:
                permissions_by_category[cat] = []
            permissions_by_category[cat].append({
                'permission': perm,
                'is_assigned': perm.id in assigned_perm_ids
            })
        
        return render(request, self.template_name, {
            'role': role,
            'permissions_by_category': permissions_by_category,
        })
    
    def post(self, request, pk):
        role = get_object_or_404(Role, pk=pk)
        from ..models import Permission, RolePermission
        
        # الحصول على الصلاحيات المحددة
        selected_perm_ids = request.POST.getlist('permissions')
        
        # حذف جميع الصلاحيات الحالية
        RolePermission.objects.filter(role=role).delete()
        
        # إضافة الصلاحيات الجديدة
        new_permissions = []
        for perm_id in selected_perm_ids:
            new_permissions.append(RolePermission(role=role, permission_id=int(perm_id)))
        
        if new_permissions:
            RolePermission.objects.bulk_create(new_permissions)
        
        # تسجيل العملية
        AuditLog.log(
            user=request.user,
            action='update',
            model_name='RolePermission',
            object_id=role.id,
            object_repr=f'صلاحيات {role.display_name}',
            changes={'permissions_count': len(selected_perm_ids)},
            request=request
        )
        
        messages.success(request, f'تم تحديث صلاحيات الدور "{role.display_name}" بنجاح.')
        return redirect('accounts:admin_roles')


# ========== Permission Management Views ==========

class PermissionListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """
    قائمة جميع الصلاحيات مجمعة حسب الفئة.
    """
    template_name = 'admin_panel/permissions/list.html'
    context_object_name = 'permissions'
    
    def get_queryset(self):
        from ..models import Permission
        return Permission.objects.order_by('category', 'display_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from ..models import Permission
        
        # تجميع حسب الفئة
        permissions_by_category = {}
        for perm in context['permissions']:
            cat = perm.get_category_display()
            if cat not in permissions_by_category:
                permissions_by_category[cat] = []
            permissions_by_category[cat].append(perm)
        
        context['permissions_by_category'] = permissions_by_category
        return context

