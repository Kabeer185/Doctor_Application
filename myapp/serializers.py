import random
from rest_framework import serializers
from .models import *
from datetime import timedelta
from django.utils import timezone
from allauth.account import app_settings
from .utils import get_available_slots





class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=app_settings.SIGNUP_FIELDS['email']['required'])
    username = serializers.CharField(required=app_settings.SIGNUP_FIELDS['username']['required'])
    gender = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['user_id','username','image','date_of_birth','gender','select_role','email','phone_number','password','address','about']
        extra_kwargs = {'password': {'write_only': True}}




    def validate_gender(self, value):
        value=value.lower()
        valid_genders=dict(User.GENDER_CHOICES).keys()
        if value not in valid_genders:
            raise serializers.ValidationError('gender must be one of {}'.format(valid_genders))
        return value



    def validate(self, data):
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("This email is already registered.")
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError("This username is already registered.")
        return data


    def create(self, validated_data):
        validated_data["is_varified"]=False
        validated_data['gender'] = validated_data['gender'].lower()
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
    def to_representation(self, instance):
        data= super().to_representation(instance)
        data['gender']=instance.get_gender_display()
        return data


class StaffDoctorRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffDoctorRelation
        fields = '__all__'



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


class UserProfileSerializer(serializers.ModelSerializer):
    gender=serializers.SerializerMethodField()
    class Meta:
        model = User
        fields=['username','image','date_of_birth','phone_number','gender','address']
        extra_kwargs={
            'username': {'required': False}
        }

    def get_gender(self,obj):
        return obj.get_gender_display()

    def validate_gender(self,value):
        value=value.lower()
        valid_genders = dict(User.GENDER_CHOICES).keys()
        if value not in valid_genders:
                raise serializers.ValidationError('gender must be one of {}'.format(valid_genders))
        return value



    def validate(self, data):

        user_instance = self.instance
        username = data.get('username')
        if username and User.objects.filter(username=username).exclude(pk=user_instance.pk).exists():
            raise serializers.ValidationError("This username is already taken.")

        return data



class ProfessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ['id','user','profession','specialization','clinic_name','clinic_address','your_note']


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ['id','user','certificate_title','organization','date_issued','certificate_attachment']


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publication
        fields =['id','user','publication_title','journal','publish_date','publication_attachment']



class AwardsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Awards
        fields=['id','user','award_name','organization','receive_date','award_attachment']


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model=EmergencyContact
        fields=['id','user','full_name','relation','phone_number','email','address']


class WorkingHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingHours
        fields = ['id','doctor','day','start_time','end_time']


class MainProfileSerializer(serializers.ModelSerializer):
    user_details=UserSerializer(source='user',read_only=True,many=False)
    profession_details=ProfessionSerializer(source='profession',read_only=True,many=False)
    certificate_details=CertificationSerializer(source='certificate',read_only=True,many=True)
    publication_details=PublicationSerializer(source='Publication',read_only=True,many=True)
    award_details=AwardsSerializer(source='awards',read_only=True,many=True)
    working_hours_details=WorkingHoursSerializer(source='working_hours',read_only=True,many=True)

    class Meta:
        model=MainProfile
        fields=['id','user_details','profession_details','certificate_details','publication_details','award_details','working_hours_details']

    def to_representation(self, instance):
        data=super().to_representation(instance)

        list_fields=['certificate_details','publication_details','award_details','working_hours_details']
        for field in list_fields:
            if field in data and data[field]==[]:
                data[field]=None

        if 'profession_details' in data and data['profession_details']=={}:
            data['profession_details']=None
        if 'user_details' in data and data['user_details']=={}:
            data['user_details']=None
        return data



class PatientProfileSerializer(serializers.ModelSerializer):
    user_details=UserSerializer(source='user',read_only=True)
    emergency_contact_details=EmergencyContactSerializer(source='emergency_contact',read_only=True)
    class Meta:
        model=PatientProfile
        fields=['id','user_details','emergency_contact_details']

    def to_representation(self, instance):
        data=super().to_representation(instance)

        if'emergency_contact_details' in data  and data['emergency_contact_details']=={}:
            data['emergency_contact_details']=None
        return data


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Option
        fields=['id','text','is_main_option','parent_option']


class QuestionSerializer(serializers.ModelSerializer):
    options=OptionSerializer(many=True,read_only=True)
    class Meta:
        model=Question
        fields=['id','text','question_type','options']


class PatientAssessmentAnsSerializer(serializers.ModelSerializer):
    select_sub_option = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Option.objects.all()
    )
    class Meta:
        model=PatientAssessmentAns
        fields=['id','question','select_main_option','select_sub_option','text_answer']


class PatientAssessmentSerializer(serializers.ModelSerializer):
    answer=PatientAssessmentAnsSerializer(many=True)
    class Meta:
        model=PatientAssessment
        fields=['id','answer']

    def create(self, validated_data):
        request = self.context.get('request')
        user=request.user if request else None
        answers_data=validated_data.pop('answer')
        assessment=PatientAssessment.objects.create(user=user,**validated_data)
        for answer_data in answers_data:
            sub_options=answer_data.pop('select_sub_option',[])
            answer=PatientAssessmentAns.objects.create(assessment=assessment, **answer_data)
            answer.select_sub_option.set(sub_options)
        return assessment


class WebOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model=WebOption
        fields=['id','text']


class WebQuestionSerializer(serializers.ModelSerializer):
    web_options=WebOptionSerializer(many=True,read_only=True)
    class Meta:
        model=WebQuestion
        fields=['id','text','question_type','web_options']


class WebPatientAssessmentAnsSerializer(serializers.ModelSerializer):
    select_option = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=WebOption.objects.all()
    )
    class Meta:
        model=WebPatientAssessmentAns
        fields=['id','question','select_option','text_answer']


class WebPatientAssessmentSerializer(serializers.ModelSerializer):
    assessment_answers=WebPatientAssessmentAnsSerializer(many=True)
    class Meta:
        model=WebPatientAssessment
        fields=['id','assessment_answers']

    def create(self, validated_data):
        request = self.context.get('request')
        user=request.user if request else None
        answers_data=validated_data.pop('assessment_answers')
        assessment=WebPatientAssessment.objects.create(user=user,**validated_data)
        for answer_data in answers_data:
            select_options=answer_data.pop('select_option',[])
            answer=WebPatientAssessmentAns.objects.create(assessment=assessment, **answer_data)
            answer.select_option.set(select_options)
        return assessment


class FAQsSerializer(serializers.ModelSerializer):
    class Meta:
        model=FAQs
        fields=['id','question','answer']



class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Appointment
        fields='__all__'
        read_only_fields=['created_by', 'status', 'is_approved', 'cancelled_at', 'created_at']

    def validate_date_time(self,data):
        if data<timezone.now():
            raise serializers.ValidationError('Date must be in the future')
        return data

    def validate(self,data):

        doctor=data.get('doctor')
        date_time=data.get('date_time')
        patient=data.get('patient')

        if not doctor or not date_time or not patient:
            return data
        weekday=date_time.strftime('%A')
        try:
            working_hours=WorkingHours.objects.get(doctor=doctor ,day=weekday)
        except WorkingHours.DoesNotExist:
            raise serializers.ValidationError({
                "date_time":f"Doctor  is not available on{weekday} "
            })
        if not (working_hours.start_time <= date_time.time()<working_hours.end_time):
            raise serializers.ValidationError({
                "date_time":f"Selected time is out of doctor's working hours:{working_hours.start_time}-{working_hours.end_time}"
            })
        if Appointment.objects.filter(
            doctor=doctor,
            date_time=date_time,
            status='upcoming'
        ).exists():
            available_slots=get_available_slots(doctor,date_time.date())
            raise serializers.ValidationError({
                "date_time":"Selected time slot is already booked ",
                "available_slots":available_slots
            })

        if Appointment.objects.filter(
            doctor=doctor,
            patient=patient,
            status='upcoming'
        ).exists():
            raise serializers.ValidationError({
                "patent":"This patient is already booked ",
            })
        return data




class DiagnosisDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model=DiagnosisDetail
        fields='__all__'

    def validate(self, data):
        request=self.context['request']
        user=request.user
        appointment=data.get('patient')
        if not appointment:
            raise serializers.ValidationError({"error":"Appointment are required"})

        if request.method == 'POST':
            if user.select_role != 'doctor':
                raise serializers.ValidationError("Only doctor can create diagnosis")
            if appointment.doctor != user:
                raise serializers.ValidationError("You are not assigned  to this appointment")
        return data


class LabReportSerializer(serializers.ModelSerializer):
    class Meta:
        model=LabReport
        fields='__all__'



class PatientHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model=PatientHistory
        fields='__all__'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields='__all__'