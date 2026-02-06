# تقرير المشاكل المتبقية والإصلاحات المطلوبة
## مشروع S-ACM - نظام إدارة المحتوى الأكاديمي الذكي
**تاريخ التقرير:** 27 يناير 2026

---

## ملخص الحالة الحالية

### ✅ ما تم إنجازه بنجاح:
1. **توحيد القوالب الأساسية** - تم إنشاء `dashboard_base.html` و `base.html`
2. **إنشاء المكونات** - 10 مكونات قابلة لإعادة الاستخدام
3. **لوحة التحكم الموحدة** - تعمل بشكل صحيح ✅
4. **صفحة قائمة المقررات** - تعمل بشكل صحيح ✅
5. **القائمة الجانبية الديناميكية** - تعمل حسب الصلاحيات ✅
6. **البيانات الوهمية** - تم إنشاء مستخدمين ومقررات للاختبار ✅

---

## 🔴 المشاكل الحرجة (يجب إصلاحها أولاً)

### 1. صفحة تفاصيل المقرر (`/courses/<id>/`) - خطأ 500

**الملف:** `templates/courses/detail.html`

**المشكلة:** URLs غير موجودة في ملف `file_item.html`

**الإصلاح المطلوب:**
```python
# في ملف apps/courses/urls.py أضف:
path('files/<int:pk>/edit/', views_unified.file_edit, name='file_edit'),
path('files/<int:pk>/delete/', views_unified.file_delete, name='file_delete'),
```

**أو** عدّل `templates/components/file_item.html`:
```html
# السطر 122 - غيّر:
{% url 'courses:file_edit' file.id %}
# إلى:
{% url 'courses:file_update' file.id %}

# السطر 155 - غيّر:
{% url 'courses:file_delete' file.id %}
# إلى:
{% url 'courses:file_delete' file.id %}  # موجود بالفعل
```

---

### 2. URLs الذكاء الاصطناعي غير موجودة

**الملف:** `templates/components/file_item.html` (السطور 107-113)

**المشكلة:** URLs التالية غير موجودة:
- `ai_features:summarize` ← موجود ✅
- `ai_features:generate_questions` ← **غير موجود** ❌
- `ai_features:ask_document` ← موجود ✅

**الإصلاح المطلوب:**
```python
# في ملف apps/ai_features/urls.py أضف:
path('generate-questions/<int:file_id>/', views.GenerateQuestionsView.as_view(), name='generate_questions'),
```

**أو** عدّل `file_item.html` السطر 110:
```html
# غيّر:
{% url 'ai_features:generate_questions' file.id %}
# إلى:
{% url 'ai_features:questions' file.id %}
```

---

## 🟡 مشاكل متوسطة الأهمية

### 3. صفحات الإدارة - Views غير مكتملة

**الملفات المتأثرة:**
- `templates/users/list.html`
- `templates/roles/list.html`
- `templates/reports/index.html`
- `templates/settings/index.html`

**المشكلة:** القوالب موجودة لكن Views غير مربوطة

**الإصلاح المطلوب:**
```python
# في apps/core/views.py أضف:

class UsersListView(LoginRequiredMixin, TemplateView):
    template_name = 'users/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = User.objects.all()
        return context

class RolesListView(LoginRequiredMixin, TemplateView):
    template_name = 'roles/list.html'
    
class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = 'reports/index.html'
    
class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'settings/index.html'
```

```python
# في apps/core/urls.py أضف:
path('users/', views.UsersListView.as_view(), name='users_list'),
path('roles/', views.RolesListView.as_view(), name='roles_list'),
path('reports/', views.ReportsView.as_view(), name='reports'),
path('settings/', views.SettingsView.as_view(), name='settings'),
```

---

### 4. روابط القائمة الجانبية - بعضها لا يعمل

**الملف:** `apps/core/menu.py`

**الروابط التي تحتاج تحقق:**
| الرابط | الحالة | الإصلاح |
|--------|--------|---------|
| `accounts:admin_dashboard` | ✅ يعمل | - |
| `courses:course_list` | ✅ يعمل | - |
| `courses:admin_course_list` | ✅ يعمل | - |
| `notifications:list` | ❓ يحتاج تحقق | تحقق من apps/notifications/urls.py |
| `ai_features:usage_stats` | ✅ يعمل | - |
| `core:settings` | ❌ غير موجود | أضف URL |
| `core:audit_logs` | ❌ غير موجود | أضف URL |
| `core:statistics` | ❌ غير موجود | أضف URL |

---

## 🟢 مشاكل بسيطة (تحسينات)

### 5. ملفات CSS/JS مفقودة

**المشكلة:** بعض الأنماط قد لا تظهر بشكل صحيح

**الملفات المطلوبة:**
```
static/css/dashboard.css  ← موجود ✅
static/css/sidebar.css    ← موجود ✅
static/js/sidebar.js      ← موجود ✅
```

### 6. Template Tags - تحتاج اختبار

**الملف:** `apps/core/templatetags/permissions.py`

**الدوال المطلوب اختبارها:**
- `has_permission`
- `can_view_course`
- `can_edit_course`
- `can_upload_file`
- `get_user_role_badge`

---

## 📋 قائمة الإصلاحات بالترتيب

### الأولوية 1 (حرجة):
1. [ ] إصلاح `file_item.html` - تغيير `file_edit` إلى `file_update`
2. [ ] إصلاح `file_item.html` - تغيير `generate_questions` إلى `questions`
3. [ ] اختبار صفحة تفاصيل المقرر بعد الإصلاح

### الأولوية 2 (متوسطة):
4. [ ] إضافة Views لصفحات الإدارة (users, roles, reports, settings)
5. [ ] إضافة URLs في `core/urls.py`
6. [ ] إصلاح روابط القائمة الجانبية

### الأولوية 3 (تحسينات):
7. [ ] اختبار جميع الصفحات
8. [ ] اختبار الأزرار والنماذج
9. [ ] التحقق من الصلاحيات

---

## 🔧 أوامر الإصلاح السريع

### إصلاح file_item.html:
```bash
cd /home/ubuntu/scam_analysis
sed -i "s/{% url 'courses:file_edit' file.id %}/{% url 'courses:file_update' file.id %}/g" templates/components/file_item.html
sed -i "s/{% url 'ai_features:generate_questions' file.id %}/{% url 'ai_features:questions' file.id %}/g" templates/components/file_item.html
```

### إعادة تشغيل السيرفر:
```bash
pkill -f "runserver"
cd /home/ubuntu/scam_analysis && python3 manage.py runserver 0.0.0.0:8000 &
```

---

## 📁 الملفات الرئيسية للمراجعة

```
/home/ubuntu/scam_analysis/
├── templates/
│   ├── components/
│   │   ├── file_item.html          # يحتاج إصلاح URLs
│   │   ├── course_card.html        # ✅ تم إصلاحه
│   │   ├── stat_card.html          # ✅ تم إصلاحه
│   │   ├── page_header.html        # ✅ تم إصلاحه
│   │   ├── empty_state.html        # ✅ تم إصلاحه
│   │   └── modal_confirm.html      # ✅ تم إصلاحه
│   ├── courses/
│   │   ├── list.html               # ✅ يعمل
│   │   ├── detail.html             # يحتاج إصلاح URLs
│   │   ├── form.html               # يحتاج اختبار
│   │   └── file_upload.html        # يحتاج اختبار
│   ├── dashboard/
│   │   └── index.html              # ✅ يعمل
│   └── layouts/
│       └── dashboard_base.html     # ✅ يعمل
├── apps/
│   ├── core/
│   │   ├── views.py                # يحتاج إضافة Views
│   │   ├── urls.py                 # يحتاج إضافة URLs
│   │   ├── menu.py                 # يحتاج مراجعة URLs
│   │   └── services.py             # ✅ يعمل
│   └── courses/
│       ├── views_unified.py        # ✅ يعمل
│       └── urls.py                 # يحتاج مراجعة
└── static/
    ├── css/
    │   ├── dashboard.css           # ✅ موجود
    │   └── sidebar.css             # ✅ موجود
    └── js/
        └── sidebar.js              # ✅ موجود
```

---

## 🔐 بيانات الاختبار

### المستخدمون:
| الاسم | الرقم الأكاديمي | كلمة المرور | الدور |
|-------|-----------------|-------------|-------|
| مدير النظام | admin001 | admin123 | مسؤول |
| أحمد محمد | inst001 | test123 | مدرس |
| سارة علي | inst002 | test123 | مدرس |
| محمد أحمد | std001 | test123 | طالب |
| فاطمة خالد | std002 | test123 | طالب |

### المقررات:
- مقدمة في البرمجة (CS101)
- هياكل البيانات (CS201)
- قواعد البيانات (CS301)
- نظم المعلومات الإدارية (IS201)
- هندسة البرمجيات (CS302)
- مقدمة في نظم المعلومات الإدارية (IS201)

---

## ✅ الخطوة التالية

1. افتح الملف `templates/components/file_item.html`
2. غيّر السطر 122 من `file_edit` إلى `file_update`
3. غيّر السطر 110 من `generate_questions` إلى `questions`
4. أعد تشغيل السيرفر
5. اختبر صفحة تفاصيل المقرر

---

**ملاحظة:** هذا التقرير يعكس حالة المشروع في 27 يناير 2026. يرجى تحديثه بعد كل إصلاح.
