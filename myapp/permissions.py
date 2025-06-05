from rest_framework.permissions import BasePermission, SAFE_METHODS

class CanCreateAppointments(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'create':
            return  request.user.select_role in('patient','staff')
        return True


class CanCompleteAppointment(BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'complete':
            return request.user==obj.created_by and request.user.select_role == 'staff'
        return True



class CanUpdateAppointments(BasePermission):
    def has_object_permission(self, request, view,obj):
        if view.action in['update','partial_update']:
            return request.user==obj.created_by and request.user.select_role in('patient','staff')
        return True


class CanCancelAppointments(BasePermission):
    def has_object_permission(self, request, view,obj):
        if view.action =='cancel':
            return request.user==obj.created_by and request.user.select_role in('patient','staff')
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



