from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Sequence

from django.conf import settings
from django.utils import timezone

from django.contrib.auth import get_user_model
from django.utils.text import slugify

from .models import Appointment, Doctor, Patient

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None


@dataclass
class TriageAnalysis:
    summary: str
    risk_level: str
    suggestions: List[str]
    possible_conditions: List[str]


def analyze_triage(patient: Patient, triage_data: Dict) -> TriageAnalysis:
    ai_result = _analyze_triage_ai(patient, triage_data)
    if ai_result:
        return ai_result

    # Temel vital bulgular
    temperature = float(triage_data.get("temperature", 36.7))
    pain = int(triage_data.get("pain_level", 0))
    heart_rate = int(triage_data.get("heart_rate", 70))
    symptoms_detail = triage_data.get("symptoms_detail") or ""
    complaint = patient.primary_complaint.lower()
    
    # Yeni triyaj alanları
    complaint_duration = triage_data.get("complaint_duration", "")
    breathing_difficulty = triage_data.get("has_breathing_difficulty", "")
    previous_condition = triage_data.get("previous_similar_condition", "")

    suggestions: List[str] = []
    possible_conditions: List[str] = []
    risk_level = "Düşük"

    # Vital bulgu analizi
    if temperature >= 38.5:
        risk_level = "Orta"
        suggestions.append("Yüksek ateş için enfeksiyon taraması yapın.")
        possible_conditions.append("Enfeksiyon / Viral hastalık")
    if pain >= 7:
        risk_level = "Orta"
        suggestions.append("Şiddetli ağrı için ağrı yönetimi planı düşünün.")
    if heart_rate > 110:
        risk_level = "Yüksek"
        suggestions.append("Yüksek nabız için kardiyak değerlendirme ekleyin.")
        possible_conditions.append("Taşikardi / Kardiyak stres")
    
    # Şikayet süresi analizi
    if complaint_duration in ["months", "weeks"]:
        suggestions.append("Kronik şikayet - detaylı tetkik ve takip gerekli.")
        possible_conditions.append("Kronik durum / Sistemik hastalık şüphesi")
    elif complaint_duration == "hours":
        risk_level = "Yüksek" if risk_level != "Yüksek" else risk_level
        suggestions.append("Akut başlangıç - acil değerlendirme öncelikli.")
    
    # Nefes darlığı analizi
    if breathing_difficulty in ["severe", "moderate"]:
        risk_level = "Yüksek"
        suggestions.append("ACİL: Nefes darlığı mevcut - oksijen satürasyonu ve solunum fonksiyonları değerlendirilmeli.")
        possible_conditions.append("Solunum yetmezliği / Astım / KOAH / Pnömoni")
    elif breathing_difficulty == "mild":
        risk_level = "Orta" if risk_level == "Düşük" else risk_level
        suggestions.append("Hafif nefes darlığı - solunum sistemi muayenesi önerilir.")
    
    # Geçmiş durum analizi
    if previous_condition == "chronic":
        suggestions.append("Tekrarlayan kronik durum - uzun dönem takip planı yapılmalı.")
        possible_conditions.append("Kronik tekrarlayan hastalık")
    elif previous_condition == "no":
        suggestions.append("İlk kez görülüyor - kapsamlı inceleme gerekli.")
    
    # Şikayet içerik analizi
    if any(k in complaint for k in ["göğüs", "nefes", "solunum"]):
        risk_level = "Yüksek"
        possible_conditions.append("Solunum / Kardiyak problemi")
        suggestions.append("ACİL: EKG ve göğüs radyografisi yapılmalı.")
    
    if any(k in complaint for k in ["baş ağrı", "başım", "migren"]):
        possible_conditions.append("Migren / Tansiyon / Nörolojik durum")
        suggestions.append("Baş ağrısı için nörolojik muayene ve kan basıncı kontrolü.")
    
    # Alerji kontrolü
    if "alerji" in symptoms_detail.lower() or patient.allergies:
        suggestions.append("UYARI: İlaç alerjilerini gözden geçirin ve dokümante edin.")

    # Özet oluşturma
    summary = (
        f"{patient.full_name} ({patient.age} yaş, {patient.gender}) için triyaj özeti:\n"
        f"• Vital bulgular: Ateş {temperature}°C, nabız {heart_rate} atım/dk, ağrı {pain}/10\n"
        f"• Ana şikayet: {patient.primary_complaint}"
    )
    
    if complaint_duration:
        duration_map = {
            "hours": "Birkaç saat",
            "days": "1-3 gün",
            "week": "1 hafta",
            "weeks": "1-4 hafta",
            "months": "1 aydan fazla"
        }
        summary += f"\n• Şikayet süresi: {duration_map.get(complaint_duration, 'Belirtilmedi')}"
    
    if breathing_difficulty and breathing_difficulty != "none":
        breath_map = {
            "mild": "Hafif (eforla)",
            "moderate": "Orta (yürürken)",
            "severe": "Şiddetli (dinlenirken de)"
        }
        summary += f"\n• Nefes darlığı: {breath_map.get(breathing_difficulty, 'Var')}"
    
    if symptoms_detail:
        summary += f"\n• Ek semptomlar: {symptoms_detail}"

    return TriageAnalysis(
        summary=summary,
        risk_level=risk_level,
        suggestions=suggestions or ["Standart muayene ve vital kontrolü önerilir."],
        possible_conditions=possible_conditions or ["Durum değerlendirmesi klinik muayene ile netleştirilmeli."],
    )


def check_drug_interactions(
    patient: Patient,
    medication_name: str,
    existing: Sequence[str],
) -> str:
    ai_result = _check_drug_interactions_ai(patient, medication_name, existing)
    if ai_result:
        return ai_result

    med = medication_name.lower()
    interactions = []

    if "ibuprofen" in med or "naproksen" in med:
        interactions.append("NSAID kullanımı böbrek fonksiyonlarını etkileyebilir; hidrasyon ve böbrek fonksiyonlarını izleyin.")
    if "aspirin" in med and ("ibuprofen" in " ".join(existing).lower()):
        interactions.append("Aspirin ve ibuprofen birlikte kullanımı kanama riskini artırabilir.")
    if patient.age >= 65:
        interactions.append("65+ yaş için ilaç dozu ve yan etkilere dikkat edin.")
    if patient.allergies:
        interactions.append(f"Bilinen alerjiler: {patient.allergies}; ilaç içeriğini doğrulayın.")

    if not interactions:
        return "Belirgin etkileşim uyarısı yok. Klinik değerlendirme ile onaylayın."

    return " | ".join(interactions)


def ensure_demo_doctors():
    User = get_user_model()
    from datetime import time
    demos = [
        ("ayse", "Ayşe Kaya", "Dahiliye"),
        ("mehmet", "Mehmet Demir", "Kardiyoloji"),
        ("selin", "Selin Acar", "Acil Tıp"),
    ]
    if not Doctor.objects.exists():
        for username, full_name, specialty in demos:
            user, _ = User.objects.get_or_create(username=username)
            if not user.has_usable_password():
                user.set_password("doktor123")
                user.save()
            Doctor.objects.create(
                user=user, 
                full_name=full_name, 
                specialty=specialty,
                work_start_time=time(9, 0),  # 09:00
                work_end_time=time(17, 0),  # 17:00
                slot_duration_minutes=30,
                working_days={
                    "monday": True,
                    "tuesday": True,
                    "wednesday": True,
                    "thursday": True,
                    "friday": True,
                    "saturday": False,
                    "sunday": False,
                }
            )
    else:
        # Backfill missing user links for existing doctors
        for doctor in Doctor.objects.filter(user__isnull=True):
            username = slugify(doctor.full_name.split()[0])
            user, _ = User.objects.get_or_create(username=username)
            if not user.has_usable_password():
                user.set_password("doktor123")
                user.save()
            doctor.user = user
            doctor.save(update_fields=["user"])
        
        # Mevcut doktorların çalışma saatlerini ayarla
        from datetime import time
        for doctor in Doctor.objects.all():
            if not doctor.working_days:
                doctor.working_days = {
                    "monday": True,
                    "tuesday": True,
                    "wednesday": True,
                    "thursday": True,
                    "friday": True,
                    "saturday": False,
                    "sunday": False,
                }
                doctor.work_start_time = time(9, 0)
                doctor.work_end_time = time(17, 0)
                doctor.slot_duration_minutes = 30
                doctor.save()
    
    # Demo hastalar da oluştur
    ensure_demo_patients()


def ensure_demo_patients():
    """Demo test hastaları oluştur."""
    User = get_user_model()
    
    # Test hastası 1
    username = "test_hasta"
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password="hasta123")
        Patient.objects.create(
            user=user,
            full_name="Test Hasta",
            age=35,
            gender="male",
            weight_kg=75.0,
            height_cm=175.0,
            primary_complaint="Genel kontrol ve muayene",
            allergies="Penisilin"
        )
    
    # Test hastası 2
    username2 = "aylin_hasta"
    if not User.objects.filter(username=username2).exists():
        user2 = User.objects.create_user(username=username2, password="hasta123")
        Patient.objects.create(
            user=user2,
            full_name="Aylin Yılmaz",
            age=28,
            gender="female",
            weight_kg=62.0,
            height_cm=165.0,
            primary_complaint="Baş ağrısı ve yorgunluk",
            allergies=""
        )


def default_schedule_time():
    return timezone.now().replace(minute=0, second=0, microsecond=0) + timezone.timedelta(hours=1)


# --- AI helpers ---


def _get_openai_client():
    if not settings.OPENAI_API_KEY or not OpenAI:
        return None
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _analyze_triage_ai(patient: Patient, triage_data: Dict) -> TriageAnalysis | None:
    client = _get_openai_client()
    if not client:
        return None

    prompt = (
        "Hasta triayj verilerini kullanarak kısa klinik özet, risk seviyesi "
        "(Düşük/Orta/Yüksek), 2-4 öneri ve olası durumlar üret. "
        "JSON olarak cevap ver: {\"summary\":..., \"risk_level\":..., \"suggestions\":[], \"possible_conditions\":[]}.\n\n"
        f"Hasta: {patient.full_name}, yaş {patient.age}, cinsiyet {patient.gender}, "
        f"kilo {patient.weight_kg}kg, boy {patient.height_cm}cm. "
        f"Şikayet: {patient.primary_complaint}. Alerjiler: {patient.allergies or 'bilinmiyor'}.\n"
        f"Triyaj: ateş {triage_data.get('temperature')}, nabız {triage_data.get('heart_rate')}, "
        f"ağrı {triage_data.get('pain_level')}/10, ek semptomlar: {triage_data.get('symptoms_detail') or '-'}."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Klinik karar desteği asistanısın. JSON çıktısı ver."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        return TriageAnalysis(
            summary=data.get("summary", ""),
            risk_level=data.get("risk_level", "Düşük"),
            suggestions=list(data.get("suggestions") or []),
            possible_conditions=list(data.get("possible_conditions") or []),
        )
    except Exception:
        return None


def _check_drug_interactions_ai(patient: Patient, medication_name: str, existing: Sequence[str]) -> str | None:
    client = _get_openai_client()
    if not client:
        return None
    existing_list = ", ".join(existing) if existing else "yok"
    prompt = (
        "İlaç etkileşimi ve uyarılarını 1-2 cümleyle yaz. Yalnızca klinik uyarı ver.\n"
        f"Hasta: yaş {patient.age}, cinsiyet {patient.gender}, kilo {patient.weight_kg}kg, "
        f"alerjiler: {patient.allergies or 'bilinmiyor'}.\n"
        f"Yeni ilaç: {medication_name}. Mevcut ilaçlar: {existing_list}."
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Kısa klinik uyarı ver; koruyucu ton, 2 cümle."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=120,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None
