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
    date_of_birth = models.DateField(null=True, blank=True,)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    select_role=models.CharField(max_length=50,choices=ROLE_CHOICES)
    is_varified=models.BooleanField(default=False)
    address=models.CharField(max_length=150,null=True,blank=True)
    image=models.ImageField(null=True,blank=True)


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
    date_issued=models.DateField(null=True,blank=True)
    certificate_attachment=models.FileField(null=True,blank=True)


class Publication(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='publication')
    publication_title=models.CharField(max_length=50,null=True,blank=True)
    journal=models.CharField(max_length=50,null=True,blank=True)
    publish_date=models.DateField(null=True,blank=True)
    publication_attachment=models.ImageField(null=True,blank=True)


class Awards(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='awards')
    award_name=models.CharField(max_length=50,null=True,blank=True)
    organization=models.CharField(max_length=100,null=True,blank=True)
    receive_date=models.DateField(null=True,blank=True)
    award_attachment=models.ImageField(null=True,blank=True)



class EmergencyContact(models.Model):
    user=ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True,related_name='emergencycontact')
    full_name=models.CharField(max_length=50,null=True,blank=True)
    relation=models.CharField(max_length=50,null=True,blank=True)
    phone_number=models.CharField(max_length=50,null=True,blank=True)
    email=models.EmailField(null=True,blank=True)
    address=models.CharField(max_length=50,null=True,blank=True)


class MainProfile(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='user')
    profession=ForeignKey(Profession,on_delete=models.CASCADE,related_name='main_profession',null=True,blank=True)
    certificate=ManyToManyField(Certification,related_name='main_certification',blank=True)
    Publication=ManyToManyField(Publication,related_name='main_publication',blank=True)
    awards=ManyToManyField(Awards,related_name='main_awards',blank=True)


class PatientProfile(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='patient_user',null=True,blank=True)
    emergency_contact=ForeignKey(EmergencyContact,on_delete=models.CASCADE,related_name='contact',null=True,blank=True)