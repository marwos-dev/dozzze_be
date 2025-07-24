from django import forms
from django.forms import inlineformset_factory

from .models import Property, PmsDataProperty, CommunicationMethod, PropertyImage


class PropertyStepOneForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    class Meta:
        model = Property
        fields = [
            "name",
            "description",
            "address",
            "pms",
        ]


class PmsDataForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    class Meta:
        model = CommunicationMethod
        fields = ["name", "value"]


CommunicationMethodFormSet = inlineformset_factory(
    Property, CommunicationMethod, form=CommunicationMethodForm, extra=1
)

class PropertyImageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            classes = field.widget.attrs.get("class", "")
            if name == "image":
                field.widget.attrs["class"] = (classes + " form-control-file").strip()
            else:
                field.widget.attrs["class"] = (classes + " form-control").strip()

    class Meta:
        model = PropertyImage
        fields = ["image", "caption"]


PropertyImageFormSet = inlineformset_factory(
    Property, PropertyImage, form=PropertyImageForm, extra=1
)
