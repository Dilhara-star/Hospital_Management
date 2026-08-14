from django.shortcuts import render, redirect, get_object_or_404  # helpers for rendering pages and redirecting
from django.contrib import messages  # lets us show "success"/"error" banners after an action
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from .forms import PatientCreateForm, PatientEditForm, StaffCreateForm, StaffEditForm, STAFF_ROLE_CHOICES  # our forms
from .models import UserProfile, PatientProfile, StaffProfile  # our own profile models
from .notifications import send_staff_welcome_email  # emails a new staff member their username
from .notifications import send_patient_welcome_email  # emails a new patient their username

# role codes that count as "staff" (not a patient, not a plain "user")
STAFF_ROLES = ['admin', 'doctor', 'nurse', 'receptionist', 'pharmacist', 'lab_technician']

# roles allowed to assign a room to each doctor
ROOM_STAFF_ROLES = ('admin', 'receptionist')


def _is_room_staff(user):
    # true only for logged in users whose profile role can assign doctor rooms
    return hasattr(user, 'profile') and user.profile.role in ROOM_STAFF_ROLES


# ── Patient Management ────────────────────────────────────────────────────────

@login_required
def patient_user_list(request):
    # only show users whose current role is "patient"
    # this stops old patients from showing here after their role gets changed (e.g. to pharmacist)
    patients = PatientProfile.objects.select_related('user', 'user__profile').filter(user__profile__role='patient')
    # show the list page
    return render(request, 'dashboard/patient_management/patient_list.html', {'patients': patients})


@login_required
def patient_add(request):
    patient_user = User()  # a blank user, only used so the template can show default field values
    profile = UserProfile(role='patient')  # a blank profile
    patient = PatientProfile(status='active')  # a blank patient record
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = PatientCreateForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # step 1: create the login account (User model)
        patient_user = User.objects.create_user(
            username=request.POST.get('username', ''),  # login name
            email=request.POST.get('email', ''),  # email address
            password=request.POST.get('password', ''),  # password (Django hashes this for us)
            first_name=request.POST.get('first_name', ''),  # first name
            last_name=request.POST.get('last_name', ''),  # last name
            is_active=request.POST.get('is_active') == 'on',  # can they log in
        )
        # step 2: create their profile row, always with role "patient"
        UserProfile.objects.create(
            user=patient_user,  # link back to the User we just made
            phone=request.POST.get('phone', ''),  # phone number
            date_of_birth=request.POST.get('date_of_birth') or None,  # date of birth
            gender=request.POST.get('gender', ''),  # gender
            role='patient',  # this form always makes patients
        )
        # step 3: create the patient's medical/insurance record
        patient = PatientProfile.objects.create(
            user=patient_user,  # link back to the User we just made
            blood_type=request.POST.get('blood_type', ''),  # blood type
            allergies=request.POST.get('allergies', ''),  # known allergies
            chronic_conditions=request.POST.get('chronic_conditions', ''),  # chronic conditions
            address=request.POST.get('address', ''),  # home address
            emergency_contact_name=request.POST.get('emergency_contact_name', ''),  # emergency contact name
            emergency_contact_phone=request.POST.get('emergency_contact_phone', ''),  # emergency contact phone
            emergency_contact_relationship=request.POST.get('emergency_contact_relationship', ''),  # relationship
            insurance_provider=request.POST.get('insurance_provider', ''),  # insurance provider
            insurance_number=request.POST.get('insurance_number', ''),  # insurance policy number
            insurance_expiry=request.POST.get('insurance_expiry') or None,  # insurance expiry date
            status=request.POST.get('status', 'active'),  # patient status
        )
        send_patient_welcome_email(patient_user)
        # show a success banner with their auto-generated MRN
        messages.success(request, f'Patient "{patient.user.get_full_name()}" (MRN: {patient.mrn}) registered successfully.')
        # go back to the patient list page
        return redirect('patient_user_list')

    # show the add patient page
    return render(request, 'dashboard/patient_management/patient_add.html', {
        'form': form, 'patient_user': patient_user, 'profile': profile, 'patient': patient,
    })


@login_required
def patient_edit(request, patient_id):
    # find the patient we want to edit, or show a 404 page if they don't exist
    patient = get_object_or_404(PatientProfile, pk=patient_id)
    # the patient's login account
    patient_user = patient.user
    # the patient's basic profile (phone, gender, etc)
    profile = patient_user.profile

    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = PatientEditForm(request.POST or None, current_user=patient_user)

    if request.method == 'POST' and form.is_valid():
        # update the login account fields
        patient_user.first_name = request.POST.get('first_name', '')  # first name
        patient_user.last_name = request.POST.get('last_name', '')  # last name
        patient_user.email = request.POST.get('email', '')  # email address
        patient_user.username = request.POST.get('username', '')  # login name
        patient_user.is_active = request.POST.get('is_active') == 'on'  # can they log in
        patient_user.save()  # write the changes to the database

        # update the basic profile fields
        profile.phone = request.POST.get('phone', '')  # phone number
        profile.date_of_birth = request.POST.get('date_of_birth') or None  # date of birth
        profile.gender = request.POST.get('gender', '')  # gender
        profile.save()  # write the changes to the database

        # update the patient's medical/insurance record
        patient.blood_type = request.POST.get('blood_type', '')  # blood type
        patient.allergies = request.POST.get('allergies', '')  # known allergies
        patient.chronic_conditions = request.POST.get('chronic_conditions', '')  # chronic conditions
        patient.address = request.POST.get('address', '')  # home address
        patient.emergency_contact_name = request.POST.get('emergency_contact_name', '')  # emergency contact name
        patient.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')  # emergency contact phone
        patient.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', '')  # relationship
        patient.insurance_provider = request.POST.get('insurance_provider', '')  # insurance provider
        patient.insurance_number = request.POST.get('insurance_number', '')  # insurance policy number
        patient.insurance_expiry = request.POST.get('insurance_expiry') or None  # insurance expiry date
        patient.status = request.POST.get('status', 'active')  # patient status
        patient.save()  # write the changes to the database

        # show a success banner
        messages.success(request, f'Patient "{patient.user.get_full_name()}" updated successfully.')
        # go back to the patient list page
        return redirect('patient_user_list')

    # show the edit patient page
    return render(request, 'dashboard/patient_management/patient_edit.html', {
        'form': form, 'patient_user': patient_user, 'profile': profile, 'patient': patient,
    })


@login_required
def patient_detail(request, patient_id):
    # find the patient, or show a 404 page if they don't exist, loading related rows in one query
    patient = get_object_or_404(
        PatientProfile.objects.select_related('user', 'user__profile'), pk=patient_id
    )
    # show the patient detail page
    return render(request, 'dashboard/patient_management/patient_detail.html', {'patient': patient})


@login_required
def patient_delete(request, patient_id):
    # find the patient we want to delete, or show a 404 page if they don't exist
    patient = get_object_or_404(PatientProfile, pk=patient_id)
    if request.method == 'POST':
        # remember their name before we delete the row
        name = patient.user.get_full_name()
        # delete the login account (this also deletes the patient profile because of on_delete=CASCADE)
        patient.user.delete()
        # show a success banner
        messages.success(request, f'Patient "{name}" deleted successfully.')
        # go back to the patient list page
        return redirect('patient_user_list')
    # not a POST request, so just go back to the list without deleting anything
    return redirect('patient_user_list')


# ── Staff Management ──────────────────────────────────────────────────────────

@login_required
def staff_user_list(request):
    # get every staff profile, plus their linked User and StaffProfile rows, in one query
    profiles = UserProfile.objects.select_related('user', 'user__staff_profile').filter(role__in=STAFF_ROLES)
    # show the list page
    return render(request, 'dashboard/staff_management/staff_list.html', {'profiles': profiles})


@login_required
def staff_add(request):
    staff_user = User()  # a blank user, only used so the template can show default field values
    profile = UserProfile()  # a blank profile, only used so the template can show default field values
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = StaffCreateForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # step 1: create the login account (User model)
        staff_user = User.objects.create_user(
            username=request.POST.get('username', ''),  # login name
            email=request.POST.get('email', ''),  # email address
            password=request.POST.get('password', ''),  # password (Django hashes this for us)
            first_name=request.POST.get('first_name', ''),  # first name
            last_name=request.POST.get('last_name', ''),  # last name
            is_active=request.POST.get('is_active') == 'on',  # can they log in
        )
        # step 2: create their profile row with the staff role they picked
        UserProfile.objects.create(
            user=staff_user,  # link back to the User we just made
            phone=request.POST.get('phone', ''),  # phone number
            date_of_birth=request.POST.get('date_of_birth') or None,  # date of birth
            gender=request.POST.get('gender', ''),  # gender
            role=request.POST.get('role', ''),  # staff role (admin, doctor, nurse, etc)
        )
        # step 3: create their employment record (department, shift, etc all start blank,
        # the staff member fills these in later by editing their own record)
        StaffProfile.objects.create(user=staff_user)
        send_staff_welcome_email(staff_user, request.POST.get('role', ''))  # email the new staff member their username
        # show a success banner
        messages.success(request, f'Staff member "{staff_user.get_full_name()}" added successfully.')
        # go back to the staff list page
        return redirect('staff_user_list')

    # show the add staff page
    return render(request, 'dashboard/staff_management/staff_add.html', {
        'form': form, 'staff_user': staff_user, 'profile': profile, 'role_choices': STAFF_ROLE_CHOICES,
    })


@login_required
def staff_edit(request, user_id):
    # find the staff member we want to edit, or show a 404 page if they don't exist
    staff_user = get_object_or_404(User, pk=user_id)
    # this user's basic profile (phone, role, etc)
    profile = staff_user.profile
    # this user's employment details, if they already have one
    staff_profile = getattr(staff_user, 'staff_profile', None) or StaffProfile()

    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = StaffEditForm(request.POST or None, current_user=staff_user)

    if request.method == 'POST' and form.is_valid():
        # update the login account fields
        staff_user.first_name = request.POST.get('first_name', '')  # first name
        staff_user.last_name = request.POST.get('last_name', '')  # last name
        staff_user.email = request.POST.get('email', '')  # email address
        staff_user.username = request.POST.get('username', '')  # login name
        staff_user.is_active = request.POST.get('is_active') == 'on'  # can they log in
        staff_user.save()  # write the changes to the database

        # update the basic profile fields
        profile.phone = request.POST.get('phone', '')  # phone number
        profile.date_of_birth = request.POST.get('date_of_birth') or None  # date of birth
        profile.gender = request.POST.get('gender', '')  # gender
        profile.role = request.POST.get('role', '')  # staff role
        profile.save()  # write the changes to the database

        # this person is now staff, so remove any old patient record they might still
        # have (e.g. if they were first registered through "Register Patient" and are
        # only now being made staff) - a person cannot be both at the same time
        PatientProfile.objects.filter(user=staff_user).delete()

        # get their employment record, or make a new one if they don't have one yet
        staff_profile, _created = StaffProfile.objects.get_or_create(user=staff_user)
        # update the employment fields
        staff_profile.department = request.POST.get('department', '')  # department
        staff_profile.specialization = request.POST.get('specialization', '')  # specialization
        staff_profile.qualification = request.POST.get('qualification', '')  # qualification
        staff_profile.license_number = request.POST.get('license_number', '')  # license number
        staff_profile.hire_date = request.POST.get('hire_date') or None  # hire date
        staff_profile.employment_type = request.POST.get('employment_type', '')  # employment type
        staff_profile.shift = request.POST.get('shift', '')  # shift
        staff_profile.hourly_fee = request.POST.get('hourly_fee') or 0  # consultation fee (doctors only)
        staff_profile.emergency_contact_name = request.POST.get('emergency_contact_name', '')  # emergency contact name
        staff_profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')  # emergency contact phone
        staff_profile.save()  # write the changes to the database

        # show a success banner
        messages.success(request, f'Staff "{staff_user.get_full_name()}" updated successfully.')
        # go back to the staff list page
        return redirect('staff_user_list')

    # show the edit staff page
    return render(request, 'dashboard/staff_management/staff_edit.html', {
        'form': form, 'staff_user': staff_user, 'profile': profile, 'staff_profile': staff_profile,
        'role_choices': STAFF_ROLE_CHOICES,
    })


@login_required
def staff_detail(request, user_id):
    # find the staff member, or show a 404 page if they don't exist
    staff_user = get_object_or_404(User, pk=user_id)
    # find their profile, or show a 404 page if it's missing
    profile = get_object_or_404(UserProfile, user=staff_user)
    # find their employment details, if they have any
    try:
        sp = staff_user.staff_profile
    except StaffProfile.DoesNotExist:
        sp = None
    # show the staff detail page
    return render(request, 'dashboard/staff_management/staff_detail.html', {
        'staff_user': staff_user,
        'profile': profile,
        'sp': sp,
    })


@login_required
def staff_delete(request, user_id):
    # find the staff member we want to delete, or show a 404 page if they don't exist
    staff_user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        # remember their name before we delete the row
        name = staff_user.get_full_name()
        # delete the login account (this also deletes their profile because of on_delete=CASCADE)
        staff_user.delete()
        # show a success banner
        messages.success(request, f'Staff member "{name}" deleted successfully.')
        # go back to the staff list page
        return redirect('staff_user_list')
    # not a POST request, so just go back to the list without deleting anything
    return redirect('staff_user_list')


# ── Doctor Rooms ──────────────────────────────────────────────────────────────

@login_required
def doctor_room_list(request):
    # only reception/admin staff may assign doctor rooms
    if not _is_room_staff(request.user):
        messages.error(request, 'You do not have permission to manage doctor rooms.')
        return redirect('dashboard_index')

    # every active doctor, ordered by name
    doctors = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')

    if request.method == 'POST':
        # go through every doctor and read the room number typed for them
        for doctor in doctors:
            room_number = request.POST.get(f'room_{doctor.pk}', '').strip()  # room typed in for this doctor's row
            staff_profile, _created = StaffProfile.objects.get_or_create(user=doctor)
            staff_profile.room_number = room_number
            staff_profile.save()
        messages.success(request, 'Doctor room numbers have been updated.')
        return redirect('doctor_room_list')

    # each doctor with their current room number, so the form can show existing values
    doctor_rows = []
    for doctor in doctors:
        try:
            room_number = doctor.staff_profile.room_number
        except StaffProfile.DoesNotExist:
            room_number = ''
        doctor_rows.append({'doctor': doctor, 'room_number': room_number})

    return render(request, 'dashboard/staff_management/doctor_rooms.html', {'doctor_rows': doctor_rows})
