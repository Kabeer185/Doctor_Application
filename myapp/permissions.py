from rest_framework.permissions import BasePermission
from.utils import is_lab_technician_staff,is_administrator_staff
from.models import Appointment



class CanCreateAppointments(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            if request.user.select_role == 'patient':
                return True
            elif request.user.select_role == 'staff':
                doctor_id = request.data.get('doctor')
                if doctor_id:
                    return is_administrator_staff(request.user, doctor_id)
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if view.action in ['update', 'partial_update']:
            if request.user.select_role == 'patient':
                return True
            elif request.user.select_role == 'staff':
                return is_administrator_staff(request.user, obj.doctor)
            return False
        return True


class CanCompleteAppointment(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'complete':
            if  request.user==obj.created_by and request.user.select_role == 'patient':
                return True

            if request.user.select_role == 'staff' and is_administrator_staff(request.user, obj.doctor):
                return True
            return False
        return True




class CanUpdateAppointments(BasePermission):
    def has_object_permission(self, request, view,obj):
        if view.action in['update','partial_update']:
            if request.user==obj.created_by and request.user.select_role =='patient':
                return True
            if request.user.select_role == 'staff' and is_administrator_staff(request.user, obj.doctor):
                return True
            return False
        return True



class CanCancelAppointments(BasePermission):
    def has_object_permission(self, request, view,obj):
        if view.action =='cancel':
            if request.user==obj.created_by and request.user.select_role =='patient':
                return True
            if request.user.select_role == 'staff' and is_administrator_staff(request.user, obj.doctor):
                return True
            return False
        return True


class CanCreateDiagnosis(BasePermission):
   def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.select_role == 'doctor'
        return True
   def has_object_permission(self, request, view, obj):
       if view.action in ['update','partial_update','destroy']:
           return request.user.select_role == 'doctor' and obj.patient.doctor == request.user
       return True

class CanCreateStaffManagement(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.select_role == 'doctor'
        return True


class CanCreateLabReport(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            appointment_id = request.data.get('appointment')
            if not appointment_id:
                return False
            try:
                appointment = Appointment.objects.select_related('doctor').get(id=appointment_id)
            except Appointment.DoesNotExist:
                return False

            return (
                    request.user.select_role == 'staff' and
                    is_lab_technician_staff(request.user, appointment.doctor)
            )
        return True

