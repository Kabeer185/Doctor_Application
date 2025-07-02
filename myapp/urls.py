from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.conf.urls.static import static



class ApiRootView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({
            'google_login': request.build_absolute_uri('/google/'),
            'facebook_login': request.build_absolute_uri('/facebook/'),
        })


router = DefaultRouter()
router.register(r'signup',SignUpView,basename='signup')
router.register(r'staff_management',StaffManagementViewSet,basename='staff_management')
router.register(r'varifyotp',VerifyOTPView,basename='varifyotp')
router.register(r'login',LoginView,basename='login')
router.register(r'profession',ProfessionViewSet,basename='profession')
router.register(r'certification',CertificationViewSet,basename='certification')
router.register(r'publication',PublicationViewSet,basename='publication')
router.register(r'awards',AwardsViewSet,basename='awards')
router.register(r'emrgency_contact',EmergencyContactViewSet,basename='emrgency_contact')
router.register(r'userprofile',UserProfileViewSet,basename='userprofile')
router.register(r'mainprofile',MainProfileViewSet,basename='mainprofile')
router.register(r'patientprofile',PatientProfileViewSet,basename='patientprofile')
router.register(r'workinghours',WorkingHoursViewSet,basename='workinghours')
router.register(r'questions',QuestionViewSet,basename='questions')
router.register(r'patientassessment',PatientAssessmentViewSet,basename='patientassessment')
router.register(r'web_questions',WebQuestionViewSet,basename='web_questions')
router.register(r'web_patientassessment',WebPatientAssessmentViewSet,basename='web_patientassessment')
router.register(r'faqs',FAQViewSet,basename='faqs')
router.register(r'doctors',DoctorViewSet,basename='doctors')
router.register(r'staff',StaffViewSet,basename='staff')
router.register(r'appointments',AppointmentViewSet,basename='appointments')
router.register(r'diagnosis_detail',DiagnosisViewSet,basename='diagnosis_detail')
router.register(r'lab_report',LabReportViewSet,basename='lab_report')
router.register(r'history',PatientHistoryViewSet,basename='history')
router.register(r'category',CategoryViewSet,basename='category')
router.register(r'staff_dashboard',StaffDashBoardViewSet,basename='staff_dashboard')
router.register(r'doctor_dashboard',DoctorDashBoardViewSet,basename='doctor_dashboard')
router.register(r'patient_dashboard',PatientDashboardViewSet,basename='patient_dashboard')
router.register(r'fcm',FCMDeviceAuthorizedViewSet,basename='fcm')
router.register(r'appointment_reminder',AppointmentReminderViewSet,basename='appointment_reminder')
router.register(r'medicine_reminder',MedicineReminderViewSet,basename='medicine_reminder')






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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)