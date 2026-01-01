from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CompanyInfo


def contact_page(request):
    """Display company contact information"""
    company_info = CompanyInfo.get_instance()
    return render(request, 'core/contact.html', {
        'company_info': company_info
    })
