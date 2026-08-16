from django.shortcuts import render, redirect, get_object_or_404  # helpers to render pages and redirect
from django.contrib import messages  # shows a flash message after the form saves
from django.contrib.auth.decorators import login_required  # blocks a view unless the user is logged in
from .forms import ContactForm  # our form
from .models import Contact_us  # our model
from .notifications import send_contact_inquiry_admin_email, send_contact_resolved_email  # emails for new/solved inquiries
from apps.core.utils import required_role  # decorator that checks the logged in user's profile role


# ── Frontend ───────────────────────────────────────────────────────────────

# shows the public "Contact Us" page with a blank enquiry form
def contact_us_index(request):
    form = ContactForm()  # blank form, used only to check the data typed on this page
    return render(request, 'frontend/core/contact_us_index.html', {'form': form})


# saves a new contact enquiry and emails the admin about it
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
        send_contact_inquiry_admin_email(inquiry)  # let the admin know a new message has arrived
        messages.success(request, 'Your message has been sent. Thank you!')
        return redirect('contact_us_index')

    messages.error(request, 'Please fix the errors below and try again.')
    return render(request, 'frontend/core/contact_us_index.html', {'form': form})


# ── Dashboard ────────────────────────────────────────────────────────────────

# lists every "Contact Us" message sent by the public
@login_required
@required_role(['admin'], 'You do not have permission to view contact inquiries.')
def view_inquiries(request):
    inquiries = Contact_us.objects.all()  # every message sent through the contact form
    return render(request, 'dashboard/contact_us/list_inquiries.html', {'inquiries': inquiries})


# shows one "Contact Us" message's full details to an admin
@login_required
@required_role(['admin'], 'You do not have permission to view contact inquiries.')
def view_inquiry(request, id):
    inquiry = get_object_or_404(Contact_us, id=id)  # find the message or show a 404 page
    return render(request, 'dashboard/contact_us/view_inquiry.html', {'inquiry': inquiry})


# lets an admin mark a "Contact Us" message as solved, then emails the sender to let them know
@login_required
@required_role(['admin'], 'You do not have permission to update contact inquiries.')
def mark_inquiry_solved(request, id):
    inquiry = get_object_or_404(Contact_us, id=id)  # find the message or show a 404 page
    if request.method == 'POST':
        # only update when the button is actually clicked, not on a plain page visit
        inquiry.status = 'solved'  # mark this inquiry as solved
        inquiry.save()  # write the change to the database
        send_contact_resolved_email(inquiry)  # let the sender know their message was resolved
        messages.success(request, 'Inquiry marked as solved.')
    return redirect('view_inquiries')
