from django.shortcuts import render
from apps.contact.ContactForm import ContactForm
from .models import Contact_us
from django.shortcuts import redirect
from pprint import pprint 



def contact_us_index(request):
    form = ContactForm()
    return render(request, "frontend/core/contact_us_index.html" , {"form": form})


def add_contact(request):
    pprint(request.POST.dict())

    form = ContactForm(request.POST)

    if form.is_valid():
          print("FORM IS VALID")

          Contact_us.objects.create(
               name=request.POST.get("name", ""),
               email=request.POST.get("email", ""),
               subject=request.POST.get("subject", ""),
               message=request.POST.get("message", ""),
               created_date=request.POST.get("created_date", None)
          )
          print("FORM IS VALID before redi")
          return redirect("contact_us_index")
          print("FORM IS VALID after redi")

    else:
        print("FORM IS INVALID")
        print(form.errors)

        return render(request,"frontend/core/contact_us_index.html",{"form": form})
    

     
          
              
     
