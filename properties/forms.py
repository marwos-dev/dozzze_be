from django import forms
from django.forms import inlineformset_factory

from .models import Property, PmsDataProperty, CommunicationMethod, PropertyImage


class PropertyStepOneForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            "name",
            "description",
            "address",
            "pms",
        ]


class PmsDataForm(forms.ModelForm):
    class Meta:
        model = PmsDataProperty
        fields = [
            "base_url",
            "email",
            "phone_number",
            "pms_token",
            "pms_hotel_identifier",
            "pms_username",
            "pms_password",
        ]


class CommunicationMethodForm(forms.ModelForm):
    class Meta:
        model = CommunicationMethod
        fields = ["name", "value"]


CommunicationMethodFormSet = inlineformset_factory(
    Property, CommunicationMethod, form=CommunicationMethodForm, extra=1
)

PropertyImageFormSet = inlineformset_factory(
    Property, PropertyImage, fields=["image", "caption"], extra=1
)
