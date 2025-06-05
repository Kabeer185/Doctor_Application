from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from django.db.models import Q
from django.db.models.aggregates import Count
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.views.generic import RedirectView
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from datetime import date
from .serializers import *
from .utils import *
from .models import *
from.permissions import *

# Create your views here.



class SignUpView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        username = request.data.get('username')
        if not email or not phone_number or not username:
            return  Response({ "email": "Email is required.",
                "phone_number": "Phone number is required.",
                "username":"Username is required"},status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email,username=username)
            if user.is_varified:
                return Response({ "detail": "Account already verified  with this email "},status=status.HTTP_400_BAD_REQUEST)

            # setattr(object,field,new_field)
            update_fields =['date_of_birth','gender','phone_number','select_role']
            for field in update_fields:
                if field in request.data:
                    setattr(user,field,request.data[field])
            user.save()

            role=user.select_role
            if role in ['doctor','staff','therapist']:
                profile, _ = get_or_create_main_profile(user)
                profile.gender = user.gender
                profile.save()
            if role in ['patient']:
                profile, _ = get_or_create_patient_profile(user)
                profile.gender = user.gender
                profile.save()


            OTP.objects.filter(user=user).delete()
            otp_code = f"{random.randint(0, 99999):05d}"
            OTP.objects.create(
                user=user,
                token=otp_code,
                otp_expiry=timezone.now() + timedelta(seconds=120),
                is_varified=False
            )

            send_mail(
                "Your OTP Code",
                f"Your OTP Code is {otp_code}",
                settings.EMAIL_HOST_USER,
                [user.email],
                fail_silently=False,
            )
            return Response({"message":"OTP sent successfully To log in First verify it ."},status=status.HTTP_200_OK)
        except User.DoesNotExist:

            serializer=self.serializer_class(data=request.data,context={'request':request})
            if serializer.is_valid():
                user = serializer.save()
                user.save()

                role = user.select_role
                if role in ['doctor', 'therapist', 'staff']:
                    get_or_create_main_profile(user)
                elif role == 'patient':
                    get_or_create_patient_profile(user)


                latest_otp=OTP.objects.filter(user=user).latest('id')
                send_mail(
                    "Your OTP Code ",
                    f"Your OTP Code is {latest_otp.token}",
                    settings.EMAIL_HOST_USER,
                    [user.email],
                    fail_silently=False,
                )
                return Response({"message":"Account Created Successfully  an OTP send via email "}, status=status.HTTP_201_CREATED)

            return Response(print(serializer.errors), status=status.HTTP_400_BAD_REQUEST)

class StaffDoctorRelationViewSet(viewsets.ModelViewSet):
    queryset = StaffDoctorRelation.objects.all()
    serializer_class = StaffDoctorRelationSerializer
    permission_classes = [IsAuthenticated]



class VerifyOTPView(viewsets.ModelViewSet):
    queryset = OTP.objects.all()
    serializer_class = OTPSerializer
    permission_classes = [AllowAny]


    def create(self, request, *args, **kwargs):
        serializer=self.serializer_class(data=request.data,context={'request':request})
        if serializer.is_valid():
            token=serializer.validated_data['token']
            try:
                otp_instance=OTP.objects.get(token=token,is_varified=False)
                if otp_instance.otp_expiry<timezone.now():
                    return Response({'error':'OTP Expired'}, status=status.HTTP_400_BAD_REQUEST)
                otp_instance.is_varified=True
                otp_instance.save()
                user=otp_instance.user
                user.is_varified=True
                user.save()
                return Response({'message':'Account verified Successfully'}, status=status.HTTP_200_OK)
            except OTP.DoesNotExist:
                return Response({'message':'OTP Does Not Exist'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



class RegenerateOTPView(APIView):

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        email=request.data.get('email')
        if not email:
            return Response({'error':'Email Required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


        otp_instance,created = OTP.objects.get_or_create(user=user)

        now = timezone.now()

        if int(otp_instance.max_otp_try) <= 0:
            if otp_instance.otp_max_out and now < otp_instance.otp_max_out:
                return Response({"error": "You reached maximum OTP try limit. Please try again after 15 minutes."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                otp_instance.max_otp_try = 5
                otp_instance.otp_max_out = None

        otp_instance.token = f"{random.randint(0, 99999):05d}"
        otp_instance.otp_expiry = now + timedelta(seconds=120)
        otp_instance.max_otp_try =max(int(otp_instance.max_otp_try) - 1,0)
        otp_instance.is_verified = False

        if int(otp_instance.max_otp_try) == 0:
            otp_instance.otp_max_out = now + timedelta(minutes=15)
        otp_instance.save()

        send_mail(
            "Your New OTP Code",
            f"Your new OTP is {otp_instance.token}",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )

        return Response({"message": "New OTP sent successfully"}, status=status.HTTP_200_OK)



class LoginView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']


    def create(self, request, *args, **kwargs):
        serializer=self.serializer_class(data=request.data,context={'request':request})
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user=authenticate(request,email=email,password=password)
            if user:
                if not  user.is_varified:
                    return Response({"error":"Please first varify the account then login "},status=status.HTTP_403_FORBIDDEN)
                refresh=RefreshToken.for_user(user)
                access_token=str(refresh.access_token)
                return Response({'message':'Login Successfully','id':user.user_id,'email':email,'role':user.select_role,'access_token':access_token,'refresh_token':str(refresh)},status=status.HTTP_200_OK)

            return Response({'error':'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)

        return Response({"error":"Username or Password Incorrect "}, status=status.HTTP_400_BAD_REQUEST)



class UserRedirectView(RedirectView,LoginRequiredMixin):
    permanent = False
    def get_redirect_url(self):
        return "http://127.0.0.1"



class GoogleConnect(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class=OAuth2Client


    def post(self,request,*args, **kwargs):
        role=request.data.get('select_role') or request.data.get('role')
        response=super().post(request,*args,**kwargs)

        if response.status_code != status.HTTP_200_OK:
            return response

        user=self.request.user

        if role and not user.select_role:
            user.select_role=role
        if not user.is_varified:
            user.is_varified=True
            user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            "message":"Login Successfully with google",
            "id":user.user_id,
            "email":user.email,
            "role":user.select_role,
            "access_token":access_token,
            "refresh_token":str(refresh)

        },status=status.HTTP_200_OK)




class FacebookConnect(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    authentication_classes = []
    permission_classes = []

    def post(self,request,*args, **kwargs):
        role=request.data.get('select_role') or request.data.get('role')
        response=super().post(request,*args,**kwargs)

        if response.status_code != status.HTTP_200_OK:
            return response

        user=self.request.user
        if role and not user.select_role:
            user.select_role=role
        if not user.is_varified:
            user.is_varified=True
            user.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'message':'Login Successfully with facebook',
            'id':user.user_id,
            'email':user.email,
            'role':user.select_role,
            'access_token':access_token,
            'refresh_token':str(refresh)
        },status=status.HTTP_200_OK)




class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)


    def perform_update(self, serializer):
        user=serializer.save()

        if user.select_role in ['doctor','therapist','staff']:
            profile,_=get_or_create_main_profile(user)

        elif user.select_role == 'patient':
            profile,_=get_or_create_patient_profile(user)
        else:
            profile=None


        if profile:
            profile.username=user.username
            profile.address = user.address
            profile.image = user.image
            profile.gender = user.gender
            profile.date_of_birth = user.date_of_birth
            profile.phone_number = user.phone_number
            profile.email = user.email
            profile.save()
        return Response({
            "message":"User profile updated successfully",
        },status=status.HTTP_200_OK)




class ProfessionViewSet(viewsets.ModelViewSet):
    queryset = Profession.objects.all()
    serializer_class = ProfessionSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile,_ = get_or_create_main_profile(self.request.user)
        profile.profession = instance
        profile.save()



class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile,_ = get_or_create_main_profile(self.request.user)
        profile.certificate.add(instance)


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile,_ = get_or_create_main_profile(self.request.user)
        profile.Publication.add(instance)



class AwardsViewSet(viewsets.ModelViewSet):
    queryset = Awards.objects.all()
    serializer_class = AwardsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile,_ = get_or_create_main_profile(self.request.user)
        profile.awards.add(instance)



class EmergencyContactViewSet(viewsets.ModelViewSet):
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile,_=get_or_create_patient_profile(self.request.user)
        profile.emergency_contact=instance
        profile.save()





class MainProfileViewSet(viewsets.ModelViewSet):
    serializer_class = MainProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    def get_queryset(self):
        return  MainProfile.objects.select_related('user', 'profession').prefetch_related('certificate', 'Publication', 'awards').filter(user=self.request.user)


    def  list(self,request,*args,**kwargs):
        queryset = self.get_queryset()
        instance=queryset.first()
        if not instance:
            return  Response({})
        serializer=self.get_serializer(instance)
        return Response(serializer.data)


class PatientProfileViewSet(viewsets.ModelViewSet):
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return PatientProfile.objects.select_related('user','emergency_contact').filter(user=self.request.user)


    def  list(self,request,*args,**kwargs):
        queryset = self.get_queryset()
        instance=queryset.first()
        if not instance:
            return  Response({})
        serializer=self.get_serializer(instance)
        return Response(serializer.data)



class WorkingHoursViewSet(viewsets.ModelViewSet):
    queryset = WorkingHours.objects.all()
    serializer_class = WorkingHoursSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save(doctor=self.request.user)
        profile,_= get_or_create_main_profile(self.request.user)
        profile.working_hours.add(instance)



class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']



class PatientAssessmentViewSet(viewsets.ModelViewSet):
    queryset = PatientAssessment.objects.all()
    serializer_class = PatientAssessmentSerializer
    permission_classes = [IsAuthenticated]



class WebQuestionViewSet(viewsets.ModelViewSet):
    queryset = WebQuestion.objects.all()
    serializer_class = WebQuestionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']



class WebPatientAssessmentViewSet(viewsets.ModelViewSet):
    queryset = WebPatientAssessment.objects.all()
    serializer_class = WebPatientAssessmentSerializer
    permission_classes = [IsAuthenticated]


class FAQViewSet(viewsets.ModelViewSet):
    queryset = FAQs.objects.all()
    serializer_class = FAQsSerializer
    http_method_names = ['get']


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated,CanCreateAppointments,]
    queryset = Appointment.objects.all()

    def get_queryset(self):

        user=self.request.user
        status_param=self.request.query_params.get('status')


        if user.select_role =='patient':
            qs=Appointment.objects.filter(created_by=user)
        elif user.select_role =='staff':
            doctors_ids=(
                StaffDoctorRelation.objects
                .filter(staff=user)
                .values_list('doctor_id', flat=True)
            )
            qs=(Appointment.objects.filter(doctor_id__in=doctors_ids))
        elif user.select_role =='doctor':
            qs=Appointment.objects.filter(doctor=user)
        else:
            qs=Appointment.objects.none()

        if status_param in ['upcoming','completed','cancelled']:
            qs=qs.filter(status=status_param)
        return qs



    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            created_by=request.user,
            status='upcoming',
            is_approved=True,
        )
        return Response({
            "message": "Appointment created successfully","appointment": serializer.data
        },status=status.HTTP_201_CREATED)


    def perform_update(self, serializer):
        serializer.save(
            status='upcoming',
            is_approved=True,
            cancelled_at=None
        )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        status_count=queryset.aggregate(
            total =Count(id),
            upcoming=Count(id,filter=Q(status='upcoming')),
            completed=Count(id,filter=Q(status='completed')),
            cancelled=Count(id,filter=Q(status='cancelled')),
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status_count":status_count,
            "results": serializer.data,
        })


    @action(detail=True,methods=['patch'],permission_classes=[IsAuthenticated,CanCancelAppointments])
    def cancel(self,request,pk=None):
        appointment= self.get_object()
        self.check_object_permissions(request,appointment)
        appointment.status = 'cancelled'
        appointment.cancelled_at=timezone.now()
        appointment.save()
        return Response({
            "message":"Your Appointment has been cancelled",
            "appointment":self.get_serializer(appointment).data
        },status=status.HTTP_200_OK)

    @action(detail=True,methods=['patch'],permission_classes=[IsAuthenticated,CanCompleteAppointment])
    def complete(self,request,pk=None):
        appointment = self.get_object()
        self.check_object_permissions(request,appointment)
        appointment.status = 'completed'
        appointment.cancelled_at=None
        appointment.save()
        return Response({
            "message":"Your Appointment has been completed",
            "appointment":self.get_serializer(appointment).data
        },status=status.HTTP_200_OK)

    @action(detail=True,methods=['patch'],permission_classes=[IsAuthenticated,CanUpdateAppointments])
    def reschedule(self,request,pk=None):
        appointment = self.get_object()
        new_datetime_str=request.data.get('date_time')

        if not new_datetime_str:
            return Response({"error":"New date_time is required"},status=status.HTTP_400_BAD_REQUEST)

        try:
            new_datetime = datetime.fromisoformat(new_datetime_str)
        except ValueError:
            return Response({"error": "Invalid date_time format. Use ISO format like YYYY-MM-DDTHH:MM:SS"},
                            status=status.HTTP_400_BAD_REQUEST)

        available_slots = get_available_slots(appointment.doctor, new_datetime.date())
        new_time_str = new_datetime.strftime('%H:%M')
        if new_time_str not in available_slots:
            return Response({"error": "Selected slot is not available."}, status=status.HTTP_400_BAD_REQUEST)


        appointment.date_time=new_datetime
        appointment.status = 'upcoming'
        appointment.cancelled_at=None
        appointment.save()
        return Response({
            "message":"Your Appointment has been rescheduled",
            "appointment":self.get_serializer(appointment).data
        },status=status.HTTP_200_OK)
    @action(detail=False,methods=['get'])
    def available_slots(self,request):
        doctor_id=request.query_params.get('doctor_id')
        date=request.query_params.get('date')
        if not doctor_id or not date:
            return  Response({"error":"Doctor_id or date is required"},status=status.HTTP_400_BAD_REQUEST)
        try:
            doctor=User.objects.get(id=doctor_id,select_role='doctor')

        except User.DoesNotExist:
            return Response({"error":"Doctor does not found"},status=status.HTTP_400_BAD_REQUEST)


        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()

        except ValueError:
            return Response({"error":"Invalid date format. Use YYYY-MM-DD."},status=status.HTTP_400_BAD_REQUEST)
        slots=get_available_slots(doctor,selected_date)
        return Response({"available_slots":slots},status=status.HTTP_200_OK)


    @action(detail=False,methods=['get'])
    def today_schedule(self,request):
        qs=self.get_queryset().filter(date= date.today()).order_by('start_time')
        serializer=self.get_serializer(qs,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)



    @action(detail=False,methods=['get'])
    def upcoming_schedule(self,request):
        qs = self.get_queryset().filter(date__gt= date.today()).order_by("date","start_time")
        serializer=self.get_serializer(qs,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)



class DiagnosisDetailViewSet(viewsets.ModelViewSet):
    queryset = DiagnosisDetail.objects.all()
    serializer_class = DiagnosisDetailSerializer
    permission_classes = [IsAuthenticated,CanCreateDiagnosis]

    def get_queryset(self):
        user=self.request.user

        if user.select_role == 'doctor':
            return DiagnosisDetail.objects.filter(patient__doctor=user)
        elif user.select_role == 'patient':
            return DiagnosisDetail.objects.filter(patient__created_by=user)
        elif user.select_role == 'staff':
            assigned_doctors=StaffDoctorRelation.objects.filter(staff=user).values_list('doctor',flat=True)
            return DiagnosisDetail.objects.filter(patient__doctor__in=assigned_doctors)
        return DiagnosisDetail.objects.none()


class LabReportViewSet(viewsets.ModelViewSet):
    queryset = LabReport.objects.all()
    serializer_class = LabReportSerializer
    permission_classes = [IsAuthenticated]




class HistoryViewSet(viewsets.ModelViewSet):
    queryset = History.objects.all()
    serializer_class = HistorySerializer
    permission_classes = [IsAuthenticated]



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
