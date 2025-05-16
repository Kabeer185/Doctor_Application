from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework.response import Response
from rest_framework.views import APIView


class ApiRootView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({
            'google_login': request.build_absolute_uri('/google/'),
            'facebook_login': request.build_absolute_uri('/facebook/'),
        })


router = DefaultRouter()
router.register(r'signup',SignUpView,basename='signup')
router.register(r'varifyotp',VerifyOTPView,basename='varifyotp')

router.register(r'login',LoginView,basename='login')
router.register(r'profession',ProfessionViewSet,basename='profession')
router.register(r'certification',CertificationViewSet,basename='certification')
router.register(r'publication',PublicationViewSet,basename='publication')
router.register(r'awards',AwardsViewSet,basename='awards')
router.register(r'emrgency_contact',EmergencyContactViewSet,basename='emrgency_contact')
router.register(r'mainprofile',MainProfileViewSet,basename='mainprofile')
router.register(r'patientprofile',PatientProfileViewSet,basename='patientprofile')





urlpatterns = [
    path('',include(router.urls)),
    path(r'regenerateotp/',RegenerateOTPView.as_view(),name='regenerate_otp'),
    path(r'password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    path('accounts/', include('allauth.urls'), name='socialaccount_signup'),
    path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('google/',GoogleConnect.as_view(),name='google_connect'),
    path('facebook/',FacebookConnect.as_view(),name='facebook_connect'),
    path('redirect/',UserRedirectView.as_view(),name='redirect'),
    path('',ApiRootView.as_view(),name='api_root'),
]