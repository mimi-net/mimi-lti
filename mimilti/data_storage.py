import typing as tp
from typing import TypedDict, Sequence
from abc import abstractmethod, ABC
from flask import session


class DataStorage:
    def __init__(self):
        self._iss: str
        self._aud: str
        self._deployment_id: int
        self._sub: int
        self._roles: Sequence[str]
        self._context: TypedDict(
            "context", {"id": int, "label": str, "title": str, "type": str}
        )

    @property
    @abstractmethod
    def lineitems(self, *args, **kwargs):
        pass

    @lineitems.setter
    @abstractmethod
    def lineitems(self, lineitems: Sequence[str]):
        pass

    @property
    @abstractmethod
    def iss(self, *args, **kwargs):
        pass

    @iss.setter
    @abstractmethod
    def iss(self, iss: str):
        pass

    @property
    @abstractmethod
    def aud(self, *args, **kwargs):
        pass

    @aud.setter
    @abstractmethod
    def aud(self, aud: str):
        pass

    @property
    @abstractmethod
    def sub(self, *args, **kwargs):
        pass

    @sub.setter
    @abstractmethod
    def sub(self, sub: str):
        pass

    @property
    @abstractmethod
    def context_roles(self, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def roles(self, *args, **kwargs):
        pass

    @property
    @abstractmethod
    def context(self, *args, **kwargs):
        pass

    @staticmethod
    def inner_role_handler(role: str):
        if "#" in role:
            _, last = role.split("#")
            return last
        return role

    @staticmethod
    def role_handler(roles: list[str]):
        new_roles = {}

        for role in roles:
            role_part = DataStorage.inner_role_handler(role)
            if "institution" in role:
                new_roles["institution"] = role_part
            if "membership" in role:
                new_roles["context"] = role_part
            if "system" in role:
                new_roles["system"] = role_part
        return new_roles

    @property
    def main_context_role_name(self):
        context_roles = self.context_roles
        if "Administrator" in context_roles:
            return "Administrator"
        if "Instructor" in context_roles:
            return "Instructor"
        if "Mentor" in context_roles:
            return "Mentor"
        if "Learner" in context_roles:
            return "Learner"


class SessionStorage(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def session_validate(self, param: tp.Any, param_name: str) -> bool:
        pass

    @abstractmethod
    def get_param(self, param_name: str) -> str | None:
        pass

    @abstractmethod
    def save_param_to_session(self, param: tp.Any, param_name: str) -> None:
        pass

    @abstractmethod
    def remove_param_from_session(self, param_name: str) -> None:
        pass


class SessionDataStorage(DataStorage, SessionStorage):
    def __init__(self, lti_session=session):
        super().__init__()
        self._session = lti_session

    def session_validate(self, param: tp.Any, param_name: str) -> bool:
        return (
            False
            if param_name not in self._session
            else self._session[param_name] == param
        )

    def get_param(self, param_name: str) -> str | None:
        return self._session.get(param_name, None)

    def save_param_to_session(self, param: tp.Any, param_name: str) -> None:
        self._session[param_name] = param

    def remove_param_from_session(self, param_name: str) -> None:
        self._session.pop(param_name, None)

    @property
    def lineitems(self):
        return self._session.get("lineitems", None)

    @lineitems.setter
    def lineitems(self, lineitems: Sequence[str]):
        self._session["lineitems"] = lineitems

    @property
    def iss(self):
        return self._session.get("iss", None)

    @iss.setter
    def iss(self, iss: str):
        self._session["iss"] = iss

    @property
    def aud(self):
        return self._session.get("aud", None)

    @aud.setter
    def aud(self, aud: str):
        self._session["aud"] = aud

    @property
    def sub(self):
        return self._session.get("sub", None)

    @sub.setter
    def sub(self, sub: str):
        self._session["sub"] = sub

    @property
    def roles(self, *args, **kwargs):
        return self._session.get("roles", None)

    @property
    def context_roles(self):
        roles = self._session.get("roles", None)
        if roles is None:
            return None
        return roles.get("context", None)

    @property
    def context(self):
        return self._session.get("context", None)

    def update_params(self, data) -> None:
        if data is not None:
            self._init_params(data)

    def _init_params(self, data):
        if "iss" in data:
            self._session["iss"] = data.get("iss", None)

        if "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint" in data:
            self._session["lineitems"] = data[
                "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint"
            ]["lineitems"]

        if "aud" in data:
            self._session["aud"] = data["aud"]

        if "https://purl.imsglobal.org/spec/lti/claim/deployment_id" in data:
            self._session["deployment_id"] = data[
                "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
            ]

        if "sub" in data:
            self._session["sub"] = data.get("sub", None)

        if "https://purl.imsglobal.org/spec/lti/claim/roles" in data:
            self._session["roles"] = self.role_handler(
                data["https://purl.imsglobal.org/spec/lti/claim/roles"]
            )

        if "https://purl.imsglobal.org/spec/lti/claim/context" in data:
            self._session["context"] = data.get(
                "https://purl.imsglobal.org/spec/lti/claim/context", None
            )

        for x, y in data.items():
            self.save_param_to_session(y, x)
