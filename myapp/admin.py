from django.contrib import admin
from .models import *


# Register your models here.

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['user_id','username','image','date_of_birth','gender','email','select_role','phone_number','password','address','is_varified','about','experience','price','stripe_customer_id']


@admin.register(StaffManagement)
class StaffManagementAdmin(admin.ModelAdmin):
    list_display = ['id','doctor','staff','staff_role','start_time','end_time','duty','assigned_at']


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

@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ['id','doctor','day','start_time','end_time']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id','text','question_type']


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ['id','question','text','is_main_option','parent_option']


@admin.register(PatientAssessment)
class PatientAssessmentAdmin(admin.ModelAdmin):
    list_display = ['id','user','created_at']



@admin.register(PatientAssessmentAns)
class PatientAssessmentAnsAdmin(admin.ModelAdmin):
    list_display = ['id','assessment','question','select_main_option']



@admin.register(WebQuestion)
class WebQuestionAdmin(admin.ModelAdmin):
    list_display = ['id','text','question_type']


@admin.register(WebOption)
class WbOptionAdmin(admin.ModelAdmin):
    list_display = ['id','question','text']


@admin.register(WebPatientAssessment)
class WebPatientAssessmentAdmin(admin.ModelAdmin):
    list_display = ['id','user','created_at']



@admin.register(WebPatientAssessmentAns)
class WebPatientAssessmentAnsAdmin(admin.ModelAdmin):
    list_display = ['id','assessment','question']


@admin.register(FAQs)
class FAQsAdmin(admin.ModelAdmin):
    list_display = ['id','question','answer']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
   list_display = ['id','doctor','patient','created_by','appointment_type','phone_number','age','gender','email','blood_group','marital_status','date_time','duration','note','is_approved','created_at','status']


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ['id','appointment','created_at']



@admin.register(DiagnosisDetail)
class DiagnosisDetailAdmin(admin.ModelAdmin):
    list_display = ['id','diagnosis','diagnosis_type','text']


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ['id','appointment','date','laboratory','test_name','results','report_detail']



@admin.register(PatientHistory)
class PatientHistoryAdmin(admin.ModelAdmin):
    list_display = ['id','appointment','status','created_at']



@admin.register(AppointmentReminder)
class AppointmentReminderAdmin(admin.ModelAdmin):
    list_display = ['id','appointment','datetime','location','reasons_to_reschedule','notification','is_rescheduled']



@admin.register(MedicineReminder)
class MedicineReminderAdmin(admin.ModelAdmin):
    list_display = ['id','appointment','medicine_name','dosage','date_time','medicine_status','notification']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name']