from django import forms

from .models import CommunicationMethod, Property, PropertyImage, PmsDataProperty


class PropertyStepForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            "name",
            "description",
            "address",
            "location",
            "cover_image",
            "pms",
            "use_pms_information",
        ]


class PmsDataForm(forms.ModelForm):
    class Meta:
        model = PmsDataProperty
        exclude = [
            "property",
            "first_sync",
            "pms_property_id",
            "pms_property_name",
            "pms_property_address",
            "pms_property_city",
            "pms_property_province",
            "pms_property_postal_code",
            "pms_property_country",
            "pms_property_latitude",
            "pms_property_longitude",
            "pms_property_phone",
            "pms_property_category",
        ]


class MultipleFileInput(forms.ClearableFileInput):
    """Allow selecting multiple files in admin forms."""

    allow_multiple_selected = True


class PropertyImagesForm(forms.Form):
    images = forms.ImageField(
        widget=MultipleFileInput(attrs={"multiple": True}),
        required=False,
    )


class CommunicationForm(forms.Form):
    name = forms.CharField()
    value = forms.CharField()


CommunicationFormSet = forms.formset_factory(CommunicationForm, extra=1)
