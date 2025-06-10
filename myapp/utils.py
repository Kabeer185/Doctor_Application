from .models import MainProfile,PatientProfile,WorkingHours,Appointment
from datetime import datetime,timedelta



def get_or_create_main_profile(user):
    return MainProfile.objects.get_or_create(user=user)



def get_or_create_patient_profile(user):
    return PatientProfile.objects.get_or_create(user=user)



def get_available_slots(doctor,selected_date,slot_minutes=30):
    try :
        working_hour= WorkingHours.objects.get(doctor=doctor,day=selected_date.strftime("%A"))
    except WorkingHours.DoesNotExist:
        return []

    start_time=datetime.combine(selected_date,working_hour.start_time)
    end_time=datetime.combine(selected_date,working_hour.end_time)
    delta=timedelta(minutes=slot_minutes)

    all_slots=[]
    current_time=start_time

    while current_time < end_time:
        all_slots.append(current_time)
        current_time += delta
    booked=Appointment.objects.filter(
        doctor=doctor,
        date_time__date=selected_date,
        status='upcoming',
    ).values_list('date_time',flat=True)
    booked_time =set(dt.strftime('%H:%M') for dt in booked)
    available = [slot.strftime('%H:%M') for slot in all_slots if slot.strftime('%H:%M')  not in  booked_time]
    return available