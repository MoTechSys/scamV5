#!/bin/bash

# S-ACM Development Environment Setup Script
# هذا السكريبت يقوم بإعداد بيئة التطوير للمشروع

echo "=========================================="
echo "  S-ACM Development Environment Setup"
echo "=========================================="

# التحقق من وجود Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# التحقق من وجود pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed."
    exit 1
fi

# الانتقال إلى مجلد المشروع
PROJECT_DIR="${1:-/home/ubuntu/ScamV4_Extracted/pasted_file_AsU6pS_ScamV4}"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory not found at $PROJECT_DIR"
    echo "Usage: ./setup_dev.sh /path/to/project"
    exit 1
fi

cd "$PROJECT_DIR"
echo "Working directory: $(pwd)"

# إنشاء بيئة افتراضية (اختياري)
# python3 -m venv venv
# source venv/bin/activate

# تثبيت المتطلبات
echo ""
echo "Installing requirements..."
pip3 install -r requirements.txt

# إنشاء ملف .env إذا لم يكن موجوداً
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please update .env with your settings."
fi

# تطبيق الـ migrations
echo ""
echo "Applying database migrations..."
python3 manage.py migrate

# إنشاء مستخدم أدمن (اختياري)
echo ""
echo "Do you want to create a superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    python3 manage.py createsuperuser
fi

# جمع الملفات الثابتة
echo ""
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "To start the development server, run:"
echo "  python3 manage.py runserver"
echo ""
