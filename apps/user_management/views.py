from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserCreateForm, UserEditForm, PatientCreateForm, PatientEditForm, StaffEditForm
from .models import UserProfile, PatientProfile, StaffProfile

STAFF_ROLES = ['admin', 'doctor', 'nurse', 'receptionist', 'pharmacist', 'lab_technician']

# roles allowed to assign a room to each doctor
ROOM_STAFF_ROLES = ('admin', 'receptionist')


def _is_room_staff(user):
    # true only for logged in users whose profile role can assign doctor rooms
    return hasattr(user, 'profile') and user.profile.role in ROOM_STAFF_ROLES


# ── General User Management ───────────────────────────────────────────────────

@login_required
def user_list(request):
    profiles = UserProfile.objects.select_related('user').all()
    return render(request, 'dashboard/user_management/user_list.html', {'profiles': profiles})


@login_required
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" created successfully.')
            return redirect('user_list')
    else:
        form = UserCreateForm()
    return render(request, 'dashboard/user_management/user_add.html', {'form': form})


@login_required
def user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User "{user.username}" updated successfully.')
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user)
    return render(request, 'dashboard/user_management/user_edit.html', {'form': form, 'edit_user': user})


@login_required
def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('user_list')
    return redirect('user_list')


# ── Patient Management ────────────────────────────────────────────────────────

@login_required
def patient_user_list(request):
    # only show users whose current role is "patient"
    # this stops old patients from showing here after their role gets changed (e.g. to pharmacist)
    patients = PatientProfile.objects.select_related('user', 'user__profile').filter(user__profile__role='patient')
    return render(request, 'dashboard/patient_management/patient_list.html', {'patients': patients})


@login_required
def patient_add(request):
    if request.method == 'POST':
        form = PatientCreateForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f'Patient "{patient.user.get_full_name()}" (MRN: {patient.mrn}) registered successfully.')
            return redirect('patient_user_list')
    else:
        form = PatientCreateForm()
    return render(request, 'dashboard/patient_management/patient_add.html', {'form': form})


@login_required
def patient_edit(request, patient_id):
    patient = get_object_or_404(PatientProfile, pk=patient_id)
    if request.method == 'POST':
        form = PatientEditForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Patient "{patient.user.get_full_name()}" updated successfully.')
            return redirect('patient_user_list')
    else:
        form = PatientEditForm(instance=patient)
    return render(request, 'dashboard/patient_management/patient_edit.html', {'form': form, 'patient': patient})


@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(
        PatientProfile.objects.select_related('user', 'user__profile'), pk=patient_id
    )
    return render(request, 'dashboard/patient_management/patient_detail.html', {'patient': patient})


@login_required
def patient_delete(request, patient_id):
    patient = get_object_or_404(PatientProfile, pk=patient_id)
    if request.method == 'POST':
        name = patient.user.get_full_name()
        patient.user.delete()
        messages.success(request, f'Patient "{name}" deleted successfully.')
        return redirect('patient_user_list')
    return redirect('patient_user_list')


# ── Staff Management ──────────────────────────────────────────────────────────

@login_required
def staff_user_list(request):
    profiles = UserProfile.objects.select_related('user', 'staff_profile').filter(role__in=STAFF_ROLES)
    return render(request, 'dashboard/staff_management/staff_list.html', {'profiles': profiles})


@login_required
def staff_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = StaffEditForm(request.POST, user_instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Staff "{user.get_full_name()}" updated successfully.')
            return redirect('staff_user_list')
    else:
        form = StaffEditForm(user_instance=user)
    return render(request, 'dashboard/staff_management/staff_edit.html', {'form': form, 'staff_user': user})


@login_required
def staff_detail(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    profile = get_object_or_404(UserProfile, user=user)
    try:
        sp = profile.staff_profile
    except StaffProfile.DoesNotExist:
        sp = None
    return render(request, 'dashboard/staff_management/staff_detail.html', {
        'staff_user': user,
        'profile': profile,
        'sp': sp,
    })


# ── Doctor Rooms ──────────────────────────────────────────────────────────────

@login_required
def doctor_room_list(request):
    # only reception/admin staff may assign doctor rooms
    if not _is_room_staff(request.user):
        messages.error(request, 'You do not have permission to manage doctor rooms.')
        return redirect('dashboard_index')

    doctors = User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name')

    if request.method == 'POST':
        for doctor in doctors:
            room_number = request.POST.get(f'room_{doctor.pk}', '').strip()  # room typed in for this doctor's row
            staff_profile, _created = StaffProfile.objects.get_or_create(user_profile=doctor.profile)
            staff_profile.room_number = room_number
            staff_profile.save()
        messages.success(request, 'Doctor room numbers have been updated.')
        return redirect('doctor_room_list')

    # each doctor with their current room number, so the form can show existing values
    doctor_rows = []
    for doctor in doctors:
        try:
            room_number = doctor.profile.staff_profile.room_number
        except StaffProfile.DoesNotExist:
            room_number = ''
        doctor_rows.append({'doctor': doctor, 'room_number': room_number})

    return render(request, 'dashboard/staff_management/doctor_rooms.html', {'doctor_rows': doctor_rows})
