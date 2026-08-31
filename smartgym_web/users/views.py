"""
SmartGym AI — Users Views (Auth)
Login, Logout, Register
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Username dan password wajib diisi.')
            return render(request, 'auth/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return _redirect_by_role(user)
            else:
                messages.error(request, 'Akun Anda telah dinonaktifkan. Hubungi administrator.')
        else:
            messages.error(request, 'Username atau password salah.')

    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def _redirect_by_role(user):
    role_map = {
        'admin': 'admin_dashboard',
        'pt': 'pt_dashboard',
        'klien': 'klien_dashboard',
    }
    url_name = role_map.get(user.role, 'login')
    return redirect(url_name)
