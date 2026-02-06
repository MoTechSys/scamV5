# دليل التنفيذ التفصيلي لإعادة هيكلة S-ACM

## المرحلة 1: توحيد القوالب الأساسية

### الخطوة 1.1: تحديث `base.html`
- **الهدف**: جعله مخصصاً للصفحات العامة فقط (تسجيل دخول، تفعيل، أخطاء).
- **الإجراءات**:
  - إزالة منطق الأدوار الثابت (`{% if user.is_admin %}`, `{% if user.is_instructor %}`).
  - تبسيط الـ Navbar ليعرض فقط: الشعار، تسجيل الدخول، تفعيل الحساب.

### الخطوة 1.2: تحديث `layouts/dashboard_base.html`
- **الهدف**: جعله القالب الموحد لجميع لوحات التحكم.
- **الإجراءات**:
  - التأكد من أن الـ Sidebar يعمل بشكل ديناميكي.
  - إضافة Blocks إضافية للمرونة: `{% block page_actions %}`, `{% block breadcrumb %}`.

### الخطوة 1.3: إنشاء المكونات الأساسية
- **الملفات المطلوبة**:
  - `components/stat_card.html` ✓
  - `components/course_card.html` ✓
  - `components/page_header.html` ✓
  - `components/empty_state.html` ✓

---

## المرحلة 2: إعادة بناء لوحات التحكم

### الخطوة 2.1: إنشاء `dashboard/index.html` الموحد
- **الهدف**: لوحة تحكم واحدة تعرض محتوى ديناميكي حسب الصلاحيات.
- **المحتوى**: انظر القالب في `templates/dashboard/index.html` ✓

### الخطوة 2.2: تحديث الـ View
- **الملف**: `apps/core/views.py` أو `apps/accounts/views.py`
- **الكود المقترح**:

```python
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class UnifiedDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # إحصائيات النظام (للمسؤولين)
        if user.has_perm('view_system_stats'):
            context['total_users'] = User.objects.count()
            context['active_users'] = User.objects.filter(is_active=True).count()
            context['total_students'] = User.objects.filter(role__code='student').count()
            context['total_instructors'] = User.objects.filter(role__code='instructor').count()
            context['recent_activities'] = ActivityLog.objects.order_by('-activity_time')[:10]
        
        # إحصائيات شخصية
        if user.has_perm('view_my_stats'):
            context['my_courses_count'] = user.get_courses().count()
            context['my_files_count'] = CourseFile.objects.filter(uploaded_by=user).count()
        
        # المقررات
        if user.has_perm('view_my_courses'):
            context['my_courses'] = user.get_courses()
        
        return context
```

### الخطوة 2.3: تحديث الـ URLs
- **الملف**: `config/urls.py`
- **الكود المقترح**:

```python
from apps.core.views import UnifiedDashboardView

urlpatterns = [
    # ...
    path('dashboard/', UnifiedDashboardView.as_view(), name='dashboard'),
    # ...
]
```

---

## المرحلة 3: إعادة بناء صفحات المقررات

### الخطوة 3.1: إنشاء `courses/list.html` الموحد
- **الهدف**: صفحة واحدة لعرض المقررات لجميع الأدوار.
- **المحتوى الديناميكي**:
  - **للطالب**: عرض مقرراته المسجلة.
  - **للمدرس**: عرض المقررات المعينة له مع أزرار الإدارة.
  - **للمسؤول**: عرض جميع المقررات مع أزرار الإضافة والتعديل والحذف.

### الخطوة 3.2: إنشاء `courses/detail.html` الموحد
- **الهدف**: صفحة تفاصيل المقرر موحدة.
- **المحتوى الديناميكي**:
  - **للطالب**: عرض الملفات + ميزات AI.
  - **للمدرس**: عرض الملفات + زر رفع ملف + إدارة الملفات.
  - **للمسؤول**: كل ما سبق + تعديل بيانات المقرر.

---

## المرحلة 4: إعادة بناء صفحات الإدارة

### الخطوة 4.1: تحديث `users/list.html`
- **الإجراءات**:
  - إضافة فلاتر البحث (الدور، التخصص، المستوى، الحالة).
  - إضافة أزرار الإجراءات (تعديل، حذف، ترقية).
  - استخدام `dashboard_base.html`.

### الخطوة 4.2: تحديث `roles/list.html` و `roles/permissions.html`
- **الإجراءات**:
  - عرض جدول الأدوار مع الصلاحيات كـ Checkboxes.
  - إضافة زر "إضافة دور جديد".
  - استخدام `dashboard_base.html`.

---

## المرحلة 5: ربط الواجهات بالـ Backend

### الخطوة 5.1: تحديث نموذج User
- **الملف**: `apps/accounts/models.py`
- **الكود المقترح**:

```python
class User(AbstractBaseUser, PermissionsMixin):
    # ... الحقول الموجودة ...
    
    def has_perm(self, perm_code):
        """التحقق من امتلاك المستخدم لصلاحية معينة"""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.permissions.filter(code=perm_code, is_active=True).exists()
    
    def get_permissions(self):
        """الحصول على جميع صلاحيات المستخدم"""
        if self.is_superuser:
            return Permission.objects.filter(is_active=True)
        if not self.role:
            return Permission.objects.none()
        return self.role.permissions.filter(is_active=True)
    
    def get_courses(self):
        """الحصول على مقررات المستخدم حسب دوره"""
        if self.has_perm('view_any_course'):
            return Course.objects.all()
        elif self.has_perm('view_assigned_courses'):
            return self.assigned_courses.all()
        elif self.has_perm('view_enrolled_courses'):
            return Course.objects.filter(level=self.level, majors=self.major)
        return Course.objects.none()
```

### الخطوة 5.2: إنشاء Middleware للصلاحيات
- **الملف**: `apps/core/middleware.py`
- **الكود المقترح**:

```python
from apps.core.services import MenuService

class PermissionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # تحميل الصلاحيات
            request.user_permissions = set(
                request.user.get_permissions().values_list('code', flat=True)
            )
            # تحميل عناصر القائمة
            request.menu_items = MenuService.get_menu_for_user(request.user)
        
        response = self.get_response(request)
        return response
```

### الخطوة 5.3: إنشاء Template Tags
- **الملف**: `apps/core/templatetags/permissions.py`
- **الكود المقترح**:

```python
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def has_perm(context, perm_code):
    """التحقق من امتلاك المستخدم لصلاحية معينة"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    return perm_code in getattr(request, 'user_permissions', set())
```

---

## ملخص الملفات المطلوب إنشاؤها/تعديلها

| الملف | الإجراء | الأولوية |
|---|---|---|
| `base.html` | تعديل | عالية |
| `layouts/dashboard_base.html` | تعديل | عالية |
| `components/stat_card.html` | إنشاء ✓ | عالية |
| `components/course_card.html` | إنشاء ✓ | عالية |
| `components/page_header.html` | إنشاء ✓ | عالية |
| `components/empty_state.html` | إنشاء ✓ | عالية |
| `dashboard/index.html` | إنشاء ✓ | عالية |
| `courses/list.html` | إعادة بناء | عالية |
| `courses/detail.html` | إعادة بناء | عالية |
| `apps/accounts/models.py` | تعديل | عالية |
| `apps/core/middleware.py` | إنشاء | عالية |
| `apps/core/templatetags/permissions.py` | تعديل | عالية |
