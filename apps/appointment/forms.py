from datetime import date

from django import forms
from django.contrib.auth.models import User

from .models import Appointment


class DoctorChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.username


class AppointmentForm(forms.ModelForm):
    doctor = DoctorChoiceField(
        queryset=User.objects.filter(profile__role='doctor', is_active=True).order_by('first_name', 'last_name'),
        empty_label='Select Doctor',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    class Meta:
        model = Appointment
        fields = ['department', 'date', 'doctor', 'message']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Additional notes or symptoms (optional)',
            }),
        }

    def clean_date(self):
        appointment_date = self.cleaned_data['date']
        if appointment_date < date.today():
            raise forms.ValidationError('Appointment date cannot be in the past.')
        return appointment_date
