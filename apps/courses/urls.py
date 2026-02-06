"""
URL Configuration for Courses App - UNIFIED ROUTER
S-ACM - Smart Academic Content Management System

Single Source of Truth: Unified URLs that handle all roles via permissions.
NO LEGACY PATHS - All views are permission-based.
"""

from django.urls import path
from . import views
from . import views_unified

app_name = 'courses'

urlpatterns = [
    # ==============================
    # UNIFIED VIEWS (Permission-Based)
    # ==============================
    
    # Course List - Single view adapts to user permissions
    path('', views_unified.UnifiedCourseListView.as_view(), name='course_list'),
    path('list/', views_unified.UnifiedCourseListView.as_view(), name='list'),
    path('my/', views_unified.UnifiedCourseListView.as_view(), name='my_courses'),
    
    # Course Detail
    path('<int:pk>/', views_unified.UnifiedCourseDetailView.as_view(), name='course_detail'),
    path('<int:pk>/detail/', views_unified.UnifiedCourseDetailView.as_view(), name='detail'),
    
    # Course CRUD (Permission-Protected)
    path('create/', views_unified.course_create, name='course_create'),
    path('<int:pk>/edit/', views_unified.course_edit, name='course_edit'),
    path('<int:pk>/update/', views_unified.course_edit, name='course_update'),
    
    # ==============================
    # FILE OPERATIONS
    # ==============================
    path('files/upload/', views.FileUploadView.as_view(), name='file_upload'),
    path('files/<int:pk>/download/', views.FileDownloadView.as_view(), name='file_download'),
    path('files/<int:pk>/view/', views.FileViewView.as_view(), name='file_view'),
    path('files/<int:pk>/update/', views.FileUpdateView.as_view(), name='file_update'),
    path('files/<int:pk>/delete/', views.FileDeleteView.as_view(), name='file_delete'),
    path('files/<int:pk>/toggle-visibility/', views.FileToggleVisibilityView.as_view(), name='file_toggle_visibility'),
    
    # ==============================
    # AI Features
    # ==============================
    path('files/<int:pk>/ai/', views.InstructorAIGenerationView.as_view(), name='file_ai'),
]