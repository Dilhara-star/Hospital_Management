from datetime import date  # today's date, used to count today's appointments
from django.shortcuts import render, redirect  # helpers for rendering pages and redirecting
from django.contrib.auth import login, update_session_auth_hash  # django's login tools
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from django.contrib import messages  # lets us show "success"/"error" banners after an action
from .forms import PatientSignupForm  # our patient sign up form
# reuse the same profile forms the frontend "My Profile" page uses
from apps.frontend.forms import ProfileDetailsForm, ProfilePictureForm, ChangePasswordForm
from apps.user_management.models import UserProfile, PatientProfile, StaffProfile  # our own profile models
from apps.appointment.models import Appointment, Payment  # used to show real counts on the dashboard home page
from apps.stock.models import Medicine  # used to count low stock medicines on the dashboard home page
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role

# role codes that count as "staff" and may open the dashboard area
STAFF_ROLES = ['admin', 'doctor', 'nurse', 'receptionist', 'pharmacist', 'lab_technician']


# ── Shared Helpers ───────────────────────────────────────────────────────────

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


# ── Dashboard ────────────────────────────────────────────────────────────────

# staff home page: shows today's appointment/payment/patient/low-stock counts
@login_required
@required_role(STAFF_ROLES, 'You do not have permission to view the dashboard.', 'frontend_index')
def dashboard_index(request):
    # doctors should always land on their appointments, not the generic dashboard
    if hasattr(request.user, 'profile') and request.user.profile.role == 'doctor':
        return redirect('appointment_index')  # send doctor straight to their appointment list

    today = date.today()  # today's date
    today_appointments_count = Appointment.objects.filter(date=today).count()  # appointments booked for today
    pending_appointments_count = Appointment.objects.filter(status='pending').count()  # appointments waiting to be confirmed
    pending_payments_count = Payment.objects.filter(status='pending').count()  # payments not collected yet
    total_patients_count = PatientProfile.objects.count()  # how many patients are registered

    # count medicines whose total stock has dropped to or below their reorder level
    low_stock_count = 0  # start the count at zero
    for medicine in Medicine.objects.all():  # check every medicine
        if medicine.is_low_stock:  # true if its stock is running low
            low_stock_count += 1  # add one to the count

    return render(request, 'dashboard/index.html', {
        'today_appointments_count': today_appointments_count,
        'pending_appointments_count': pending_appointments_count,
        'pending_payments_count': pending_payments_count,
        'total_patients_count': total_patients_count,
        'low_stock_count': low_stock_count,
    })


# lets a logged in staff member view/edit their own details, picture, and password
@login_required
@required_role(STAFF_ROLES, 'You do not have permission to view this page.', 'frontend_index')
def dashboard_profile(request):
    staff_user = request.user
    # find their profile row, or make one if it does not exist yet
    profile, _created = UserProfile.objects.get_or_create(user=staff_user, defaults={'role': 'admin'})

    # doctors have a staff profile holding their hourly fee; other roles may not have one yet
    try:
        sp = staff_user.staff_profile
    except StaffProfile.DoesNotExist:
        sp = None

    # forms are only used to check the typed data is valid; the actual save is done by hand below
    details_form = ProfileDetailsForm(request.POST or None, user=staff_user)
    picture_form = ProfilePictureForm(request.POST or None, request.FILES or None)
    password_form = ChangePasswordForm(request.POST or None)

    if request.method == 'POST':
        action = request.POST.get('action')  # which form on the page was submitted

        if action == 'update_details' and details_form.is_valid():
            staff_user.first_name = request.POST.get('first_name', '')  # first name
            staff_user.last_name = request.POST.get('last_name', '')  # last name
            staff_user.email = request.POST.get('email', '')  # email address
            staff_user.save()  # write the changes to the database

            profile.phone = request.POST.get('phone', '')  # phone number
            profile.date_of_birth = request.POST.get('date_of_birth') or None  # date of birth
            profile.gender = request.POST.get('gender', '')  # gender
            profile.save()  # write the changes to the database

            messages.success(request, 'Profile details updated successfully.')
            return redirect('dashboard_profile')  # reload the page fresh

        elif action == 'update_picture' and picture_form.is_valid():
            profile.profile_picture = request.FILES.get('profile_picture')  # save the uploaded picture
            profile.save()
            messages.success(request, 'Profile picture updated.')
            return redirect('dashboard_profile')

        elif action == 'change_password' and password_form.is_valid():
            if not password_form.validate_current_password(staff_user):  # check old password matches
                password_form.add_error('current_password', 'Current password is incorrect.')
            else:
                staff_user.set_password(request.POST.get('new_password', ''))  # set the new password
                staff_user.save()
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


# ── Frontend ───────────────────────────────────────────────────────────────
# note: login/logout/forgot-password/reset-password views live in
# apps/user_management/views.py now - this app only keeps patient self sign up

# public patient self sign up page: creates the login account plus a blank patient record
def register_view(request):
    if request.user.is_authenticated:
        # already logged in accounts don't need to sign up again
        return _redirect_by_role(request.user)

    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = PatientSignupForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # step 1: create the login account (User model)
        patient_account = User.objects.create_user(
            username=request.POST.get('username', ''),  # login name
            email=request.POST.get('email', ''),  # email address
            password=request.POST.get('password', ''),  # password (Django hashes this for us)
            first_name=request.POST.get('first_name', ''),  # first name
            last_name=request.POST.get('last_name', ''),  # last name
        )
        # step 2: create their basic profile, always with role "patient"
        UserProfile.objects.create(
            user=patient_account,  # link back to the account we just made
            phone=request.POST.get('phone', ''),  # phone number
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

    return render(request, 'dashboard/auth/register.html', {'form': form})
