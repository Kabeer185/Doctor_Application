import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import ForeignKey, ManyToManyField


# Create your models here.



class User(AbstractUser):
    GENDER_CHOICES = [
        ('male', 'Male'), ('female', 'Female'), ('other', 'Other'),
    ]
    ROLE_CHOICES = [
        ('patient', 'Patient'), ('doctor', 'Doctor'), ('staff', 'Staff'), ('therapist', 'Therapist')
    ]
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    user_id=models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    phone_number = models.CharField(max_length=11,null=True,blank=True)
    date_of_birth = models.DateTimeField(null=True, blank=True,)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    select_role=models.CharField(max_length=50,choices=ROLE_CHOICES)
    is_varified=models.BooleanField(default=False)
    address=models.CharField(max_length=150,null=True,blank=True)
    image=models.ImageField(null=True,blank=True)
    about=models.TextField(null=True,blank=True)



class StaffDoctorRelation(models.Model):
    doctor=models.ForeignKey(User,on_delete=models.CASCADE,related_name='doctor_assigned_staff',limit_choices_to={'select_role':'doctor'})
    staff=models.ForeignKey(User,on_delete=models.CASCADE,related_name='staff_assigned_doctor',limit_choices_to={'select_role':'staff'})
    assigned_at=models.DateTimeField(auto_now_add=True)



class OTP(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='otp')
    token=models.CharField(max_length=5,blank=True,null=True)
    otp_expiry=models.DateTimeField(null=True, blank=True)
    is_varified=models.BooleanField(default=False)
    max_otp_try=models.CharField(max_length=4,default=5)
    otp_max_out=models.DateTimeField(null=True, blank=True)




class Profession(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='profession')
    profession=models.CharField(max_length=50,null=True,blank=True)
    specialization=models.CharField(max_length=50,null=True,blank=True)
    clinic_name=models.CharField(max_length=50,null=True,blank=True)
    clinic_address=models.CharField(max_length=150,null=True,blank=True)
    your_note=models.TextField(null=True,blank=True)



class Certification(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='certification')
    certificate_title=models.CharField(max_length=50,null=True,blank=True)
    organization=models.CharField(max_length=50,null=True,blank=True)
    date_issued=models.DateTimeField(null=True,blank=True)
    certificate_attachment=models.FileField(null=True,blank=True)



class Publication(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='publication')
    publication_title=models.CharField(max_length=50,null=True,blank=True)
    journal=models.CharField(max_length=50,null=True,blank=True)
    publish_date=models.DateTimeField(null=True,blank=True)
    publication_attachment=models.ImageField(null=True,blank=True)



class Awards(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='awards')
    award_name=models.CharField(max_length=50,null=True,blank=True)
    organization=models.CharField(max_length=100,null=True,blank=True)
    receive_date=models.DateTimeField(null=True,blank=True)
    award_attachment=models.ImageField(null=True,blank=True)



class EmergencyContact(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='emergencycontact')
    full_name=models.CharField(max_length=50,null=True,blank=True)
    relation=models.CharField(max_length=50,null=True,blank=True)
    phone_number=models.CharField(max_length=50,null=True,blank=True)
    email=models.EmailField(null=True,blank=True)
    address=models.CharField(max_length=50,null=True,blank=True)



class WorkingHours(models.Model):
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    doctor=ForeignKey(User,on_delete=models.CASCADE,related_name='working_hours',null=True,blank=True)
    day=models.CharField(max_length=50,choices=DAYS_OF_WEEK,null=True,blank=True)
    start_time=models.TimeField(null=True,blank=True)
    end_time=models.TimeField(null=True,blank=True)


class MainProfile(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='user')
    profession=ForeignKey(Profession,on_delete=models.CASCADE,related_name='main_profession',null=True,blank=True)
    certificate=ManyToManyField(Certification,related_name='main_certification',blank=True)
    Publication=ManyToManyField(Publication,related_name='main_publication',blank=True)
    awards=ManyToManyField(Awards,related_name='main_awards',blank=True)
    working_hours=ManyToManyField(WorkingHours,related_name='main_working_hours',blank=True)



class PatientProfile(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='patient_user',null=True,blank=True)
    emergency_contact=ForeignKey(EmergencyContact,on_delete=models.CASCADE,related_name='contact',null=True,blank=True)



class Question(models.Model):
    QUESTION_TYPE = [
        ('yes_no_sub', 'Yes/No with sub-option'),
        ('multi_choice', 'Multiple Choice'),
        ('text', 'Free text input'),
    ]
    text=models.TextField(null=True,blank=True)
    question_type=models.CharField(choices=QUESTION_TYPE,max_length=50,null=True,blank=True)


class Option(models.Model):
    question=models.ForeignKey(Question,on_delete=models.CASCADE,related_name='options',null=True,blank=True)
    text=models.TextField(null=True,blank=True)
    is_main_option=models.BooleanField(default=False)
    parent_option=models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True)


class PatientAssessment(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,related_name='patientassessment',null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)



class PatientAssessmentAns(models.Model):
    assessment=ForeignKey(PatientAssessment,on_delete=models.CASCADE,related_name='answer',null=True,blank=True)
    question=ForeignKey(Question,on_delete=models.CASCADE,related_name='assessment_question',null=True,blank=True)
    select_main_option=models.ForeignKey(Option,on_delete=models.CASCADE,related_name='assessment_main_option',null=True,blank=True)
    select_sub_option=models.ManyToManyField(Option,related_name='assessment_sub_option')
    text_answer=models.TextField(null=True,blank=True)



class WebQuestion(models.Model):
    QUESTION_TYPE = [
        ('multi_choice', 'Multiple Choice'),
        ('text', 'Free text input'),
    ]
    text=models.TextField(null=True,blank=True)
    question_type=models.CharField(choices=QUESTION_TYPE,max_length=50,null=True,blank=True)


class WebOption(models.Model):
    question=models.ForeignKey(WebQuestion,on_delete=models.CASCADE,related_name='web_options')
    text=models.TextField(null=True,blank=True)


class WebPatientAssessment(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,related_name='web_patientassessment')
    created_at=models.DateTimeField(auto_now_add=True)



class WebPatientAssessmentAns(models.Model):
    assessment=ForeignKey(WebPatientAssessment,on_delete=models.CASCADE,related_name='assessment_answers')
    question=ForeignKey(WebQuestion,on_delete=models.CASCADE,related_name='assessment_questions')
    select_option=models.ManyToManyField(WebOption,related_name='assessment_option')
    text_answer=models.TextField(null=True,blank=True)



class FAQs(models.Model):
    question=models.TextField(null=True,blank=True)
    answer=models.TextField(null=True,blank=True)



class Appointment(models.Model):
    APPOINTMENT_TYPE = [
        ('regular check_up', 'Regular Check_up'),
        ('urgent check_up', 'Urgent Check_up'),
    ]
    APPOINTMENT_STATUS = [
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    doctor=models.ForeignKey(User,on_delete=models.CASCADE,related_name='appointment_doctor',limit_choices_to={"select_role":"doctor"})
    patient=models.TextField()
    created_by=models.ForeignKey(User,on_delete=models.CASCADE,related_name='appointment_created_by')
    appointment_type=models.CharField(choices=APPOINTMENT_TYPE,max_length=50)
    phone_number=models.CharField(null=True,blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    blood_group = models.CharField(max_length=50, null=True, blank=True)
    marital_status = models.CharField(max_length=50, null=True, blank=True)
    date_time=models.DateTimeField()
    duration=models.CharField(max_length=50,null=True,blank=True)
    note=models.TextField(null=True,blank=True)
    is_approved=models.BooleanField(default=False)
    status=models.CharField(choices=APPOINTMENT_STATUS,max_length=50,null=True,blank=True)
    cancelled_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)



class DiagnosisDetail(models.Model):
    FIELDS_CHOICES=[
        ('compliants','Compliants'),
        ('history & symptoms','History & Symptoms'),
        ('physical examination','Physical Examination'),
        ('diagnosis','Diagnosis'),
        ('treatment plan','Treatment Plan'),
        ('recomended test','Recommended Test'),
        ('medication','Medication'),
        ('immediate attention required ','Immediate Attention Required'),
    ]
    patient=models.ForeignKey(Appointment,on_delete=models.CASCADE,related_name='diagnosis_patient')
    diagnosis_type=models.CharField(choices=FIELDS_CHOICES,max_length=50,null=True,blank=True)
    text=models.TextField(null=True,blank=True)



class LabReport(models.Model):
    RESULT_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High'),
        ('low', 'Low'),
        ('positive +ve', 'Positive +ve'),
        ('negative -ve', 'Negative -ve'),
        ('borderline', 'Borderline'),
        ('detected', 'Detected'),
    ]
    patient_name=models.CharField(max_length=50,null=True,blank=True)
    date=models.DateTimeField(auto_now_add=True)
    laboratory=models.CharField(max_length=50,null=True,blank=True)
    test_name=models.CharField(max_length=50,null=True,blank=True)
    results=models.CharField(max_length=50,choices=RESULT_CHOICES)
    report_detail=models.TextField(null=True,blank=True)


class History(models.Model):
    STATUS_CHOICES=[
        ("recovered", "Recovered"),
        ("pending", "Pending"),
        ("ongoing", "Ongoing"),
        ("cancelled", "Cancelled"),
        ("expired", "Expired"),
    ]
    # patient_name=models.ManyToManyField
    date_time=models.DateTimeField(auto_now_add=True)
    diagnosis_summery=models.ForeignKey(DiagnosisDetail,on_delete=models.CASCADE,related_name='history')
    lab_test=models.ForeignKey(LabReport,on_delete=models.CASCADE,related_name='lab_test_history')
    status=models.CharField(choices=STATUS_CHOICES,max_length=50,null=True,blank=True)


class Category(models.Model):
    name=models.CharField(max_length=50,null=True,blank=True)
