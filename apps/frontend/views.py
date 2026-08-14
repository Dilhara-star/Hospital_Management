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
    account = request.user
    profile, _ = UserProfile.objects.get_or_create(user=account, defaults={'role': 'admin'})

    # forms are only used to check the typed data is valid; the actual save is done by hand below
    details_form = ProfileDetailsForm(request.POST or None, user=account)
    picture_form = ProfilePictureForm(request.POST or None, request.FILES or None)
    password_form = ChangePasswordForm(request.POST or None)

    if request.method == 'POST':
        action = request.POST.get('action')  # which form on the page was submitted

        if action == 'update_details' and details_form.is_valid():
            account.first_name = request.POST.get('first_name', '')  # first name
            account.last_name = request.POST.get('last_name', '')  # last name
            account.email = request.POST.get('email', '')  # email address
            account.save()  # write the changes to the database

            profile.phone = request.POST.get('phone', '')  # phone number
            profile.date_of_birth = request.POST.get('date_of_birth') or None  # date of birth
            profile.gender = request.POST.get('gender', '')  # gender
            profile.save()  # write the changes to the database

            messages.success(request, 'Profile details updated successfully.')
            return redirect('profile')

        elif action == 'update_picture' and picture_form.is_valid():
            profile.profile_picture = request.FILES.get('profile_picture')  # save the uploaded picture
            profile.save()
            messages.success(request, 'Profile picture updated.')
            return redirect('profile')

        elif action == 'change_password' and password_form.is_valid():
            if not password_form.validate_current_password(account):  # check old password matches
                password_form.add_error('current_password', 'Current password is incorrect.')
            else:
                account.set_password(request.POST.get('new_password', ''))  # set the new password
                account.save()
                update_session_auth_hash(request, account)  # keep the account logged in after password change
                messages.success(request, 'Password changed successfully.')
                return redirect('profile')

    return render(request, 'frontend/profile/profile.html', {
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
    return render(request, 'frontend/patient/patient_portal.html', {
        'patient': patient,
        'user': request.user,
    })
