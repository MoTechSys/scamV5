"""
Views الموحدة للمقررات - Unified Course Views
S-ACM - Smart Academic Content Management System

تحتوي على Views موحدة للمقررات تعمل لجميع أنواع المستخدمين
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Q, Count
from django.urls import reverse_lazy

from .models import Course, LectureFile, CourseMajor, InstructorCourse
from apps.accounts.models import Semester, Level, Major


class UnifiedCourseListView(LoginRequiredMixin, ListView):
    """
    قائمة المقررات الموحدة - تعرض المقررات حسب صلاحيات المستخدم
    """
    model = Course
    template_name = 'courses/list.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.all()
        
        # تصفية حسب نوع المستخدم
        if hasattr(user, 'is_admin') and user.is_admin():
            # المسؤول يرى جميع المقررات
            pass
        elif hasattr(user, 'is_instructor') and user.is_instructor():
            # المدرس يرى مقرراته فقط
            instructor_courses = InstructorCourse.objects.filter(instructor=user).values_list('course_id', flat=True)
            queryset = queryset.filter(id__in=instructor_courses)
        else:
            # الطالب يرى جميع المقررات النشطة
            queryset = queryset.filter(is_active=True)
        
        # تطبيق الفلاتر
        queryset = self._apply_filters(queryset)
        
        return queryset.order_by('-created_at')
    
    def _apply_filters(self, queryset):
        """تطبيق فلاتر البحث"""
        # البحث النصي
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(course_name__icontains=q) |
                Q(course_code__icontains=q)
            )
        
        # فلتر الفصل الدراسي
        semester = self.request.GET.get('semester')
        if semester:
            queryset = queryset.filter(semester_id=semester)
        
        # فلتر المستوى
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level_id=level)
        
        # فلتر التخصص
        major = self.request.GET.get('major')
        if major:
            queryset = queryset.filter(course_majors__major_id=major)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # بيانات الفلاتر
        context['semesters'] = Semester.objects.all()
        context['levels'] = Level.objects.all()
        context['majors'] = Major.objects.all()
        
        # الفصل الحالي
        context['current_semester'] = Semester.objects.filter(is_current=True).first()
        
        # إحصائيات
        if hasattr(user, 'is_admin') and user.is_admin():
            context['total_courses'] = Course.objects.count()
        elif hasattr(user, 'is_instructor') and user.is_instructor():
            context['total_courses'] = InstructorCourse.objects.filter(instructor=user).count()
        else:
            context['total_courses'] = Course.objects.filter(is_active=True).count()
        
        # هل يمكن للمستخدم إنشاء مقرر؟
        context['can_create_course'] = hasattr(user, 'is_admin') and user.is_admin()
        
        return context


class UnifiedCourseDetailView(LoginRequiredMixin, DetailView):
    """
    تفاصيل المقرر الموحدة
    """
    model = Course
    template_name = 'courses/detail.html'
    context_object_name = 'course'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        user = self.request.user
        
        # الملفات مصنفة حسب النوع
        files = course.files.all()
        if not (hasattr(user, 'is_admin') and user.is_admin()):
            # فلترة الملفات المرئية فقط للطلاب
            files = files.filter(is_visible=True)
        
        context['lecture_files'] = files.filter(file_type='Lecture')
        context['assignment_files'] = files.filter(file_type='Assignment')
        context['reference_files'] = files.filter(file_type='Reference')
        context['summary_files'] = files.filter(file_type='Summary')
        context['exam_files'] = files.filter(file_type='Exam')
        context['other_files'] = files.filter(file_type='Other')
        context['files'] = files
        context['files_count'] = files.count()
        
        # المدرسين
        context['instructors'] = InstructorCourse.objects.filter(course=course).select_related('instructor')
        
        # عدد الطلاب
        context['students_count'] = 0  # يمكن حسابها لاحقاً
        
        # صلاحيات الإدارة
        is_admin = hasattr(user, 'is_admin') and user.is_admin()
        is_course_instructor = InstructorCourse.objects.filter(course=course, instructor=user).exists()
        context['can_manage_files'] = is_admin or is_course_instructor
        
        # روابط الإجراءات
        context['upload_url'] = reverse_lazy('courses:file_upload', kwargs={'pk': course.pk})
        
        return context


@login_required
def course_list(request):
    """View function لقائمة المقررات"""
    view = UnifiedCourseListView.as_view()
    return view(request)


@login_required
def course_detail(request, pk):
    """View function لتفاصيل المقرر"""
    view = UnifiedCourseDetailView.as_view()
    return view(request, pk=pk)


@login_required
def file_upload(request, pk=None):
    """رفع ملف لمقرر"""
    user = request.user
    
    # إذا لم يتم تحديد مقرر، عرض قائمة المقررات للاختيار
    if pk is None:
        if hasattr(user, 'is_admin') and user.is_admin():
            courses = Course.objects.all()
        elif hasattr(user, 'is_instructor') and user.is_instructor():
            instructor_courses = InstructorCourse.objects.filter(instructor=user).values_list('course_id', flat=True)
            courses = Course.objects.filter(id__in=instructor_courses)
        else:
            messages.error(request, 'ليس لديك صلاحية رفع ملفات')
            return redirect('courses:course_list')
        
        return render(request, 'courses/file_upload.html', {
            'courses': courses,
            'select_course': True,
        })
    
    course = get_object_or_404(Course, pk=pk)
    
    # التحقق من الصلاحية
    is_admin = hasattr(user, 'is_admin') and user.is_admin()
    is_course_instructor = InstructorCourse.objects.filter(course=course, instructor=user).exists()
    
    if not (is_admin or is_course_instructor):
        messages.error(request, 'ليس لديك صلاحية رفع ملفات لهذا المقرر')
        return redirect('courses:course_detail', pk=pk)
    
    if request.method == 'POST':
        # معالجة رفع الملف
        title = request.POST.get('title')
        file_type = request.POST.get('file_type', 'Lecture')
        content_type = request.POST.get('content_type', 'local_file')
        description = request.POST.get('description', '')
        is_visible = request.POST.get('is_visible') == 'on'
        
        if content_type == 'external_link':
            external_link = request.POST.get('external_link')
            # إنشاء ملف من رابط خارجي
            lecture_file = LectureFile.objects.create(
                course=course,
                title=title,
                file_type=file_type,
                content_type='external_link',
                external_link=external_link,
                description=description,
                is_visible=is_visible,
                uploader=user,
            )
        else:
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                lecture_file = LectureFile.objects.create(
                    course=course,
                    title=title,
                    file_type=file_type,
                    content_type='local_file',
                    local_file=uploaded_file,
                    description=description,
                    is_visible=is_visible,
                    uploader=user,
                    file_size=uploaded_file.size,
                )
        
        messages.success(request, f'تم رفع الملف "{title}" بنجاح')
        return redirect('courses:course_detail', pk=pk)
    
    return render(request, 'courses/file_upload.html', {
        'course': course,
    })


@login_required
def course_create(request):
    """إنشاء مقرر جديد"""
    user = request.user
    
    # التحقق من الصلاحية
    if not (hasattr(user, 'is_admin') and user.is_admin()):
        messages.error(request, 'ليس لديك صلاحية إنشاء مقررات')
        return redirect('courses:course_list')
    
    if request.method == 'POST':
        course_code = request.POST.get('course_code')
        course_name = request.POST.get('course_name')
        description = request.POST.get('description', '')
        level_id = request.POST.get('level')
        semester_id = request.POST.get('semester')
        credit_hours = request.POST.get('credit_hours', 3)
        major_ids = request.POST.getlist('majors')
        is_active = request.POST.get('is_active') == 'on'
        
        course = Course.objects.create(
            course_code=course_code,
            course_name=course_name,
            description=description,
            level_id=level_id,
            semester_id=semester_id,
            credit_hours=credit_hours,
            is_active=is_active,
        )
        
        # إضافة التخصصات
        for major_id in major_ids:
            CourseMajor.objects.create(course=course, major_id=major_id)
        
        messages.success(request, f'تم إنشاء المقرر "{course_name}" بنجاح')
        return redirect('courses:course_detail', pk=course.pk)
    
    return render(request, 'courses/form.html', {
        'levels': Level.objects.all(),
        'semesters': Semester.objects.all(),
        'majors': Major.objects.all(),
    })


@login_required
def course_edit(request, pk):
    """تعديل مقرر"""
    course = get_object_or_404(Course, pk=pk)
    user = request.user
    
    # التحقق من الصلاحية
    if not (hasattr(user, 'is_admin') and user.is_admin()):
        messages.error(request, 'ليس لديك صلاحية تعديل هذا المقرر')
        return redirect('courses:course_detail', pk=pk)
    
    if request.method == 'POST':
        course.course_code = request.POST.get('course_code')
        course.course_name = request.POST.get('course_name')
        course.description = request.POST.get('description', '')
        course.level_id = request.POST.get('level')
        course.semester_id = request.POST.get('semester')
        course.credit_hours = request.POST.get('credit_hours', 3)
        course.is_active = request.POST.get('is_active') == 'on'
        course.save()
        
        # تحديث التخصصات
        major_ids = request.POST.getlist('majors')
        CourseMajor.objects.filter(course=course).delete()
        for major_id in major_ids:
            CourseMajor.objects.create(course=course, major_id=major_id)
        
        messages.success(request, f'تم تعديل المقرر "{course.course_name}" بنجاح')
        return redirect('courses:course_detail', pk=course.pk)
    
    # الحصول على التخصصات الحالية
    current_majors = CourseMajor.objects.filter(course=course).values_list('major_id', flat=True)
    
    return render(request, 'courses/form.html', {
        'course': course,
        'levels': Level.objects.all(),
        'semesters': Semester.objects.all(),
        'majors': Major.objects.all(),
        'current_majors': list(current_majors),
    })
