import stripe
from zoneinfo import ZoneInfo
from django.utils.timezone import now
from .models import MainProfile,PatientProfile,WorkingHours,Appointment,PatientHistory,StaffManagement,DiagnosisDetail
from datetime import datetime,timedelta
from firebase_admin import  messaging
from rest_framework.views import exception_handler



def get_or_create_main_profile(user):
    return MainProfile.objects.get_or_create(user=user)



def get_or_create_patient_profile(user):
    return PatientProfile.objects.get_or_create(user=user)


def get_or_create_patient_history(appointments):
    history,created=PatientHistory.objects.get_or_create(appointment=appointments)
    return history


def is_administrator_staff(user,doctor):

    return StaffManagement.objects.filter(
        staff=user,
        doctor=doctor,
        staff_role='Administrator'
    ).exists()

def get_available_slots(doctor,selected_date,slot_minutes=30):
    try :
        working_hour= WorkingHours.objects.get(doctor=doctor,day=selected_date.strftime("%A"))
    except WorkingHours.DoesNotExist:
        return []
    tz = ZoneInfo("Asia/Karachi")

    start_time=datetime.combine(selected_date,working_hour.start_time).replace(tzinfo=tz)
    end_time=datetime.combine(selected_date,working_hour.end_time).replace(tzinfo=tz)

    delta=timedelta(minutes=slot_minutes)

    all_slots=[]
    current_time=start_time

    current_datetime=now().astimezone(tz)
    is_today=selected_date==current_datetime.date()

    while current_time < end_time:
        if not is_today or current_time.time() > current_datetime.time():
            all_slots.append(current_time)
        current_time += delta
    booked=Appointment.objects.filter(
        doctor=doctor,
        date_time__date=selected_date,
        status='upcoming',
    ).values_list('date_time',flat=True)
    booked_time =set(dt.astimezone(tz).strftime('%H:%M') for dt in booked)
    available = [slot.strftime('%H:%M') for slot in all_slots if slot.strftime('%H:%M')  not in  booked_time]
    return available

def is_lab_technician_staff(user,doctor):

    return StaffManagement.objects.filter(
        staff=user,
        doctor=doctor,
        staff_role='Lab Technician'
    ).exists()


def send_push_notification(registration_id, title, body, data=None):
    message=messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=registration_id,
        android=messaging.AndroidConfig(
            priority='high',
        ),
        data=data if data else{},
    )
    response=messaging.send(message)
    return response



def create_customer(user):
    return stripe.Customer.create(
        email=user.email,
        name=user.username,
        phone=user.phone_number,
        metadata={
            'user_id': user.user_id
        }
    )
def assign_customer_id_to_user(user, id):
    user.customer_id = id
    user.save()


def check_if_customer_exists(user):
    if user.stripe_customer_id:
        return user.stripe_customer_id
    else:
        customer_id = create_customer(user)
        assign_customer_id_to_user(user, customer_id)
        return customer_id


def create_profile_with_roles(user):
    role = user.select_role
    if role in ['doctor', 'staff', 'therapist']:
        profile, _ = get_or_create_main_profile(user)
        profile.gender = user.gender
        profile.save()
    if role in ['patient']:
        profile, _ = get_or_create_patient_profile(user)
        profile.gender = user.gender
        profile.save()




def get_medicine_chart(patient_user):
    meds = DiagnosisDetail.objects.filter(
        diagnosis__appointment__created_by=patient_user,
        diagnosis_type='medication',
    ).exclude(text__isnull=True).exclude(text__exact='')

    med_counts = {}
    for m in meds:
        med_counts[m.text.strip()] = med_counts.get(m.text.strip(), 0) + 1

    total = sum(med_counts.values())
    return {
        k: round(v / total * 100, 2) for k, v in med_counts.items()
    } if total else {}




def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        response.data['status_code'] = response.status_code

    return response


def get_queryset_for_role(user):
    role = user.select_role
    if role == 'patient':
        return Appointment.objects.filter(created_by=user)
    elif role == 'doctor':
        return Appointment.objects.filter(doctor=user)
    elif role == 'staff':
        doctors_ids=StaffManagement.objects.filter(staff=user,staff_role='Administrator').values_list('doctor_id',flat=True)
        return Appointment.objects.filter(doctor__in=doctors_ids)
    else:
        return Appointment.objects.none()