from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.views.generic import RedirectView
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import *
from .utils import *
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import *

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
                return Response({'message':'Login Successfully','email':email,'role':user.select_role,'access_token':access_token,'refresh_token':str(refresh)},status=status.HTTP_200_OK)

            return Response({'error':'Invalid Credentials'},status=status.HTTP_401_UNAUTHORIZED)

        return Response({"error":"Username or Password Incorrect "}, status=status.HTTP_400_BAD_REQUEST)



class UserRedirectView(RedirectView,LoginRequiredMixin):
    permanent = False
    def get_redirect_url(self):
        return "http://127.0.0.1"



class GoogleConnect(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class=OAuth2Client



class FacebookConnect(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    authentication_classes = []
    permission_classes = []



class ProfessionViewSet(viewsets.ModelViewSet):
    queryset = Profession.objects.all()
    serializer_class = ProfessionSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile = get_or_create_main_profile(self.request.user)
        profile.profession = instance
        profile.save()



class CertificationViewSet(viewsets.ModelViewSet):
    queryset = Certification.objects.all()
    serializer_class = CertificationSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile = get_or_create_main_profile(self.request.user)
        profile.certificate.add(instance)


class PublicationViewSet(viewsets.ModelViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile = get_or_create_main_profile(self.request.user)
        profile.publications.add(instance)



class AwardsViewSet(viewsets.ModelViewSet):
    queryset = Awards.objects.all()
    serializer_class = AwardsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile = get_or_create_main_profile(self.request.user)
        profile.awards.add(instance)



class EmergencyContactViewSet(viewsets.ModelViewSet):
    queryset = EmergencyContact.objects.all()
    serializer_class = EmergencyContactSerializer
    permission_classes = [IsAuthenticated]


    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        profile=get_or_create_patient_profile(self.request.user)
        profile.emergency_contact=instance
        profile.save()





class MainProfileViewSet(viewsets.ModelViewSet):
    serializer_class = MainProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']
    def get_queryset(self):
        return  MainProfile.objects.select_related('user', 'profession').prefetch_related('certificate', 'Publication', 'awards').filter(user=self.request.user)

class PatientProfileViewSet(viewsets.ModelViewSet):
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        return PatientProfile.objects.select_related('user','emergency_contact').filter(user=self.request.user)

