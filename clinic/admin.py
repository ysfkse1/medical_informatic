from django.contrib import admin

from .models import Appointment, AppointmentSlot, Doctor, Patient, Prescription


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "age", "gender", "weight_kg", "height_cm", "created_at")
    search_fields = ("full_name", "primary_complaint", "allergies")


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("full_name", "specialty", "email")
    search_fields = ("full_name", "specialty")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "scheduled_for", "risk_level", "status")
    list_filter = ("risk_level", "status", "doctor")
    search_fields = ("patient__full_name",)


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ("doctor", "slot_datetime", "is_available", "created_at")
    list_filter = ("is_available", "doctor")
    search_fields = ("doctor__full_name",)
    date_hierarchy = "slot_datetime"


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("medication_name", "appointment", "doctor", "created_at")
    search_fields = ("medication_name", "doctor__full_name")
