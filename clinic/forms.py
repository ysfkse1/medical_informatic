from django import forms

from .models import Appointment, Doctor, Patient, Prescription


class PatientProfileForm(forms.ModelForm):
    """Hasta profil bilgileri için form"""
    class Meta:
        model = Patient
        fields = [
            "full_name",
            "age",
            "gender",
            "weight_kg",
            "height_cm",
            "primary_complaint",
            "allergies",
        ]
        widgets = {
            "primary_complaint": forms.Textarea(attrs={"rows": 2}),
            "allergies": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "full_name": "Ad Soyad",
            "age": "Yaş",
            "gender": "Cinsiyet",
            "weight_kg": "Kilo (kg)",
            "height_cm": "Boy (cm)",
            "primary_complaint": "Ana Şikayet / Kronik Hastalıklar",
            "allergies": "Alerjiler",
        }


class PatientIntakeForm(forms.ModelForm):
    """Triyaj için form - sadece vital bulgular ve semptomlar"""
    # Temel vital bulgular
    pain_level = forms.IntegerField(
        min_value=0,
        max_value=10,
        label="Ağrı Şiddeti (0-10)",
        required=False,
        help_text="0: Ağrı yok, 10: Dayanılmaz ağrı",
    )
    temperature = forms.DecimalField(
        max_digits=4,
        decimal_places=1,
        label="Vücut Isısı (°C)",
        required=False,
        help_text="Normal: 36-37°C",
    )
    heart_rate = forms.IntegerField(
        min_value=30,
        max_value=220,
        label="Nabız (atım/dakika)",
        required=False,
        help_text="Normal: 60-100 atım/dakika",
    )
    
    # Yeni triyaj alanları (README'den)
    complaint_duration = forms.ChoiceField(
        label="Şikayetin Süresi",
        choices=[
            ("", "Seçiniz"),
            ("hours", "Birkaç saat"),
            ("days", "1-3 gün"),
            ("week", "1 hafta"),
            ("weeks", "1-4 hafta"),
            ("months", "1 aydan fazla"),
        ],
        required=False,
    )
    
    has_breathing_difficulty = forms.ChoiceField(
        label="Nefes Darlığı Var mı?",
        choices=[
            ("", "Seçiniz"),
            ("none", "Yok"),
            ("mild", "Hafif (eforla)"),
            ("moderate", "Orta (yürürken)"),
            ("severe", "Şiddetli (dinlenirken de)"),
        ],
        required=False,
    )
    
    previous_similar_condition = forms.ChoiceField(
        label="Daha Önce Benzer Durum Yaşandı mı?",
        choices=[
            ("", "Seçiniz"),
            ("no", "Hayır, ilk kez"),
            ("yes_resolved", "Evet, kendiliğinden geçti"),
            ("yes_treated", "Evet, tedavi ile geçti"),
            ("chronic", "Kronik, sık tekrarlıyor"),
        ],
        required=False,
    )
    
    symptoms_detail = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Ek Semptomlar ve Notlar",
        required=False,
        help_text="Diğer belirtileriniz, ne zaman başladığı, şiddeti vb.",
    )

    class Meta:
        model = Patient
        fields = []  # Triyaj formunda hasta bilgilerini göstermeyeceğiz


class AppointmentRequestForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.all(),
        label="Doktor",
        empty_label="Doktor seçiniz",
    )
    appointment_slot = forms.ChoiceField(
        label="Müsait Randevu Saatleri",
        required=True,
        choices=[],
        help_text="Önce doktor seçiniz, ardından müsait saatlerden birini seçiniz"
    )

    class Meta:
        model = Appointment
        fields = ["doctor"]
    
    def __init__(self, *args, **kwargs):
        doctor_id = kwargs.pop('doctor_id', None)
        super().__init__(*args, **kwargs)
        
        if doctor_id:
            # Seçilen doktorun müsait slotlarını getir
            from .models import AppointmentSlot
            from django.utils import timezone
            from datetime import timedelta
            
            # Şu andan 5 dakika sonrasını al (çok yakın zamanlı randevuları engelle)
            now = timezone.now()
            min_time = now + timedelta(minutes=5)
            
            # Geçmiş slotları otomatik kapat (şu andan önceki tüm slotlar)
            past_slots = AppointmentSlot.objects.filter(
                doctor_id=doctor_id,
                is_available=True,
                slot_datetime__lt=now
            )
            updated_count = past_slots.update(is_available=False)
            
            # Debug için konsola yazdır
            if updated_count > 0:
                print(f"[SLOT DEBUG] {updated_count} geçmiş slot kapatıldı. Şu an: {now}")
            
            # Sadece gelecekteki müsait slotları getir
            slots = AppointmentSlot.objects.filter(
                doctor_id=doctor_id,
                is_available=True,
                slot_datetime__gte=min_time
            ).order_by('slot_datetime')[:30]  # İlk 30 müsait slot
            
            # Debug
            print(f"[SLOT DEBUG] Toplam müsait slot: {slots.count()}, Min time: {min_time}")
            if slots.exists():
                print(f"[SLOT DEBUG] İlk slot: {slots.first().slot_datetime}")
            
            choices = []
            for slot in slots:
                # Türkiye saatine çevir
                import pytz
                tr_tz = pytz.timezone('Europe/Istanbul')
                slot_time_tr = slot.slot_datetime.astimezone(tr_tz)
                
                # Türkçe tarih formatı
                label = slot_time_tr.strftime('%d/%m/%Y (%A) - %H:%M')
                # Günleri Türkçe'ye çevir
                label = label.replace('Monday', 'Pazartesi').replace('Tuesday', 'Salı')
                label = label.replace('Wednesday', 'Çarşamba').replace('Thursday', 'Perşembe')
                label = label.replace('Friday', 'Cuma').replace('Saturday', 'Cumartesi')
                label = label.replace('Sunday', 'Pazar')
                choices.append((slot.id, label))
            
            if choices:
                self.fields['appointment_slot'].choices = [('', 'Saat seçiniz')] + choices
            else:
                self.fields['appointment_slot'].choices = [('', 'Müsait slot bulunamadı')]
                self.fields['appointment_slot'].help_text = "Bu doktor için henüz açık randevu slotu yok veya tüm slotlar geçmiş"


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["medication_name", "dosage", "instructions"]
        widgets = {
            "instructions": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop("doctor", None)
        super().__init__(*args, **kwargs)
        if doctor:
            self.fields["medication_name"].label = f"İlaç (Dr. {doctor.full_name})"
