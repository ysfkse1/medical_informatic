from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("patient/login/", views.patient_login, name="patient_login"),
    path("patient/signup/", views.patient_signup, name="patient_signup"),
    path("patient/dashboard/", views.patient_dashboard, name="patient_dashboard"),
    path("patient/profile/", views.patient_profile, name="patient_profile"),
    path("patient/intake/", views.patient_intake, name="patient_intake"),
    path("patient/get-slots/<int:doctor_id>/", views.get_available_slots, name="get_available_slots"),
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/<int:doctor_id>/", views.doctor_detail, name="doctor_detail"),
    path("doctors/manage-slots/", views.doctor_manage_slots, name="doctor_manage_slots"),
    path("doctors/profile/", views.doctor_profile, name="doctor_profile"),
    path("appointments/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("prescriptions/<int:pk>/edit/", views.edit_prescription, name="edit_prescription"),
    path("prescriptions/<int:pk>/delete/", views.delete_prescription, name="delete_prescription"),
    path("change-language/", views.change_language, name="change_language"),
]
