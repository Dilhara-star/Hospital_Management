# form to check a "Contact Us" message is valid; the view saves it by hand
from django import forms
from .models import Contact_us


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact_us  # this form is built from the contact message model
        fields = ['name', 'email', 'subject', 'message']  # fields checked by this form

    # the model itself allows email/subject/message to be blank (for admin use),
    # but the public contact form should always require all four fields
    name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=200, required=True)
    message = forms.CharField(required=True, widget=forms.Textarea)
    # a spam trap: a normal visitor never sees or fills this field in (it's hidden with
    # css in the template, not type="hidden"), but simple spam bots fill in every field
    # they find in the page, so anything typed here means the submission is not human
    website = forms.CharField(required=False)

    # stops a name that is just spaces from being saved
    def clean_name(self):
        # pull the cleaned name value out of the form, with extra spaces removed
        name = self.cleaned_data.get('name', '').strip()
        # stop if nothing is left after removing spaces
        if not name:
            raise forms.ValidationError('Please enter your name.')
        # name is fine
        return name

    # stops a subject that is just spaces, or too short to mean anything
    def clean_subject(self):
        # pull the cleaned subject value out of the form, with extra spaces removed
        subject = self.cleaned_data.get('subject', '').strip()
        # stop if it is missing or too short
        if len(subject) < 3:
            raise forms.ValidationError('Subject must be at least 3 characters long.')
        # subject is fine
        return subject

    # stops a message that is just spaces, too short, or unreasonably long
    def clean_message(self):
        # pull the cleaned message value out of the form, with extra spaces removed
        message = self.cleaned_data.get('message', '').strip()
        # stop if it is missing or too short
        if len(message) < 10:
            raise forms.ValidationError('Message must be at least 10 characters long.')
        # stop if it is unreasonably long
        if len(message) > 2000:
            raise forms.ValidationError('Message must be under 2000 characters long.')
        # message is fine
        return message

    # stops the submission if the hidden spam-trap field was filled in
    def clean_website(self):
        # pull the cleaned website value out of the form
        website = self.cleaned_data.get('website', '')
        # a real visitor never types anything here, so anything here means a bot filled the form in
        if website:
            raise forms.ValidationError('Could not send your message. Please try again.')
        # field was left empty, as expected from a real visitor
        return website
