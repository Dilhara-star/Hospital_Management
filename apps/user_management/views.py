from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserCreateForm, UserEditForm, PatientCreateForm, PatientEditForm, StaffEditForm
from .models import UserProfile, PatientProfile, StaffProfile

STAFF_ROLES = ['admin', 'doctor', 'nurse', 'receptionist', 'pharmacist', 'lab_technician']


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
    patients = PatientProfile.objects.select_related('user', 'user__profile').all()
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
