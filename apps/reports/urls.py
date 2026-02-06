"""
URLs لتطبيق reports
S-ACM - Smart Academic Content Management System
"""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Reports Dashboard
    path('', views.ReportsIndexView.as_view(), name='index'),
    
    # Export Reports
    path('export/', views.ReportExportView.as_view(), name='export'),
    
    # Generate Reports
    path('generate/', views.ReportGenerateView.as_view(), name='generate'),
    
    # Specific Reports
    path('users/', views.UsersReportView.as_view(), name='users_report'),
    path('courses/', views.CoursesReportView.as_view(), name='courses_report'),
    path('files/', views.FilesReportView.as_view(), name='files_report'),
    path('activity/', views.ActivityReportView.as_view(), name='activity_report'),
]
