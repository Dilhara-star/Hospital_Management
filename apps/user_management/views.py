from django.shortcuts import render, redirect, get_object_or_404  # helpers for rendering pages and redirecting
from django.contrib import messages  # lets us show "success"/"error" banners after an action
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in
from django.contrib.auth.models import User  # built-in user model (login, username, password)
from .forms import PatientCreateForm, PatientEditForm, StaffCreateForm, StaffEditForm  # our forms
from .models import UserProfile, PatientProfile, StaffProfile  # our own profile models

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
    if request.method == 'POST':
        # user submitted the form, so check the data they typed
        form = PatientCreateForm(request.POST)
        if form.is_valid():
            # data passed all checks, pull it out of the form
            data = form.cleaned_data
            # step 1: create the login account (User model)
            user = User.objects.create_user(
                username=data['username'],  # login name
                email=data['email'],  # email address
                password=data['password'],  # password (Django hashes this for us)
                first_name=data['first_name'],  # first name
                last_name=data['last_name'],  # last name
                is_active=data.get('is_active', True),  # can they log in
            )
            # step 2: create their profile row, always with role "patient"
            UserProfile.objects.create(
                user=user,  # link back to the User we just made
                phone=data.get('phone', ''),  # phone number
                date_of_birth=data.get('date_of_birth'),  # date of birth
                gender=data.get('gender', ''),  # gender
                role='patient',  # this form always makes patients
            )
            # step 3: create the patient's medical/insurance record
            patient = PatientProfile.objects.create(
                user=user,  # link back to the User we just made
                blood_type=data.get('blood_type', ''),  # blood type
                allergies=data.get('allergies', ''),  # known allergies
                chronic_conditions=data.get('chronic_conditions', ''),  # chronic conditions
                address=data.get('address', ''),  # home address
                emergency_contact_name=data.get('emergency_contact_name', ''),  # emergency contact name
                emergency_contact_phone=data.get('emergency_contact_phone', ''),  # emergency contact phone
                emergency_contact_relationship=data.get('emergency_contact_relationship', ''),  # relationship
                insurance_provider=data.get('insurance_provider', ''),  # insurance provider
                insurance_number=data.get('insurance_number', ''),  # insurance policy number
                insurance_expiry=data.get('insurance_expiry'),  # insurance expiry date
                status=data.get('status', 'active'),  # patient status
            )
            # show a success banner with their auto-generated MRN
            messages.success(request, f'Patient "{patient.user.get_full_name()}" (MRN: {patient.mrn}) registered successfully.')
            # go back to the patient list page
            return redirect('patient_user_list')
    else:
        # first time opening the page, show a blank form
        form = PatientCreateForm()
    # show the add patient page
    return render(request, 'dashboard/patient_management/patient_add.html', {'form': form})


@login_required
def patient_edit(request, patient_id):
    # find the patient we want to edit, or show a 404 page if they don't exist
    patient = get_object_or_404(PatientProfile, pk=patient_id)
    # the patient's login account
    user = patient.user
    # the patient's basic profile (phone, gender, etc)
    profile = user.profile

    if request.method == 'POST':
        # user submitted the form, so check the new data
        form = PatientEditForm(request.POST, current_user=user)
        if form.is_valid():
            # data passed all checks, pull it out of the form
            data = form.cleaned_data
            # update the login account fields
            user.first_name = data['first_name']  # first name
            user.last_name = data['last_name']  # last name
            user.email = data['email']  # email address
            user.username = data['username']  # login name
            user.is_active = data.get('is_active', False)  # can they log in
            user.save()  # write the changes to the database

            # update the basic profile fields
            profile.phone = data.get('phone', '')  # phone number
            profile.date_of_birth = data.get('date_of_birth')  # date of birth
            profile.gender = data.get('gender', '')  # gender
            profile.save()  # write the changes to the database

            # update the patient's medical/insurance record
            patient.blood_type = data.get('blood_type', '')  # blood type
            patient.allergies = data.get('allergies', '')  # known allergies
            patient.chronic_conditions = data.get('chronic_conditions', '')  # chronic conditions
            patient.address = data.get('address', '')  # home address
            patient.emergency_contact_name = data.get('emergency_contact_name', '')  # emergency contact name
            patient.emergency_contact_phone = data.get('emergency_contact_phone', '')  # emergency contact phone
            patient.emergency_contact_relationship = data.get('emergency_contact_relationship', '')  # relationship
            patient.insurance_provider = data.get('insurance_provider', '')  # insurance provider
            patient.insurance_number = data.get('insurance_number', '')  # insurance policy number
            patient.insurance_expiry = data.get('insurance_expiry')  # insurance expiry date
            patient.status = data.get('status', 'active')  # patient status
            patient.save()  # write the changes to the database

            # show a success banner
            messages.success(request, f'Patient "{patient.user.get_full_name()}" updated successfully.')
            # go back to the patient list page
            return redirect('patient_user_list')
    else:
        # first time opening the page, fill the form with the current values
        initial_data = {
            'first_name': user.first_name,  # first name
            'last_name': user.last_name,  # last name
            'email': user.email,  # email address
            'username': user.username,  # login name
            'is_active': user.is_active,  # can they log in
            'phone': profile.phone,  # phone number
            'date_of_birth': profile.date_of_birth,  # date of birth
            'gender': profile.gender,  # gender
            'address': patient.address,  # home address
            'blood_type': patient.blood_type,  # blood type
            'allergies': patient.allergies,  # known allergies
            'chronic_conditions': patient.chronic_conditions,  # chronic conditions
            'emergency_contact_name': patient.emergency_contact_name,  # emergency contact name
            'emergency_contact_phone': patient.emergency_contact_phone,  # emergency contact phone
            'emergency_contact_relationship': patient.emergency_contact_relationship,  # relationship
            'insurance_provider': patient.insurance_provider,  # insurance provider
            'insurance_number': patient.insurance_number,  # insurance policy number
            'insurance_expiry': patient.insurance_expiry,  # insurance expiry date
            'status': patient.status,  # patient status
        }
        form = PatientEditForm(initial=initial_data, current_user=user)

    # show the edit patient page
    return render(request, 'dashboard/patient_management/patient_edit.html', {'form': form, 'patient': patient})


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
    if request.method == 'POST':
        # user submitted the form, so check the data they typed
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            # data passed all checks, pull it out of the form
            data = form.cleaned_data
            # step 1: create the login account (User model)
            user = User.objects.create_user(
                username=data['username'],  # login name
                email=data['email'],  # email address
                password=data['password'],  # password (Django hashes this for us)
                first_name=data['first_name'],  # first name
                last_name=data['last_name'],  # last name
                is_active=data.get('is_active', True),  # can they log in
            )
            # step 2: create their profile row with the staff role they picked
            UserProfile.objects.create(
                user=user,  # link back to the User we just made
                phone=data.get('phone', ''),  # phone number
                date_of_birth=data.get('date_of_birth'),  # date of birth
                gender=data.get('gender', ''),  # gender
                role=data['role'],  # staff role (admin, doctor, nurse, etc)
            )
            # step 3: create their employment record (department, shift, etc all start blank,
            # the staff member fills these in later by editing their own record)
            StaffProfile.objects.create(user=user)
            # show a success banner
            messages.success(request, f'Staff member "{user.get_full_name()}" added successfully.')
            # go back to the staff list page
            return redirect('staff_user_list')
    else:
        # first time opening the page, show a blank form
        form = StaffCreateForm()
    # show the add staff page
    return render(request, 'dashboard/staff_management/staff_add.html', {'form': form})


@login_required
def staff_edit(request, user_id):
    # find the staff member we want to edit, or show a 404 page if they don't exist
    user = get_object_or_404(User, pk=user_id)
    # this user's basic profile (phone, role, etc)
    profile = user.profile
    # this user's employment details, if they already have one
    try:
        staff_profile = user.staff_profile
    except StaffProfile.DoesNotExist:
        staff_profile = None

    if request.method == 'POST':
        # user submitted the form, so check the new data
        form = StaffEditForm(request.POST, current_user=user)
        if form.is_valid():
            # data passed all checks, pull it out of the form
            data = form.cleaned_data
            # update the login account fields
            user.first_name = data['first_name']  # first name
            user.last_name = data['last_name']  # last name
            user.email = data['email']  # email address
            user.username = data['username']  # login name
            user.is_active = data.get('is_active', False)  # can they log in
            user.save()  # write the changes to the database

            # update the basic profile fields
            profile.phone = data.get('phone', '')  # phone number
            profile.date_of_birth = data.get('date_of_birth')  # date of birth
            profile.gender = data.get('gender', '')  # gender
            profile.role = data['role']  # staff role
            profile.save()  # write the changes to the database

            # this person is now staff, so remove any old patient record they might still
            # have (e.g. if they were first registered through "Register Patient" and are
            # only now being made staff) - a person cannot be both at the same time
            PatientProfile.objects.filter(user=user).delete()

            # get their employment record, or make a new one if they don't have one yet
            staff_profile, _created = StaffProfile.objects.get_or_create(user=user)
            # update the employment fields
            staff_profile.department = data.get('department', '')  # department
            staff_profile.specialization = data.get('specialization', '')  # specialization
            staff_profile.qualification = data.get('qualification', '')  # qualification
            staff_profile.license_number = data.get('license_number', '')  # license number
            staff_profile.hire_date = data.get('hire_date')  # hire date
            staff_profile.employment_type = data.get('employment_type', '')  # employment type
            staff_profile.shift = data.get('shift', '')  # shift
            staff_profile.hourly_fee = data.get('hourly_fee') or 0  # consultation fee (doctors only)
            staff_profile.emergency_contact_name = data.get('emergency_contact_name', '')  # emergency contact name
            staff_profile.emergency_contact_phone = data.get('emergency_contact_phone', '')  # emergency contact phone
            staff_profile.save()  # write the changes to the database

            # show a success banner
            messages.success(request, f'Staff "{user.get_full_name()}" updated successfully.')
            # go back to the staff list page
            return redirect('staff_user_list')
    else:
        # first time opening the page, fill the form with the current values
        initial_data = {
            'first_name': user.first_name,  # first name
            'last_name': user.last_name,  # last name
            'email': user.email,  # email address
            'username': user.username,  # login name
            'is_active': user.is_active,  # can they log in
            'phone': profile.phone,  # phone number
            'date_of_birth': profile.date_of_birth,  # date of birth
            'gender': profile.gender,  # gender
            'role': profile.role,  # staff role
        }
        if staff_profile:
            # they already have employment details, so pre-fill those fields too
            initial_data.update({
                'department': staff_profile.department,  # department
                'specialization': staff_profile.specialization,  # specialization
                'qualification': staff_profile.qualification,  # qualification
                'license_number': staff_profile.license_number,  # license number
                'hire_date': staff_profile.hire_date,  # hire date
                'employment_type': staff_profile.employment_type,  # employment type
                'shift': staff_profile.shift,  # shift
                'hourly_fee': staff_profile.hourly_fee,  # consultation fee (doctors only)
                'emergency_contact_name': staff_profile.emergency_contact_name,  # emergency contact name
                'emergency_contact_phone': staff_profile.emergency_contact_phone,  # emergency contact phone
            })
        form = StaffEditForm(initial=initial_data, current_user=user)

    # show the edit staff page
    return render(request, 'dashboard/staff_management/staff_edit.html', {'form': form, 'staff_user': user})


@login_required
def staff_detail(request, user_id):
    # find the staff member, or show a 404 page if they don't exist
    user = get_object_or_404(User, pk=user_id)
    # find their profile, or show a 404 page if it's missing
    profile = get_object_or_404(UserProfile, user=user)
    # find their employment details, if they have any
    try:
        sp = user.staff_profile
    except StaffProfile.DoesNotExist:
        sp = None
    # show the staff detail page
    return render(request, 'dashboard/staff_management/staff_detail.html', {
        'staff_user': user,
        'profile': profile,
        'sp': sp,
    })


@login_required
def staff_delete(request, user_id):
    # find the staff member we want to delete, or show a 404 page if they don't exist
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        # remember their name before we delete the row
        name = user.get_full_name()
        # delete the login account (this also deletes their profile because of on_delete=CASCADE)
        user.delete()
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
