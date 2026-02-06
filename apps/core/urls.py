"""
URLs لتطبيق core
S-ACM - Smart Academic Content Management System
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # الصفحة الرئيسية
    path('', views.HomeView.as_view(), name='home'),
    
    # لوحة التحكم الموحدة
    path('dashboard/', views.unified_dashboard, name='dashboard'),
    
    # توجيه لوحة التحكم (للتوافق مع الروابط القديمة)
    path('dashboard/redirect/', views.dashboard_redirect, name='dashboard_redirect'),
    
    # الملف الشخصي
    path('profile/', views.profile_view, name='profile'),
    
    # صفحات عامة
    path('about/', views.AboutView.as_view(), name='about'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # Health check endpoint (for Docker, Kubernetes, load balancers)
    path('health/', views.health_check, name='health_check'),
    
    # صفحات الإدارة
    path('users/', views.UsersListView.as_view(), name='users_list'),
    path('roles/', views.RolesListView.as_view(), name='roles_list'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('audit-logs/', views.AuditLogsView.as_view(), name='audit_logs'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
]
