"""
Template Tags للصلاحيات والقائمة الديناميكية
S-ACM - Smart Academic Content Management System

Usage in templates:
    {% load permissions %}
    
    {% has_perm 'manage_files' %}
        <button>رفع ملف</button>
    {% endhas_perm %}
    
    {% if request.user|has_permission:'view_courses' %}
        ...
    {% endif %}
"""

from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()


@register.simple_tag(takes_context=True)
def has_perm(context, permission_code):
    """
    التحقق مما إذا كان المستخدم يمتلك صلاحية معينة
    
    Usage:
        {% has_perm 'manage_files' as can_manage %}
        {% if can_manage %}...{% endif %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    user_permissions = getattr(request, 'user_permissions', set())
    
    # الأدمن له كل الصلاحيات
    if '__all__' in user_permissions:
        return True
    
    return permission_code in user_permissions


@register.filter
def has_permission(user, permission_code):
    """
    فلتر للتحقق من صلاحية المستخدم
    
    Usage:
        {% if request.user|has_permission:'view_courses' %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    
    return user.has_perm(permission_code)


@register.inclusion_tag('components/sidebar.html', takes_context=True)
def render_sidebar(context):
    """
    رندر القائمة الجانبية الديناميكية
    
    Usage:
        {% render_sidebar %}
    """
    request = context.get('request')
    menu_items = context.get('menu_items', [])
    
    # تحديد العنصر الحالي
    current_path = request.path if request else ''
    current_item = None
    
    for item in menu_items:
        if item.url_name:
            try:
                if current_path.startswith(reverse(item.url_name)):
                    current_item = item.code
                    break
            except NoReverseMatch:
                pass
        
        for child in getattr(item, 'children', []):
            if child.url_name:
                try:
                    if current_path.startswith(reverse(child.url_name)):
                        current_item = child.code
                        break
                except NoReverseMatch:
                    pass
    
    return {
        'menu_items': menu_items,
        'current_item': current_item,
        'request': request,
    }


@register.simple_tag
def menu_item_url(item):
    """
    الحصول على URL عنصر القائمة
    
    Usage:
        {% menu_item_url item as url %}
    """
    if not item.url_name:
        return '#'
    try:
        return reverse(item.url_name)
    except NoReverseMatch:
        return '#'


@register.simple_tag(takes_context=True)
def is_active_menu(context, item_code):
    """
    التحقق مما إذا كان العنصر نشطاً
    
    Usage:
        {% is_active_menu 'dashboard' as is_active %}
    """
    request = context.get('request')
    if not request:
        return False
    
    from apps.core.menu import get_current_menu_item
    menu_items = context.get('menu_items', [])
    current = get_current_menu_item(request, menu_items)
    
    return current == item_code


@register.filter
def get_item_attr(item, attr_name):
    """
    الحصول على خاصية من عنصر القائمة
    
    Usage:
        {{ item|get_item_attr:'icon' }}
    """
    return getattr(item, attr_name, '')


@register.filter
def is_admin(user):
    """
    التحقق من كون المستخدم مسؤول
    
    Usage:
        {% if request.user|is_admin %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    return hasattr(user, 'is_admin') and user.is_admin


@register.filter
def is_instructor(user):
    """
    التحقق من كون المستخدم مدرس
    
    Usage:
        {% if request.user|is_instructor %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    return hasattr(user, 'is_instructor') and user.is_instructor


@register.filter
def is_student(user):
    """
    التحقق من كون المستخدم طالب
    
    Usage:
        {% if request.user|is_student %}...{% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    return hasattr(user, 'is_student') and user.is_student


@register.simple_tag(takes_context=True)
def has_any_permission(context, *permission_codes):
    """
    التحقق من وجود أي صلاحية من قائمة صلاحيات
    
    Usage:
        {% has_any_permission 'edit_course' 'delete_course' as can_manage %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    user_permissions = getattr(request, 'user_permissions', set())
    
    if '__all__' in user_permissions:
        return True
    
    return bool(set(permission_codes).intersection(user_permissions))


@register.simple_tag(takes_context=True)
def get_user_role_name(context):
    """
    الحصول على اسم دور المستخدم الحالي
    
    Usage:
        {% get_user_role_name as role_name %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return ''
    
    user = request.user
    if hasattr(user, 'role') and user.role:
        return user.role.role_name
    
    if hasattr(user, 'is_admin') and user.is_admin:
        return 'مسؤول'
    elif hasattr(user, 'is_instructor') and user.is_instructor:
        return 'مدرس'
    elif hasattr(user, 'is_student') and user.is_student:
        return 'طالب'
    
    return 'مستخدم'


@register.simple_tag(takes_context=True)
def get_user_role_color(context):
    """
    الحصول على لون دور المستخدم الحالي
    
    Usage:
        {% get_user_role_color as role_color %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return 'secondary'
    
    user = request.user
    if hasattr(user, 'role') and user.role and hasattr(user.role, 'color'):
        return user.role.color
    
    if hasattr(user, 'is_admin') and user.is_admin:
        return 'danger'
    elif hasattr(user, 'is_instructor') and user.is_instructor:
        return 'warning'
    elif hasattr(user, 'is_student') and user.is_student:
        return 'info'
    
    return 'secondary'


@register.simple_tag(takes_context=True)
def can_access_course(context, course):
    """
    التحقق من إمكانية وصول المستخدم لمقرر معين
    
    Usage:
        {% can_access_course course as can_access %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    user = request.user
    
    if hasattr(user, 'is_admin') and user.is_admin:
        return True
    
    if hasattr(user, 'is_instructor') and user.is_instructor:
        if hasattr(course, 'instructors'):
            return user in course.instructors.all()
    
    if hasattr(user, 'is_student') and user.is_student:
        if hasattr(user, 'enrolled_courses'):
            return course in user.enrolled_courses.all()
    
    return False


@register.simple_tag(takes_context=True)
def can_manage_course(context, course):
    """
    التحقق من إمكانية إدارة المستخدم لمقرر معين
    
    Usage:
        {% can_manage_course course as can_manage %}
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    user = request.user
    
    if hasattr(user, 'is_admin') and user.is_admin:
        return True
    
    if hasattr(user, 'is_instructor') and user.is_instructor:
        if hasattr(course, 'instructors'):
            return user in course.instructors.all()
    
    return False
