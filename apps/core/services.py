"""
خدمات تطبيق Core
S-ACM - Smart Academic Content Management System

يحتوي على:
1. SidebarMenuService - خدمة القائمة الجانبية الديناميكية
"""

from dataclasses import dataclass
from typing import List, Optional
from django.urls import reverse, NoReverseMatch
import logging

logger = logging.getLogger(__name__)


@dataclass
class MenuItem:
    """عنصر في القائمة الجانبية"""
    code: str
    title: str
    icon: str
    url_name: Optional[str] = None
    permission: Optional[str] = None
    badge: Optional[str] = None
    badge_color: str = 'primary'
    children: List['MenuItem'] = None
    is_divider: bool = False
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    @property
    def label(self):
        """اسم العنصر (للتوافق مع القوالب)"""
        return self.title
    
    @property
    def badge_class(self):
        """صنف CSS للشارة"""
        return f'bg-{self.badge_color}'
    
    @property
    def url(self):
        """الحصول على URL العنصر"""
        if not self.url_name:
            return '#'
        try:
            return reverse(self.url_name)
        except NoReverseMatch:
            logger.warning(f"Could not reverse URL: {self.url_name}")
            return '#'
    
    @property
    def get_url(self):
        """الحصول على URL العنصر (للتوافق مع القوالب)"""
        return self.url


class SidebarMenuService:
    """
    خدمة القائمة الجانبية الديناميكية
    
    تقوم بإنشاء قائمة جانبية مخصصة لكل مستخدم بناءً على صلاحياته
    """
    
    @classmethod
    def get_menu_items(cls, user) -> List[MenuItem]:
        """
        الحصول على عناصر القائمة للمستخدم
        
        Args:
            user: المستخدم الحالي
            
        Returns:
            قائمة عناصر القائمة المرئية للمستخدم
        """
        if not user or not user.is_authenticated:
            return []
        
        menu_items = []
        
        # لوحة التحكم - للجميع
        menu_items.append(MenuItem(
            code='dashboard',
            title='لوحة التحكم',
            icon='bi-speedometer2',
            url_name='core:dashboard',
        ))
        
        # المقررات - للجميع
        menu_items.append(MenuItem(
            code='courses',
            title='المقررات',
            icon='bi-book',
            url_name='courses:course_list',
        ))
        
        # تحديد نوع المستخدم
        is_admin = hasattr(user, 'is_admin') and callable(user.is_admin) and user.is_admin()
        is_instructor = hasattr(user, 'is_instructor') and callable(user.is_instructor) and user.is_instructor()
        is_student = hasattr(user, 'is_student') and callable(user.is_student) and user.is_student()
        
        # عناصر المدرس
        if is_instructor or is_admin:
            menu_items.append(MenuItem(
                code='my_files',
                title='ملفاتي',
                icon='bi-folder',
                url_name='courses:instructor_course_list',
            ))
        
        # عناصر الذكاء الاصطناعي - للطلاب والمدرسين
        if is_student or is_instructor:
            menu_items.append(MenuItem(
                code='ai_features',
                title='الذكاء الاصطناعي',
                icon='bi-stars',
                url_name='ai_features:index',
                children=[
                    MenuItem(
                        code='ai_summarize',
                        title='تلخيص المحتوى',
                        icon='bi-card-text',
                        url_name='ai_features:summarize_select',
                    ),
                    MenuItem(
                        code='ai_quiz',
                        title='اختبار ذاتي',
                        icon='bi-question-circle',
                        url_name='ai_features:quiz_select',
                    ),
                    MenuItem(
                        code='ai_ask',
                        title='اسأل عن المقرر',
                        icon='bi-chat-dots',
                        url_name='ai_features:ask_select',
                    ),
                ]
            ))
        
        # فاصل
        if is_admin:
            menu_items.append(MenuItem(
                code='divider_admin',
                title='',
                icon='',
                is_divider=True,
            ))
        
        # عناصر المسؤول
        if is_admin:
            # إدارة المستخدمين
            menu_items.append(MenuItem(
                code='users',
                title='المستخدمين',
                icon='bi-people',
                url_name='accounts:admin_user_list',
                permission='view_users',
                children=[
                    MenuItem(
                        code='users_list',
                        title='قائمة المستخدمين',
                        icon='bi-list',
                        url_name='accounts:admin_user_list',
                    ),
                    MenuItem(
                        code='users_create',
                        title='إضافة مستخدم',
                        icon='bi-person-plus',
                        url_name='accounts:admin_user_create',
                    ),
                    MenuItem(
                        code='users_import',
                        title='استيراد',
                        icon='bi-file-earmark-arrow-up',
                        url_name='accounts:admin_user_import',
                    ),
                ]
            ))
            
            # الأدوار والصلاحيات
            menu_items.append(MenuItem(
                code='roles',
                title='الأدوار والصلاحيات',
                icon='bi-shield-lock',
                url_name='accounts:admin_roles',
                permission='manage_roles',
            ))
            
            # التقارير
            menu_items.append(MenuItem(
                code='reports',
                title='التقارير',
                icon='bi-bar-chart',
                url_name='core:dashboard',  # مؤقتاً
                permission='view_reports',
            ))
            
            # الإعدادات
            menu_items.append(MenuItem(
                code='settings',
                title='الإعدادات',
                icon='bi-gear',
                url_name='core:dashboard',  # مؤقتاً
                permission='manage_settings',
            ))
        
        return menu_items
    
    @classmethod
    def get_current_menu_item(cls, request, menu_items: List[MenuItem]) -> Optional[str]:
        """
        تحديد العنصر النشط في القائمة
        
        Args:
            request: الطلب الحالي
            menu_items: قائمة العناصر
            
        Returns:
            كود العنصر النشط أو None
        """
        current_path = request.path
        
        for item in menu_items:
            if item.url_name:
                try:
                    item_path = reverse(item.url_name)
                    if current_path.startswith(item_path):
                        return item.code
                except NoReverseMatch:
                    pass
            
            # البحث في العناصر الفرعية
            for child in item.children:
                if child.url_name:
                    try:
                        child_path = reverse(child.url_name)
                        if current_path.startswith(child_path):
                            return child.code
                    except NoReverseMatch:
                        pass
        
        return None
