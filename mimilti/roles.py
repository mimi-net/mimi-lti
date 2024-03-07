import functools
from typing import Callable
from abc import abstractmethod
from mimilti.data_storage import DataStorage


class Role(object):
    privileges = tuple()

    @abstractmethod
    def has_privileges(self, role_name):
        pass


class ContextRole(Role):
    privileges = tuple()

    @abstractmethod
    def has_privileges(self, role_name):
        pass


class ContextAdminRole(ContextRole):
    privileges = ("Administrator",)

    def has_privileges(self, role_name):
        return role_name in self.privileges


class ContextInstructorRole(ContextRole):
    privileges = ContextAdminRole.privileges + ("Instructor",)

    def has_privileges(self, role_name):
        return role_name in self.privileges


class LearnerRole(ContextRole):
    privileges = ContextInstructorRole.privileges + ("Learner",)

    def has_privileges(self, role_name):
        return role_name in self.has_privileges


class RoleService[R: Role]:
    def __init__(self, data_service: DataStorage) -> None:
        self._data_service = data_service

    def user_has_role_privileges(self, role: type[R]) -> bool:
        return role().has_privileges(self._data_service.main_context_role_name)

    def lti_role_accepted[
        T, **P
    ](self, role: type[R]) -> Callable[[Callable[P, T]], Callable[P, T]]:
        def wraps(func: Callable[P, T]) -> Callable[P, T]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if not self.user_has_role_privileges(role):
                    return "You do not have permission to this action"
                return func(*args, **kwargs)

            return wrapper

        return wraps
