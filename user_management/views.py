from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserCreateForm, UserEditForm
from .models import UserProfile


def user_list(request):
    profiles = UserProfile.objects.select_related('user').all()
    return render(request, 'dashboard/user_management/user_list.html', {'profiles': profiles})


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


def user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully.')
        return redirect('user_list')
    return redirect('user_list')