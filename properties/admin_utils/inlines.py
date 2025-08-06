from django.contrib import admin

from properties.models import (
    CommunicationMethod,
    PmsDataProperty,
    PropertyImage,
    RoomType,
    RoomTypeImage,
    TermsAndConditions,
)


class TermsAndConditionsInline(admin.StackedInline):
    model = TermsAndConditions
    extra = 1


class CommunicationMethodInline(admin.TabularInline):
    model = CommunicationMethod
    extra = 1


class PMSDataInline(admin.StackedInline):
    model = PmsDataProperty
    extra = 1
    can_delete = False

    readonly_fields = [
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


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class RoomTypeImageInline(admin.TabularInline):
    model = RoomTypeImage
    extra = 1


class RoomTypeInline(admin.StackedInline):
    model = RoomType
    extra = 1
    show_change_link = True
    inlines = [RoomTypeImageInline]
