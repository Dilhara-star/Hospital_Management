from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserCreateForm, UserEditForm
from .models import UserProfile
from django.http import JsonResponse
from django.http import HttpResponse
import pprint


@login_required
def user_list(request):
    profiles = UserProfile.objects.select_related('user').all()
    # you can read all the profiles and return them as JSON or render them in a template
    # data = list(profiles.values())
    # return HttpResponse(f'<pre>{pprint.pformat(data)}</pre>')
    return render(request, 'dashboard/user_management/user_list.html', {'profiles': profiles})

@login_required
def staff_user_list(request):
    profiles = UserProfile.objects.select_related('user').filter(role='admin')
    return render(request, 'dashboard/user_management/user_list.html', {'profiles': profiles})

@login_required
def patient_user_list(request):
    profiles = UserProfile.objects.select_related('user').filter(role='user')
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
    # URL එකෙන් ආපු user_id use කරලා database එකෙන් user object එක ගන්නවා, නැත්නම් 404 error එකක් දෙනවා
    user = get_object_or_404(User, pk=user_id)

    # request method POST ද කියලා check කරනවා - form submit කළාද?
    if request.method == 'POST':
        # POST data සහ edit කරන user instance එකත් එකට form එකට දෙනවා
        form = UserEditForm(request.POST, instance=user)
        # form data valid ද කියලා check කරනවා
        if form.is_valid():
            # valid නම් user සහ profile database එකේ update කරනවා
            form.save()
            # සාර්ථකව update වුණා කියලා success message එකක් show කරනවා
            messages.success(request, f'User "{user.username}" updated successfully.')
            # user list page එකට redirect කරනවා
            return redirect('user_list')
    else:
        # GET request නම් instance එකෙන් form fields auto-populate කරනවා
        form = UserEditForm(instance=user)

    # form සහ edit_user template එකට pass කරලා render කරනවා
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