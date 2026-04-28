from rest_framework import permissions


class DepartmentPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        print(request.user, request.user.has_perm('defects.can_view_department_defects'))
        # Администратор видит всё
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Проверяем наличие разрешения у пользователя
        print(request.user, request.user.has_perm('defects.can_view_department_defects'))
        return request.user.has_perm('defects.can_view_department_defects')