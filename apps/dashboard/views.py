from django.shortcuts import render, redirect  # helpers for rendering pages and redirecting
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash  # django's login tools
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from django.contrib import messages  # lets us show "success"/"error" banners after an action
from .forms import PatientSignupForm  # our sign up form
# reuse the same profile forms the frontend "My Profile" page uses
from apps.frontend.forms import ProfileDetailsForm, ProfilePictureForm, ChangePasswordForm
from apps.user_management.models import UserProfile, PatientProfile, StaffProfile  # our own profile models


@login_required
def dashboard_index(request):
    # doctors should always land on their appointments, not the generic dashboard
    if hasattr(request.user, 'profile') and request.user.profile.role == 'doctor':
        return redirect('appointment_index')  # send doctor straight to their appointment list
    return render(request, 'dashboard/index.html')


def _redirect_by_role(person):
    # send patients to the patient portal, plain frontend accounts to the frontend, doctors to appointments, everyone else (staff) to the dashboard
    if hasattr(person, 'profile'):
        role = person.profile.role
        if role == 'patient':
            return redirect('patient_portal')
        if role == 'user':
            return redirect('frontend_index')
        if role == 'doctor':
            return redirect('appointment_index')  # doctor logs in and sees their appointments
    return redirect('dashboard_index')


def login_view(request):
    if request.user.is_authenticated:
        # already logged in, so skip straight to their home page
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        # read the username/password typed in the form
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        # check the username/password match an account
        person = authenticate(request, username=username, password=password)

        if person is not None:
            # log this account in
            login(request, person)
            # if they were sent here from another page, go back there after logging in
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return _redirect_by_role(person)
        else:
            # username/password did not match any account
            messages.error(request, 'Invalid username or password.')

    return render(request, 'dashboard/auth/login.html')


def logout_view(request):
    if request.method == 'POST':
        # log the current account out
        logout(request)
    return redirect('login')


def register_view(request):
    # already logged in accounts don't need to sign up again
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == 'POST':
        # visitor submitted the sign up form, so check the data they typed
        form = PatientSignupForm(request.POST)
        if form.is_valid():
            # data passed all checks, pull it out of the form
            data = form.cleaned_data
            # step 1: create the login account (User model)
            patient_account = User.objects.create_user(
                username=data['username'],  # login name
                email=data['email'],  # email address
                password=data['password'],  # password (Django hashes this for us)
                first_name=data['first_name'],  # first name
                last_name=data['last_name'],  # last name
            )
            # step 2: create their basic profile, always with role "patient"
            UserProfile.objects.create(
                user=patient_account,  # link back to the account we just made
                phone=data.get('phone', ''),  # phone number
                role='patient',  # self sign up always makes patients
            )
            # step 3: create their (empty for now) medical record
            PatientProfile.objects.create(user=patient_account)
            # log the new patient in right away
            login(request, patient_account)
            # if they were sent here from another page, go back there after signing up
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return _redirect_by_role(patient_account)
    else:
        # first time opening the page, show a blank form
        form = PatientSignupForm()

    return render(request, 'dashboard/auth/register.html', {'form': form})


@login_required  # only logged in staff/admin/doctor accounts can open this page
def dashboard_profile(request):
    # the staff member who is currently logged in
    staff_user = request.user
    # find their profile row, or make one if it does not exist yet
    profile, _created = UserProfile.objects.get_or_create(user=staff_user, defaults={'role': 'admin'})

    # doctors have a staff profile holding their hourly fee; other roles may not have one yet
    try:
        sp = profile.staff_profile
    except StaffProfile.DoesNotExist:
        sp = None

    # build the 3 forms on the page, pre-filled with the current values
    details_form = ProfileDetailsForm(user=staff_user)
    picture_form = ProfilePictureForm()
    password_form = ChangePasswordForm()

    if request.method == 'POST':
        action = request.POST.get('action')  # which form on the page was submitted

        if action == 'update_details':
            details_form = ProfileDetailsForm(request.POST, user=staff_user)  # refill with submitted data
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
                if not password_form.validate_current_password(staff_user):  # check old password matches
                    password_form.add_error('current_password', 'Current password is incorrect.')
                else:
                    password_form.save(staff_user)  # set the new password
                    update_session_auth_hash(request, staff_user)  # keep the account logged in after password change
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
