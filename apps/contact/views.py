from django.shortcuts import render, redirect
from django.contrib import messages  # shows a flash message after the form saves
from apps.contact.ContactForm import ContactForm
from .models import Contact_us

#frontend start 
def contact_us_index(request):
    form = ContactForm()
    return render(request, "frontend/core/contact_us_index.html", {"form": form})


def add_contact(request):
    form = ContactForm(request.POST)

    if form.is_valid():
        Contact_us.objects.create(
            name=request.POST.get("name", ""),
            email=request.POST.get("email", ""),
            subject=request.POST.get("subject", ""),
            message=request.POST.get("message", ""),
            created_date=request.POST.get("created_date", None)
        )
        messages.success(request, "Your message has been sent. Thank you!")
        return redirect("contact_us_index")

    else:
        messages.error(request, "Please fix the errors below and try again.")
        return render(request, "frontend/core/contact_us_index.html", {"form": form})

    

#dash board start

def view_inquiries(request):
    inquiries = Contact_us.objects.all()
    return render(request, "dashboard/contact_us/list_inquiries.html", {"inquiries": inquiries})

def view_inquiry(request, id):
    inquiry = Contact_us.objects.get(id=id)
    return render(request, "dashboard/contact_us/view_inquiry.html", {"inquiry": inquiry})


