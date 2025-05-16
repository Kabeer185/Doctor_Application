import random
from rest_framework import serializers
from .models import *
from datetime import timedelta
from django.utils import timezone
from allauth.account import app_settings





class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=app_settings.SIGNUP_FIELDS['email']['required'])
    username = serializers.CharField(required=app_settings.SIGNUP_FIELDS['username']['required'])
    class Meta:
        model = User
        fields = ['user_id','username','image','date_of_birth','gender','select_role','email','phone_number','password']
        extra_kwargs = {'password': {'write_only': True}}


    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("This email is already registered.")
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("This username is already registered.")
        return data


    def create(self, validated_data):
        validated_data["is_varified"]=False
        user=User(
            username=validated_data['username'],
            date_of_birth=validated_data['date_of_birth'],
            gender=validated_data['gender'],
            select_role=validated_data['select_role'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
        )
        user.set_password(validated_data['password'])
        user.save()

        OTP.objects.create(
            user=user,
            token=f"{random.randint(0,99999):05d}",
            otp_expiry=timezone.now() +timedelta(seconds=120),
            is_varified=False
        )
        return user



class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['token']


    def validate_otp(self, value):
        if not value:
            raise serializers.ValidationError("OTP is required.")
        return value



class RegenerateOTPSerializer(serializers.Serializer):
    email=serializers.EmailField(required=app_settings.SIGNUP_FIELDS['email']['required'])



class LoginSerializer(serializers.Serializer):
    email=serializers.EmailField(required=app_settings.SIGNUP_FIELDS['email']['required'])
    password=serializers.CharField(required=True)

    def validate(self,data):
        email=data.get('email')
        password=data.get('password')
        if not email or not password:
            raise serializers.ValidationError("Email And Password is Required")
        return data




class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ['user','profession','specialization','clinic_name','clinic_address','your_note']


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['user','certificate_title','organization','date_issued','certificate_attachment']


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields =['user','publication_title','journal','publish_date','publication_attachment']



class AwardsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Awards
        fields=['user','award_name','organization','receive_date','award_attachment']


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model=EmergencyContact
        fields=['user','full_name','relation','phone_number','email','address']



class MainProfileSerializer(serializers.ModelSerializer):
    user_details=UserSerializer(source='user',read_only=True,many=False)
    profession_details=ProfessionSerializer(source='profession',read_only=True,many=False)
    certificate_details=CertificationSerializer(source='certificate',read_only=True,many=True)
    publication_details=PublicationSerializer(source='Publication',read_only=True,many=True)
    award_details=AwardsSerializer(source='awards',read_only=True,many=True)

    class Meta:
        model=MainProfile
        fields=['id','user_details','profession_details','certificate_details','publication_details','award_details']




class PatientProfileSerializer(serializers.ModelSerializer):
    user_details=UserSerializer(source='user',read_only=True)
    emergency_contact_details=EmergencyContactSerializer(source='emergency_contact',read_only=True)
    class Meta:
        model=PatientProfile
        fields=['user_details','emergency_contact_details']








