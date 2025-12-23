from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Patient(models.Model):
    GENDER_CHOICES = [
        ("female", "Kadın"),
        ("male", "Erkek"),
        ("other", "Diğer"),
    ]

    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="patient_profile")
    full_name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=16, choices=GENDER_CHOICES)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2)
    primary_complaint = models.TextField()
    allergies = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.full_name} ({self.age})"


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile", null=True, blank=True)
    full_name = models.CharField(max_length=255)
    specialty = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    
    # Çalışma saatleri
    work_start_time = models.TimeField(default="09:00", help_text="Çalışma başlangıç saati")
    work_end_time = models.TimeField(default="17:00", help_text="Çalışma bitiş saati")
    slot_duration_minutes = models.IntegerField(default=30, help_text="Randevu süresi (dakika)")
    
    # Çalışma günleri (JSON olarak tutacağız)
    # Örnek: {"monday": true, "tuesday": true, ...}
    working_days = models.JSONField(default=dict, blank=True, help_text="Çalışılan günler")

    def __str__(self) -> str:
        return f"Dr. {self.full_name} - {self.specialty}"
    
    def get_available_slots(self, date):
        """Belirli bir gün için uygun randevu saatlerini döndürür"""
        from datetime import datetime, timedelta
        
        # Çalışma günü kontrolü
        day_name = date.strftime("%A").lower()
        if not self.working_days.get(day_name, True):
            return []
        
        # Başlangıç ve bitiş zamanlarını datetime'a çevir
        start_datetime = datetime.combine(date, self.work_start_time)
        end_datetime = datetime.combine(date, self.work_end_time)
        
        # Slot'ları oluştur
        slots = []
        current_time = start_datetime
        
        while current_time < end_datetime:
            # Bu saatte randevu var mı kontrol et
            has_appointment = self.appointments.filter(
                scheduled_for=current_time,
                status__in=["scheduled", "in_progress"]
            ).exists()
            
            if not has_appointment:
                slots.append(current_time)
            
            current_time += timedelta(minutes=self.slot_duration_minutes)
        
        return slots


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Planlandı"),
        ("in_progress", "Muayene"),
        ("completed", "Tamamlandı"),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    scheduled_for = models.DateTimeField()
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="scheduled")

    triage_data = models.JSONField(default=dict)
    ai_summary = models.TextField(blank=True)
    ai_suggestions = models.JSONField(default=list)
    risk_level = models.CharField(max_length=32, default="Düşük")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.patient.full_name} - {self.doctor.full_name} @ {self.scheduled_for:%Y-%m-%d %H:%M}"


class AppointmentSlot(models.Model):
    """Doktorların açtığı randevu slotları"""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="available_slots")
    slot_datetime = models.DateTimeField(unique=True, help_text="Randevu slot zamanı")
    is_available = models.BooleanField(default=True, help_text="Slot müsait mi?")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['slot_datetime']
        unique_together = [['doctor', 'slot_datetime']]
    
    def __str__(self) -> str:
        status = "Müsait" if self.is_available else "Dolu"
        return f"Dr. {self.doctor.full_name} - {self.slot_datetime:%d/%m/%Y %H:%M} ({status})"


class Prescription(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="prescriptions")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="prescriptions")
    medication_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    ai_interaction_alerts = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.medication_name} for {self.appointment.patient.full_name}"
