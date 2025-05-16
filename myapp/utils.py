from .models import MainProfile,PatientProfile

def get_or_create_main_profile(user):
    main_profile,created=MainProfile.objects.get_or_create(user=user)
    return main_profile

def get_or_create_patient_profile(user):
    patient_profile,created=PatientProfile.objects.get_or_create(user=user)
    return patient_profile