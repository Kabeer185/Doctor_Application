from django.contrib import admin
from .models import *


# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['user_id','username','image','date_of_birth','gender','email','select_role','phone_number','password','is_varified']



@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['id','user','token','is_varified']


    
    
@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display =['id','user','profession','specialization','clinic_name','clinic_address','your_note']


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ['id','user','certificate_title','organization','date_issued','certificate_attachment']



@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ['id','user','publication_title','journal','publish_date','publication_attachment']



@admin.register(Awards)
class AwardsAdmin(admin.ModelAdmin):
    list_display = ['id','user','award_name','organization','receive_date','award_attachment']



@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ['id','user','full_name','relation','phone_number','email','address']



@admin.register(MainProfile)
class MainProfileAdmin(admin.ModelAdmin):
    list_display = ['id','user','profession']



@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ['id','user','emergency_contact']