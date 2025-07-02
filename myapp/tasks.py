from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from fcm_django.admin import FCMDevice
from .models import AppointmentReminder, MedicineReminder
from .utils import send_push_notification
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task
def send_appointment_reminder():
    now = timezone.now()
    now_floor = now.replace(second=0, microsecond=0)

    reminders = AppointmentReminder.objects.filter(
        notification=True,
        is_rescheduled=False,
        datetime__gte=now_floor,
        datetime__lte=now_floor + timedelta(minutes=1),
    )

    for reminder in reminders:
        try:
            appointment = reminder.appointment
            user=appointment.created_by
            print(f"🔔 Reminder ID: {reminder.id} for Appointment ID: {appointment.id}")
            print(f"➡️  Created by User: {user} | Email : {user.email}")
            print(f"📝 Patient (text field): {appointment.patient}")

            devices = FCMDevice.objects.filter(user=user)

            if not devices.exists():
                print(f"⚠️ No FCM devices registered for user {user.email}")
                continue

            title = 'Appointment Reminder'
            body = f'You have an appointment at {reminder.datetime.strftime("%I:%M %p")} at {reminder.location or "your clinic"}.'
            data = {
                "appointment_id": str(appointment.id),
                "type": "reminder"
            }
            for device in devices:
                try:
                    response = send_push_notification(device.registration_id, title, body, data)
                    print(f"✅ Notification sent to {user.email} on {device.id}: {response}")
                except Exception as e:
                    print(f"❌ FCM error for device {device.id} of user {user.email}: {str(e)}")
                    if "Requested entity was not found" in str(e):
                        print(f"🧹 Removing invalid FCM device {device.id} for user {user.email}")
                        device.delete()


        except Exception as e:

            print(f"❌ Unexpected error in reminder {reminder.id}: {e}")



@shared_task()
def send_medicine_reminder():
    time_now = timezone.now()
    now_floor = time_now
    reminders=MedicineReminder.objects.filter(
        notification=True,
        date_time__gte=now_floor,
        date_time__lte=now_floor + timedelta(minutes=1)

    )
    print("🚀 Medicine reminder task triggered")
    print(f"⏰ Checking medicine reminders at {now_floor}. Found: {reminders.count()}")

    for reminder in reminders:
        print(f"⏱️ Reminder scheduled for: {reminder.date_time} | Now: {now_floor}")
        try:
            appointment = reminder.appointment
            user=appointment.created_by
            print(f"🔔 Reminder ID: {reminder.id} for Appointment ID: {appointment.id}")
            print(f"➡️  Created by User: {user} | Email : {user.email}")
            print(f"📝 Patient (text field): {appointment.patient}")

            devices = FCMDevice.objects.filter(user=user)
            if not devices.exists():
                print(f"⚠️ No FCM devices registered for user {user.email}")
                continue

            title='Medicine Reminder'
            body=(
                f"time to take your medicine: {reminder.medicine_name or 'unnamed'} "
                f"({reminder.dosage or 'dosage not specified'})"
            )

            data={
                "type":"medicine_reminder",
                "appointment_id": str(appointment.id),
                "reminder_id": str(reminder.id),
            }

            for device in devices:
                try:
                    response = send_push_notification(device.registration_id, title, body, data)
                    print(f"✅ Notification sent to {user.email} on {device.id}: {response}")
                except Exception as e:
                    print(f"❌ FCM error for device {device.id} of user {user.email}: {str(e)}")
                    if "Requested entity was not found" in str(e):
                        print(f"🧹 Removing invalid FCM device {device.id} for user {user.email}")
                        device.delete()
        except Exception as e:

            print(f"❌ Unexpected error in reminder {reminder.id}: {e}")

