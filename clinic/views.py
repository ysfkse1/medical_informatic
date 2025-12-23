from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AppointmentRequestForm, PatientIntakeForm, PatientProfileForm, PrescriptionForm
from .models import Appointment, AppointmentSlot, Doctor, Patient
from .utils import analyze_triage, check_drug_interactions, ensure_demo_doctors, default_schedule_time


def home(request):
    ensure_demo_doctors()
    
    # Eğer kullanıcı giriş yapmışsa, rolüne göre yönlendir veya bilgi göster
    if request.user.is_authenticated:
        # Doktor ise doktor paneline yönlendir
        if hasattr(request.user, 'doctor_profile') and request.user.doctor_profile:
            return redirect('doctor_detail', doctor_id=request.user.doctor_profile.id)
        # Hasta ise hasta dashboard'a yönlendir
        elif hasattr(request.user, 'patient_profile') and request.user.patient_profile:
            return redirect('patient_dashboard')
    
    # Giriş yapmamışsa ana sayfayı göster
    doctors = Doctor.objects.all()
    return render(request, "home.html", {"doctors": doctors})


@login_required
def patient_dashboard(request):
    patient = Patient.objects.filter(user=request.user).first()
    appointments = []
    prescriptions = []
    if patient:
        appointments = patient.appointments.select_related("doctor").order_by("-scheduled_for")
        prescriptions = (
            patient.appointments.prefetch_related("prescriptions")
            .order_by("-scheduled_for")
        )
    return render(
        request,
        "patient_dashboard.html",
        {
            "patient": patient,
            "appointments": appointments,
            "prescriptions": prescriptions,
        },
    )


@login_required
def patient_profile(request):
    patient = Patient.objects.filter(user=request.user).first()
    
    if request.method == "POST":
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            messages.success(request, "Profiliniz başarıyla güncellendi.")
            return redirect("patient_profile")
        messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        form = PatientProfileForm(instance=patient)
    
    return render(
        request,
        "patient_profile.html",
        {
            "form": form,
            "patient": patient,
        },
    )


@login_required
def get_available_slots(request, doctor_id):
    """AJAX endpoint: Doktor için müsait slot'ları JSON olarak döndür"""
    from django.http import JsonResponse
    from django.utils import timezone
    from datetime import timedelta
    import pytz
    
    now = timezone.now()
    min_time = now + timedelta(minutes=5)
    
    # Geçmiş slotları kapat
    AppointmentSlot.objects.filter(
        doctor_id=doctor_id,
        is_available=True,
        slot_datetime__lt=now
    ).update(is_available=False)
    
    # Müsait slot'ları getir
    slots = AppointmentSlot.objects.filter(
        doctor_id=doctor_id,
        is_available=True,
        slot_datetime__gte=min_time
    ).order_by('slot_datetime')[:30]
    
    # JSON formatına çevir
    tr_tz = pytz.timezone('Europe/Istanbul')
    slot_list = []
    for slot in slots:
        slot_time_tr = slot.slot_datetime.astimezone(tr_tz)
        label = slot_time_tr.strftime('%d/%m/%Y (%A) - %H:%M')
        label = label.replace('Monday', 'Pazartesi').replace('Tuesday', 'Salı')
        label = label.replace('Wednesday', 'Çarşamba').replace('Thursday', 'Perşembe')
        label = label.replace('Friday', 'Cuma').replace('Saturday', 'Cumartesi')
        label = label.replace('Sunday', 'Pazar')
        slot_list.append({'id': slot.id, 'label': label})
    
    return JsonResponse({'slots': slot_list})


@login_required
def patient_intake(request):
    ensure_demo_doctors()
    patient = Patient.objects.filter(user=request.user).first()
    
    if request.method == "POST":
        patient_form = PatientIntakeForm(request.POST, instance=patient)
        # Form'dan gelen verileri al
        doctor_id = request.POST.get('doctor')
        slot_id = request.POST.get('appointment_slot')
        
        if patient_form.is_valid() and doctor_id and slot_id:
            try:
                doctor = Doctor.objects.get(id=doctor_id)
                slot = AppointmentSlot.objects.get(id=slot_id, doctor=doctor, is_available=True)
            except (Doctor.DoesNotExist, AppointmentSlot.DoesNotExist):
                messages.error(request, "Seçtiğiniz slot artık müsait değil. Lütfen başka bir slot seçin.")
                return render(request, "patient_intake.html", {
                    "patient_form": patient_form,
                    "patient": patient,
                })
            
            scheduled_time = slot.slot_datetime
            
            # Hastanın profil bilgilerini kaydet
            patient = patient_form.save(commit=False)
            patient.user = request.user
            patient.save()
            
            # Triyaj verilerini hazırla
            triage_data = {
                "pain_level": patient_form.cleaned_data.get("pain_level") or 0,
                "temperature": float(patient_form.cleaned_data.get("temperature") or 36.7),
                "heart_rate": patient_form.cleaned_data.get("heart_rate") or 70,
                "symptoms_detail": patient_form.cleaned_data.get("symptoms_detail") or "",
                "complaint_duration": patient_form.cleaned_data.get("complaint_duration") or "",
                "has_breathing_difficulty": patient_form.cleaned_data.get("has_breathing_difficulty") or "",
                "previous_similar_condition": patient_form.cleaned_data.get("previous_similar_condition") or "",
            }
            triage = analyze_triage(patient, triage_data)
            
            # Randevuyu oluştur
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                scheduled_for=scheduled_time,
                ai_summary=triage.summary,
                ai_suggestions=triage.suggestions + triage.possible_conditions,
                risk_level=triage.risk_level,
                triage_data=triage_data,
            )
            
            # Slotu kullanılamaz yap
            slot.is_available = False
            slot.save()
            
            messages.success(
                request,
                f"Randevunuz oluşturuldu: {scheduled_time.strftime('%d/%m/%Y %H:%M')}. Doktor triayj ve AI özetini görecek.",
            )
            return redirect("patient_dashboard")
        else:
            messages.error(request, "Lütfen formdaki hataları düzeltin.")
    else:
        patient_form = PatientIntakeForm(instance=patient)

    return render(
        request,
        "patient_intake.html",
        {
            "patient_form": patient_form,
            "patient": patient,
            "doctors": Doctor.objects.all(),
        },
    )


def doctor_list(request):
    ensure_demo_doctors()
    if request.user.is_authenticated and hasattr(request.user, "doctor_profile"):
        return redirect("doctor_detail", doctor_id=request.user.doctor_profile.id)
    doctors = Doctor.objects.all()
    return render(request, "doctor_list.html", {"doctors": doctors})


@login_required
def doctor_detail(request, doctor_id: int):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    if doctor.user and request.user != doctor.user and not request.user.is_staff:
        messages.error(request, "Bu doktor paneline erişim yetkiniz yok.")
        return redirect("doctor_list")
    
    # Randevu filtreleme
    appointments = doctor.appointments.select_related("patient")
    
    filter_type = request.GET.get("filter", "all")
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    if filter_type == "today":
        # Bugünün randevuları
        today = timezone.now().date()
        appointments = appointments.filter(
            scheduled_for__date=today
        )
    elif filter_type == "week":
        # Bu haftanın randevuları
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        appointments = appointments.filter(
            scheduled_for__date__gte=today,
            scheduled_for__date__lte=week_end
        )
    
    appointments = appointments.order_by("scheduled_for")
    
    return render(
        request,
        "doctor_detail.html",
        {
            "doctor": doctor,
            "appointments": appointments,
        },
    )


@login_required
def appointment_detail(request, pk: int):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor"), pk=pk
    )
    if appointment.doctor.user and request.user != appointment.doctor.user and not request.user.is_staff:
        messages.error(request, "Bu randevuyu görüntüleme yetkiniz yok.")
        return redirect("doctor_list")
    prescriptions = appointment.prescriptions.all()

    if request.method == "POST":
        form = PrescriptionForm(request.POST, doctor=appointment.doctor)
        if form.is_valid():
            prescription = form.save(commit=False)
            prescription.doctor = appointment.doctor
            prescription.appointment = appointment
            alert = check_drug_interactions(
                appointment.patient,
                prescription.medication_name,
                [p.medication_name for p in prescriptions],
            )
            prescription.ai_interaction_alerts = alert
            prescription.save()
            messages.success(request, "Reçete kaydedildi ve AI etkileşim notu eklendi.")
            return redirect("appointment_detail", pk=appointment.pk)
        messages.error(request, "Reçetede hatalar var, lütfen kontrol edin.")
    else:
        form = PrescriptionForm(doctor=appointment.doctor)

    return render(
        request,
        "appointment_detail.html",
        {
            "appointment": appointment,
            "prescriptions": prescriptions,
            "form": form,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("home")


def patient_signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("patient_dashboard")
    else:
        form = UserCreationForm()
    return render(request, "patient_signup.html", {"form": form})


def patient_login(request):
    if request.user.is_authenticated:
        return redirect("patient_dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("patient_dashboard")
        messages.error(request, "Hatalı kullanıcı adı veya şifre.")
    return render(request, "patient_login.html")


@login_required
def doctor_manage_slots(request):
    """Doktorun randevu slotlarını yönettiği sayfa"""
    if not hasattr(request.user, 'doctor_profile'):
        messages.error(request, "Bu sayfaya erişim yetkiniz yok.")
        return redirect('home')
    
    doctor = request.user.doctor_profile
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'generate_slots':
            # Belirli tarih aralığı için slot oluştur
            from datetime import datetime, timedelta
            from django.utils import timezone
            
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')
            
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                
                if start_date < timezone.now().date():
                    messages.error(request, "Başlangıç tarihi geçmişte olamaz.")
                elif end_date < start_date:
                    messages.error(request, "Bitiş tarihi başlangıç tarihinden önce olamaz.")
                else:
                    created_count = 0
                    current_date = start_date
                    
                    while current_date <= end_date:
                        # Bu gün için slotları oluştur
                        day_name = current_date.strftime("%A").lower()
                        
                        if doctor.working_days.get(day_name, False):
                            # Türkiye saatinde datetime oluştur
                            import pytz
                            tr_tz = pytz.timezone('Europe/Istanbul')
                            
                            start_datetime = datetime.combine(current_date, doctor.work_start_time)
                            end_datetime = datetime.combine(current_date, doctor.work_end_time)
                            
                            # Naive datetime'ı Türkiye saati olarak işaretle
                            start_datetime = tr_tz.localize(start_datetime)
                            end_datetime = tr_tz.localize(end_datetime)
                            
                            current_time = start_datetime
                            while current_time < end_datetime:
                                # Zaten var mı kontrol et
                                slot, created = AppointmentSlot.objects.get_or_create(
                                    doctor=doctor,
                                    slot_datetime=current_time,  # Zaten timezone-aware
                                    defaults={'is_available': True}
                                )
                                if created:
                                    created_count += 1
                                
                                current_time += timedelta(minutes=doctor.slot_duration_minutes)
                        
                        current_date += timedelta(days=1)
                    
                    messages.success(request, f"{created_count} yeni randevu slotu oluşturuldu.")
            except ValueError:
                messages.error(request, "Geçersiz tarih formatı.")
        
        elif action == 'toggle_slot':
            slot_id = request.POST.get('slot_id')
            try:
                slot = AppointmentSlot.objects.get(id=slot_id, doctor=doctor)
                slot.is_available = not slot.is_available
                slot.save()
                status = "açıldı" if slot.is_available else "kapatıldı"
                messages.success(request, f"Slot başarıyla {status}.")
            except AppointmentSlot.DoesNotExist:
                messages.error(request, "Slot bulunamadı.")
        
        elif action == 'delete_slot':
            slot_id = request.POST.get('slot_id')
            try:
                slot = AppointmentSlot.objects.get(id=slot_id, doctor=doctor)
                slot.delete()
                messages.success(request, "Slot silindi.")
            except AppointmentSlot.DoesNotExist:
                messages.error(request, "Slot bulunamadı.")
    
    # Gelecekteki slotları getir
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    
    # Geçmiş slotları otomatik kapat
    AppointmentSlot.objects.filter(
        doctor=doctor,
        is_available=True,
        slot_datetime__lt=now
    ).update(is_available=False)
    
    # Sadece gelecekteki slotları göster
    slots = AppointmentSlot.objects.filter(
        doctor=doctor,
        slot_datetime__gte=now
    ).order_by('slot_datetime')[:50]  # İlk 50 slot
    
    return render(request, "doctor_manage_slots.html", {
        "doctor": doctor,
        "slots": slots,
    })
