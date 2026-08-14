from django.shortcuts import render, redirect, get_object_or_404  # helpers to render pages and redirect
from django.contrib import messages  # shows a flash message after the form saves
from .forms import ContactForm  # our form
from .models import Contact_us  # our model


# ── Frontend ───────────────────────────────────────────────────────────────

def contact_us_index(request):
    form = ContactForm()  # blank form, used only to check the data typed on this page
    return render(request, 'frontend/core/contact_us_index.html', {'form': form})


def add_contact(request):
    # form is only used to check the typed data is valid; the actual save is done by hand below
    form = ContactForm(request.POST)

    if form.is_valid():
        inquiry = Contact_us()  # a blank inquiry
        inquiry.name = request.POST.get('name', '')  # name of the sender
        inquiry.email = request.POST.get('email', '')  # email to reply to
        inquiry.subject = request.POST.get('subject', '')  # subject line
        inquiry.message = request.POST.get('message', '')  # the message itself
        inquiry.save()  # write the new inquiry to the database
        messages.success(request, 'Your message has been sent. Thank you!')
        return redirect('contact_us_index')

    messages.error(request, 'Please fix the errors below and try again.')
    return render(request, 'frontend/core/contact_us_index.html', {'form': form})


# ── Dashboard ────────────────────────────────────────────────────────────────

def view_inquiries(request):
    inquiries = Contact_us.objects.all()  # every message sent through the contact form
    return render(request, 'dashboard/contact_us/list_inquiries.html', {'inquiries': inquiries})


def view_inquiry(request, id):
    inquiry = get_object_or_404(Contact_us, id=id)  # find the message or show a 404 page
    return render(request, 'dashboard/contact_us/view_inquiry.html', {'inquiry': inquiry})
