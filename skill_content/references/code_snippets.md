# أكواد مرجعية لمشروع S-ACM

## 1. نموذج Permission المحسّن

```python
# apps/accounts/models.py

class Permission(models.Model):
    """نموذج الصلاحيات الديناميكي"""
    
    CATEGORY_CHOICES = [
        ('users', 'المستخدمون'),
        ('roles', 'الأدوار'),
        ('courses', 'المقررات'),
        ('files', 'الملفات'),
        ('notifications', 'الإشعارات'),
        ('reports', 'التقارير'),
        ('settings', 'الإعدادات'),
        ('ai', 'الذكاء الاصطناعي'),
    ]
    
    code = models.CharField(max_length=100, unique=True, verbose_name='الكود')
    display_name = models.CharField(max_length=255, verbose_name='الاسم المعروض')
    description = models.TextField(blank=True, verbose_name='الوصف')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, verbose_name='الفئة')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'صلاحية'
        verbose_name_plural = 'الصلاحيات'
        ordering = ['category', 'display_name']
    
    def __str__(self):
        return self.display_name
```

---

## 2. نموذج Role المحسّن

```python
# apps/accounts/models.py

class Role(models.Model):
    """نموذج الأدوار الديناميكي"""
    
    code = models.CharField(max_length=50, unique=True, verbose_name='الكود')
    name = models.CharField(max_length=100, verbose_name='الاسم')
    description = models.TextField(blank=True, verbose_name='الوصف')
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        verbose_name='الصلاحيات'
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    is_system = models.BooleanField(default=False, verbose_name='دور نظام')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'دور'
        verbose_name_plural = 'الأدوار'
        ordering = ['name']
    
    def __str__(self):
        return self.name
```

---

## 3. خدمة القائمة الجانبية

```python
# apps/core/services.py

class MenuService:
    """خدمة إنشاء القائمة الجانبية الديناميكية"""
    
    @staticmethod
    def get_menu_for_user(user):
        """الحصول على عناصر القائمة بناءً على صلاحيات المستخدم"""
        menu_items = []
        
        # لوحة التحكم (للجميع)
        menu_items.append({
            'code': 'dashboard',
            'label': 'لوحة التحكم',
            'icon': 'bi-speedometer2',
            'url': 'core:dashboard',
        })
        
        # المقررات
        if user.has_perm('view_my_courses') or user.has_perm('view_any_course'):
            menu_items.append({
                'code': 'courses',
                'label': 'المقررات',
                'icon': 'bi-book',
                'url': 'courses:list',
            })
        
        # إدارة المستخدمين
        if user.has_perm('view_user_list'):
            menu_items.append({
                'code': 'users',
                'label': 'المستخدمين',
                'icon': 'bi-people',
                'url': 'accounts:user_list',
            })
        
        # إدارة الأدوار
        if user.has_perm('manage_roles'):
            menu_items.append({
                'code': 'roles',
                'label': 'الأدوار والصلاحيات',
                'icon': 'bi-shield-lock',
                'url': 'accounts:roles',
            })
        
        # الإشعارات
        menu_items.append({
            'code': 'notifications',
            'label': 'الإشعارات',
            'icon': 'bi-bell',
            'url': 'notifications:list',
        })
        
        # التقارير
        if user.has_perm('view_system_reports') or user.has_perm('view_personal_reports'):
            menu_items.append({
                'code': 'reports',
                'label': 'التقارير',
                'icon': 'bi-bar-chart',
                'url': 'reports:index',
            })
        
        # الإعدادات
        if user.has_perm('manage_settings'):
            menu_items.append({
                'code': 'settings',
                'label': 'الإعدادات',
                'icon': 'bi-gear',
                'url': 'settings:index',
            })
        
        return menu_items
```

---

## 4. Context Processor للصلاحيات

```python
# apps/core/context_processors.py

def permissions_context(request):
    """Context processor لتوفير الصلاحيات وعناصر القائمة في جميع القوالب"""
    context = {}
    
    if request.user.is_authenticated:
        # الصلاحيات
        context['perms'] = {
            perm.code: True
            for perm in request.user.get_permissions()
        }
        
        # عناصر القائمة
        from apps.core.services import MenuService
        context['menu_items'] = MenuService.get_menu_for_user(request.user)
        
        # دور المستخدم
        context['user_role'] = request.user.role.name if request.user.role else 'مستخدم'
    
    return context
```

---

## 5. Mixin للتحقق من الصلاحيات

```python
# apps/core/mixins.py

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

class PermissionRequiredMixin(LoginRequiredMixin):
    """Mixin للتحقق من امتلاك المستخدم لصلاحية معينة"""
    
    permission_required = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if self.permission_required:
            if isinstance(self.permission_required, str):
                perms = [self.permission_required]
            else:
                perms = self.permission_required
            
            for perm in perms:
                if not request.user.has_perm(perm):
                    raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)
```

---

## 6. استخدام الـ Mixin في الـ Views

```python
# apps/accounts/views.py

from apps.core.mixins import PermissionRequiredMixin

class UserListView(PermissionRequiredMixin, ListView):
    """عرض قائمة المستخدمين"""
    
    model = User
    template_name = 'users/list.html'
    context_object_name = 'users'
    permission_required = 'view_user_list'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # تطبيق الفلاتر
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role__code=role)
        
        major = self.request.GET.get('major')
        if major:
            queryset = queryset.filter(major_id=major)
        
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level_id=level)
        
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(academic_id__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.select_related('role', 'major', 'level')
```

---

## 7. إعدادات Django المطلوبة

```python
# config/settings.py

# إضافة Context Processor
TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': [
                # ...
                'apps.core.context_processors.permissions_context',
            ],
        },
    },
]

# إضافة Middleware
MIDDLEWARE = [
    # ...
    'apps.core.middleware.PermissionMiddleware',
]
```
