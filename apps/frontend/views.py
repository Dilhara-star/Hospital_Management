from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import ProfileDetailsForm, ProfilePictureForm, ChangePasswordForm
from apps.user_management.models import UserProfile, PatientProfile


def frontend_index(request):
    return render(request, 'frontend/index.html')


@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'admin'})

    details_form = ProfileDetailsForm(user=user)
    picture_form = ProfilePictureForm()
    password_form = ChangePasswordForm()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_details':
            details_form = ProfileDetailsForm(request.POST, user=user)
            if details_form.is_valid():
                details_form.save()
                messages.success(request, 'Profile details updated successfully.')
                return redirect('profile')
            # fall through to re-render with errors

        elif action == 'update_picture':
            picture_form = ProfilePictureForm(request.POST, request.FILES)
            if picture_form.is_valid():
                picture_form.save(profile)
                messages.success(request, 'Profile picture updated.')
                return redirect('profile')

        elif action == 'change_password':
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                if not password_form.validate_current_password(user):
                    password_form.add_error('current_password', 'Current password is incorrect.')
                else:
                    password_form.save(user)
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Password changed successfully.')
                    return redirect('profile')

    return render(request, 'frontend/profile.html', {
        'details_form': details_form,
        'picture_form': picture_form,
        'password_form': password_form,
        'profile': profile,
    })


@login_required
def patient_portal(request):
    try:
        patient = request.user.patient_profile
    except PatientProfile.DoesNotExist:
        patient = None
    return render(request, 'frontend/patient_portal.html', {
        'patient': patient,
        'user': request.user,
    })
