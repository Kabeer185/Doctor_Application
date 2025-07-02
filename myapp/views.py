from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.db.models import Q
from django.db.models.aggregates import Count
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.views.generic import RedirectView
from fcm_django.api.rest_framework import AuthorizedMixin, FCMDeviceViewSet
from rest_framework import  filters
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from datetime import date
from django.utils.timezone import localtime, localdate
from .serializers import *
from .utils import *
from .models import *
from .permissions import *
from .paginations import *
import stripe

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
            check_if_customer_exists(user)
            create_profile_with_roles(user)





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
                stripe_customer=stripe.Customer.create(
                    email=user.email,
                    username=user.username,
                    phone_number=user.phone_number,
                    metadata={'user_id': user.user_id}
                )
                user.stripe_customer_id = stripe_customer.id
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

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StaffManagementViewSet(viewsets.ModelViewSet):
    serializer_class = StaffManagementSerializer
    permission_classes = [IsAuthenticated,CanCreateStaffManagement]
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        user =self.request.user

        if user.select_role == 'doctor':
            return  StaffManagement.objects.filter(doctor=user)
        if user.select_role == 'patient':
            raise PermissionDenied("permission denied")
        if user.select_role == 'staff':
            raise PermissionDenied("permission denied")

        return StaffManagement.objects.none()



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

                staff_role = None
                if user.select_role == 'staff':
                    staff_mgmt = StaffManagement.objects.filter(staff=user).first()
                    if staff_mgmt:
                        staff_role = staff_mgmt.staff_role
                response_data = {
                    'message': 'Login Successfully',
                    'id': user.user_id,
                    'image':user.image.url if user.image and hasattr(user.image, 'url') else None,
                    'username': user.username,
                    'email': email,
                    'role': user.select_role,
                    'stripe_customer_id': user.stripe_customer_id,
                    'access_token': access_token,
                    'refresh_token': str(refresh),
                }
                if staff_role:
                    response_data['staff_role'] = staff_role
                return Response(response_data, status=status.HTTP_200_OK)

            return Response({'error':'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)

        return Response({"error":"Email  or Password Incorrect "}, status=status.HTTP_400_BAD_REQUEST)



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
            profile.image = user.image.url if user.image and hasattr(user.image, 'url') else None
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

    def get_queryset(self):
        return WorkingHours.objects.filter(doctor=self.request.user)


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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields=['status']
    search_fields=['status','patient','doctor__username','created_by__username','phone_number','age','gender','email','blood_group','marital_status']
    queryset = Appointment.objects.all()
    pagination_class = MyPageNumberPagination

    def get_queryset(self):

        user=self.request.user
        qs =get_queryset_for_role(user)

        now_time=now()
        out_dated_qs=qs.filter(status='upcoming',date_time__lt=now_time)
        if out_dated_qs.exists():
            out_dated_qs.update(status='cancelled')
        return qs

        # status_param=self.request.query_params.get('filter')
        #
        # if status_param in ['today','upcoming','completed','cancelled']:
        #     qs=qs.filter(status=status_param)




    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment=serializer.save(
            created_by=request.user,
            status='upcoming',
            is_approved=True,
        )
        get_or_create_patient_history(appointment)
        return Response({
            "message": "Appointment created successfully","appointment": serializer.data
        },status=status.HTTP_201_CREATED)


    def perform_update(self, serializer):
        appoinment=serializer.save(
            status='upcoming',
            is_approved=True,
            cancelled_at=None
        )
        get_or_create_patient_history(appoinment)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        status_count=queryset.aggregate(
            total =Count('pk'),
            upcoming=Count('pk',filter=Q(status='upcoming')),
            completed=Count('pk',filter=Q(status='completed')),
            cancelled=Count('pk',filter=Q(status='cancelled')),
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
        get_or_create_patient_history(appointment)
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
        get_or_create_patient_history(appointment)
        return Response({
            "message":"Your Appointment has been completed",
            "appointment":self.get_serializer(appointment).data
        },status=status.HTTP_200_OK)

    @action(detail=True,methods=['patch'],permission_classes=[IsAuthenticated,CanUpdateAppointments])
    def reschedule(self,request,pk=None):
        appointment = self.get_object()

        if appointment.status == 'cancelled':
            appointment.status = 'upcoming'
            appointment.cancelled_at=None
        new_datetime_str=request.data.get('date_time')

        if not new_datetime_str:
            return Response({"error":"New date_time is required"},status=status.HTTP_400_BAD_REQUEST)

        try:
            new_datetime = datetime.strptime(new_datetime_str.replace('Z', ''), "%Y-%m-%dT%H:%M:%S")
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
        get_or_create_patient_history(appointment)
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
            doctor=User.objects.get(user_id=doctor_id,select_role='doctor')

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
        qs=self.get_queryset().filter(status='upcoming',date_time__date= date.today()).order_by('date_time')
        serializer=self.get_serializer(qs,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)



    @action(detail=False,methods=['get'])
    def upcoming_schedule(self,request):
        qs = self.get_queryset().filter(status='upcoming',date_time__date__gt= date.today()).order_by("date_time")
        serializer=self.get_serializer(qs,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = User.objects.none()
    serializer_class = DoctorSerializers
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        return User.objects.filter(select_role='doctor').order_by('experience')

class StaffViewSet(viewsets.ModelViewSet):
    queryset = User.objects.none()
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        assigned_staff_ids= StaffManagement.objects.values_list('staff_id',flat=True)

        return User.objects.filter(select_role='staff').exclude(user_id__in=assigned_staff_ids)


class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all().order_by('id')
    serializer_class = DiagnosisSerializer
    permission_classes = [IsAuthenticated,CanCreateDiagnosis]
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        user=self.request.user

        if user.select_role == 'doctor':
            return Diagnosis.objects.filter(appointment__doctor=user)
        elif user.select_role == 'patient':
            return Diagnosis.objects.filter(appointment__created_by=user)
        elif user.select_role == 'staff':
            assigned_doctors=StaffManagement.objects.filter(staff=user).values_list('doctor',flat=True)
            return Diagnosis.objects.filter(appointment__doctor__in=assigned_doctors)
        return Diagnosis.objects.none()

    def perform_create(self, serializer):
        instance=serializer.save()
        get_or_create_patient_history(instance.appointment)





class LabReportViewSet(viewsets.ModelViewSet):
    queryset = LabReport.objects.all().order_by('id')
    serializer_class = LabReportSerializer
    permission_classes = [IsAuthenticated,CanCreateLabReport]
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        user=self.request.user

        if user.select_role == 'doctor':
            return LabReport.objects.filter(appointment__doctor=user)
        if user.select_role == 'patient':
            return LabReport.objects.filter(appointment__created_by=user)
        if user.select_role == 'staff':
            assigned_doctors=StaffManagement.objects.filter(staff=user).values_list('doctor',flat=True)
            return LabReport.objects.filter(appointment__doctor__in=assigned_doctors)
        return LabReport.objects.none()

    def perform_create(self, serializer):
        instance=serializer.save()
        get_or_create_patient_history(instance.appointment)




class PatientHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = PatientHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        user = self.request.user

        if user.select_role == 'doctor':
            return PatientHistory.objects.filter(appointment__doctor=user).select_related(
                'appointment','appointment__diagnosis').prefetch_related(
                'appointment__lab_report_appointment'
            )
        elif user.select_role == 'patient':
            return PatientHistory.objects.filter(appointment__created_by=user).select_related(
                'appointment','appointment__diagnosis').prefetch_related(
                'appointment__lab_report_appointment'
            )
        elif user.select_role == 'staff':
            assigned_doctors = StaffManagement.objects.filter(staff=user).values_list('doctor', flat=True)
            return PatientHistory.objects.filter(appointment__doctor__in=assigned_doctors).select_related(
                'appointment','appointment__diagnosis').prefetch_related(
                'appointment__lab_report_appointment'
            )
        return PatientHistory.objects.none()






class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer



class StaffDashBoardViewSet(viewsets.ModelViewSet):
    queryset = StaffManagement.objects.none()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']


    def list (self,request):
        staff_user=request.user

        try:
            staff_info=StaffManagement.objects.get(staff=staff_user)
        except StaffManagement.DoesNotExist:
            return Response({"detail":"Staff not assigined"})
        doctor=staff_info.doctor
        appointments=Appointment.objects.filter(doctor=doctor)
        today=localdate()

        total_appointments=appointments.count()
        new_patients=appointments.filter(created_at__date=today).count()
        checked_in_patients=appointments.filter(status='completed').count()
        pending_patients=appointments.filter(status='upcoming',created_at__date__lt=today).count()

        new_appointments=appointments.filter(created_at__date=today).order_by('-created_at')
        pending_appointments=appointments.filter(
            status='upcoming',
            created_at__date__lt=today,
        ).order_by('-created_at')

        def serialize_appointments(qs):
            if not qs.exists():
                return None
            return [
                {
                    "time":localtime(a.date_time).strftime('%I:%M %p'),
                    "date": localtime(a.date_time).strftime('%d/%m/%Y'),
                    "patient_name": a.patient,
                    "checkup_type": a.appointment_type,
                    "status": a.status,
                } for a in qs
            ]
        completed_count=appointments.filter(status='completed').count()
        upcoming_count=appointments.filter(status='upcoming').count()
        pending_count=appointments.filter(status='pending').count()
        recovered_count=PatientHistory.objects.filter(appointment__doctor=doctor,status='recovered').count()

        total_chart=completed_count+upcoming_count+pending_count+recovered_count


        def percent(x):
            return round(x/total_chart * 100,2) if total_chart else 0

        chart_data={
            "completed_appointments": percent(completed_count),
            "recovered_patients": percent(recovered_count),
            "upcoming_appointments": percent(upcoming_count),
            "pending_appointments": percent(pending_count),
        }

        return Response({
            "staff_info":{
                "role":staff_info.staff_role,
                "time":f"{staff_info.start_time.strftime('%I:%M %p')} - {staff_info.end_time.strftime('%I:%M %p')}"
                if staff_info.start_time and staff_info.end_time else "",
                "duty":staff_info.duty,
            },
            "overview":{
                "total_appointments":total_appointments,
                "new_patients":new_patients,
                "checked_in_patients":checked_in_patients,
                "pending_patients":pending_patients,
            },
            "new_appointments":serialize_appointments(new_appointments),
            "pending_appointments":serialize_appointments(pending_appointments),
            "chart_data":chart_data,
        })


class DoctorDashBoardViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.none()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def list (self,request):
        doctor_user=request.user

        if doctor_user.select_role!='doctor':
            return Response({"detail":"access denied Only Doctor can access this dashboard"},status=status.HTTP_403_FORBIDDEN)
        doctor=doctor_user

        appointments=Appointment.objects.filter(doctor=doctor)
        today=localdate()

        total_appointments=appointments.count()
        new_patients=appointments.filter(created_at__date=today).count()
        total_active_staff=StaffManagement.objects.filter(doctor=doctor,staff__is_active=True).count()
        pending_appointment=appointments.filter(status='upcoming',created_at__date__lt=today).count()


        new_appointments=appointments.filter(created_at__date=today).order_by('-created_at')
        pending_appointments=appointments.filter(status='upcoming',created_at__date__lt=today).order_by('-created_at')


        def serialize_appointments(qs):
            if not qs.exists():
                return None
            return [
                {
                    "time": localtime(a.date_time).strftime('%I:%M %p'),
                    "date": localtime(a.date_time).strftime('%d/%m/%Y'),
                    "patient_name": a.patient,
                    "checkup_type": a.appointment_type,
                    "status": a.status,
                } for a in qs
            ]

        completed_count=appointments.filter(status='completed').count()
        upcoming_count=appointments.filter(status='upcoming').count()
        pending_count=appointments.filter(status='pending').count()
        recovered_count=PatientHistory.objects.filter(appointment__doctor=doctor,status='recovered').count()

        total_chart=completed_count+upcoming_count+pending_count+recovered_count

        def percent(x):
            return round(x / total_chart * 100, 2) if total_chart else 0

        chart_data = {
            "completed_appointments": percent(completed_count),
            "recovered_patients": percent(recovered_count),
            "upcoming_appointments": percent(upcoming_count),
            "pending_appointments": percent(pending_count),
        }

        return Response({
            "overview": {
                "total_appointments": total_appointments,
                "new_patients": new_patients,
                "active_staff": total_active_staff,
                "pending_appointments": pending_appointment,
            },
            "new_appointments": serialize_appointments(new_appointments),
            "pending_appointments": serialize_appointments(pending_appointments),
            "chart": chart_data,
        })

class PatientDashboardViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.none()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def list (self,request):
        patient_user=request.user

        if patient_user.select_role!='patient':
            return Response ({'error':'permission denied'})


        appointments=Appointment.objects.filter(created_by=patient_user)
        today=localdate()
        today_appointments=appointments.filter(created_at__date=today).count()
        cancelled_appointments=appointments.filter(status='cancelled').count()
        completed_appointments=appointments.filter(status='completed').count()
        upcoming_appointments=appointments.filter(status='upcoming',created_at__date__lt=today).count()


        lab_reports_qs=LabReport.objects.filter(appointment__created_by=patient_user).select_related('appointment')
        lab_reports=[
            {
                "test_name":report.test_name,
                "results":report.results,
                "laboratory":report.laboratory,
                "date": report.date.strftime('%d/%m/%Y %I:%M %p'),
            }
            for report in lab_reports_qs
        ]
        diagnosis_qs = Diagnosis.objects.filter(appointment__created_by=patient_user).prefetch_related(
            'diagnosis_detail', 'appointment__doctor')

        diagnosis_history = []
        for diagnosis in diagnosis_qs:
            disease_detail = diagnosis.diagnosis_detail.filter(diagnosis_type='diagnosis').first()
            disease_name = disease_detail.text if disease_detail else "Not specified"

            diagnosis_history.append({
                "appointment_date": diagnosis.created_at.strftime('%d/%m/%Y'),
                "doctor": f"Dr. {diagnosis.appointment.doctor.username}" if diagnosis.appointment.doctor else "N/A",
                "clinic": diagnosis.appointment.doctor.address if hasattr(diagnosis.appointment.doctor,'address') else "N/A",
                "disease": disease_name,
            })
            medicine_chart=get_medicine_chart(patient_user)

        return Response({
            "patient_user":{
                "gender": patient_user.gender,
                "date_of_birth": patient_user.date_of_birth.strftime('%m/%d/%Y') if patient_user.date_of_birth else None,
                "phone_number":patient_user.phone_number,
                "email":patient_user.email
            },
            "overview": {
                "today_appointments": today_appointments,
                "cancelled_appointments": cancelled_appointments,
                "completed_appointments": completed_appointments,
                "upcoming_appointments": upcoming_appointments,
            },
            'lab_reports': lab_reports,
            'diagnosis_data': diagnosis_history,
            'medicine_chart': medicine_chart,
        })



class FCMDeviceAuthorizedViewSet(AuthorizedMixin,FCMDeviceViewSet):
    serializer_class = FCMDeviceSerializer
    queryset = FCMDevice.objects.all()


class AppointmentReminderViewSet(viewsets.ModelViewSet):
    queryset = AppointmentReminder.objects.all()
    serializer_class = AppointmentReminderSerializer
    permission_classes = [IsAuthenticated]



class  MedicineReminderViewSet(viewsets.ModelViewSet):
    queryset = MedicineReminder.objects.all()
    serializer_class = MedicineReminderSerializer
    permission_classes = [IsAuthenticated]





class PaymentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    @action(detail=False, methods=['post'])
    def create_payment_method(self,request):
        try:
            test_tokens={
                'visa': 'tok_visa',
                'visa_debit': 'tok_visa_debit',
                'mastercard': 'tok_mastercard',
                'amex': 'tok_amex',
                'discover': 'tok_discover',
                'jcb': 'tok_jcb',
            }
            required_filed={
                'card_type=model.Mae':'visa',
                'card_number':'0000000000000000',
                'card_holder_name':'card_holder_name',
                'exp_month':'expiry_month',
                'exp_year':'expiry_year',
                'cvv':'cvv or cvc',
            }
            missing_fields={
                field:example for field,example in required_filed.items()
                if not request.data.get('field')
            }
            if missing_fields:
                return Response({
                    'status':'failed',
                    'message':'Missing  required fields',
                    'messing_fields':missing_fields,
                },status=status.HTTP_400_BAD_REQUEST)
            card_type=request.data['card_type']
            token=test_tokens.get(card_type)
            if not token:
                return Response({
                    'status':'failed',
                    'message':f"Unsupported card type '{card_type}'.use one of {', '.join(test_tokens.keys())}"
                },status=status.HTTP_400_BAD_REQUEST)
            card_number=request.data['card_number']
            if not card_number.isdigit() or len(card_number)!=16:
                return Response({
                    'status':'failed',
                    'message':'Invalid 16 digit card number',
                    'format':{'card_number':'1234567890123456'}
                },status=status.HTTP_400_BAD_REQUEST)
            payment_method=stripe.PaymentMethod.create(
                type='card',
                card={'token':token},
                billing_details={'name':request.data['card_holder_name']}
            )
            return Response({
                'status': 'success',
                'payment_method_id': payment_method.id,
                'card_type': payment_method.card.brand,
                'card_number': card_number,
                'card_holder_name': request.data['card_holder_name'],
                'exp_month': request.data['exp_month'],
                'exp_year': request.data['exp_year'],
                'cvv': request.data['cvv']
            })
        except stripe.error.StripeError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['post'])
    def create_payment_intent_id(self,request):
        try:
            latest_appointment=Appointment.objects.filter(user=request.user).order_by('-created_at').first()
            if not latest_appointment:
                return Response({'error':'No latest appointment found'},status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)},status=status.HTTP_400_BAD_REQUEST)
