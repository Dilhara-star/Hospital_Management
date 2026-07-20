from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignupForm
# reuse the same profile forms the frontend "My Profile" page uses
from apps.frontend.forms import ProfileDetailsForm, ProfilePictureForm, ChangePasswordForm
from apps.user_management.models import UserProfile, StaffProfile


@login_required
def dashboard_index(request):
    # doctors should always land on their appointments, not the generic dashboard
    if hasattr(request.user, 'profile') and request.user.profile.role == 'doctor':
        return redirect('appointment_index')  # send doctor straight to their appointment list
    return render(request, 'dashboard/index.html')


def _redirect_by_role(user):
    """Route patients to patient portal, regular users to frontend, staff to dashboard."""
    if hasattr(user, 'profile'):
        role = user.profile.role
        if role == 'patient':
            return redirect('patient_portal')
        if role == 'user':
            return redirect('frontend_index')
        if role == 'doctor':
            return redirect('appointment_index')  # doctor logs in and sees their appointments
    return redirect('dashboard_index')


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return _redirect_by_role(user)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'dashboard/auth/login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')


def register_view(request):
    # already logged in users don't need to sign up again
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log the new user in right away
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return _redirect_by_role(user)
    else:
        form = SignupForm()

    return render(request, 'dashboard/auth/register.html', {'form': form})


@login_required  # only logged in staff/admin/doctor users can open this page
def dashboard_profile(request):
    user = request.user  # the person who is currently logged in
    # find their profile row, or make one if it does not exist yet
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'admin'})

    # doctors have a staff profile holding their hourly fee; other roles may not have one yet
    try:
        sp = profile.staff_profile
    except StaffProfile.DoesNotExist:
        sp = None

    # build the 3 forms on the page, pre-filled with the user's current data
    details_form = ProfileDetailsForm(user=user)
    picture_form = ProfilePictureForm()
    password_form = ChangePasswordForm()

    if request.method == 'POST':
        action = request.POST.get('action')  # which form on the page was submitted

        if action == 'update_details':
            details_form = ProfileDetailsForm(request.POST, user=user)  # refill with submitted data
            if details_form.is_valid():
                details_form.save()  # save name/email/phone/dob/gender
                messages.success(request, 'Profile details updated successfully.')
                return redirect('dashboard_profile')  # reload the page fresh

        elif action == 'update_picture':
            picture_form = ProfilePictureForm(request.POST, request.FILES)  # files need request.FILES
            if picture_form.is_valid():
                picture_form.save(profile)  # save the uploaded picture on the profile
                messages.success(request, 'Profile picture updated.')
                return redirect('dashboard_profile')

        elif action == 'change_password':
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                if not password_form.validate_current_password(user):  # check old password matches
                    password_form.add_error('current_password', 'Current password is incorrect.')
                else:
                    password_form.save(user)  # set the new password
                    update_session_auth_hash(request, user)  # keep the user logged in after password change
                    messages.success(request, 'Password changed successfully.')
                    return redirect('dashboard_profile')

    # show the dashboard-styled profile page with all 3 forms
    return render(request, 'dashboard/profile/profile.html', {
        'details_form': details_form,
        'picture_form': picture_form,
        'password_form': password_form,
        'profile': profile,
        'sp': sp,
    })
