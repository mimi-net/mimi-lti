import os
import pathlib
from datetime import datetime, timedelta

from flask import (
    jsonify,
    redirect,
    request,
    url_for,
    send_from_directory,
)


from mimilti.grade import LineItem, GradeService, Progress
from mimilti.login import LtiRequestObject
from mimilti.data_storage import SessionDataStorage
from mimilti.config import Config, RsaKey
from mimilti.roles import (
    ContextInstructorRole,
    RoleService,
)
from mimilti.lms_pool import LmsRequestsPool

public_key_path = os.path.join(pathlib.Path(__file__).parent, "config/public.key")
private_key_path = os.path.join(pathlib.Path(__file__).parent, "config/private.key")
public_json_path = os.path.join(pathlib.Path(__file__).parent, "config/config.json")

key = RsaKey(private_key_path, public_key_path)
config = Config(public_json_path, key)
LmsRequestsPool.start(config)


def get_lti_request_object():
    pass


def get_jwks():
    return send_from_directory(
        os.path.join(pathlib.Path(__file__).parent, "config/"), "jwk.json"
    )


def login():
    if request.method == "POST":
        session_service = SessionDataStorage()
        try:
            request_object = LtiRequestObject(request.form, session_service, config)
        except Exception as e:
            return jsonify({"error": str(e)}), 401

        redirect_url = request_object.get_redirect_url()
        issuer = request_object.get_issuer()

        next_url = request.args.get("next")

        session_service.iss = issuer
        session_service.aud = request_object.get_client_id()

        if next_url:
            session_service.save_param_to_session(next_url, "next_url")
        else:
            session_service.remove_param_from_session("next_url")

        return redirect(redirect_url)


def launch():
    if request.method == "POST":
        session_data_service = SessionDataStorage()

        request_object = LtiRequestObject(request.form, session_data_service, config)

        try:
            data = request_object.get_token()
            session_data_service.update_params(data)
            config.add_tool(session_data_service.iss, session_data_service.aud)
        except Exception as e:
            return jsonify({"error": str(e)}), 401

        # you login logic

        if (next_url := session_data_service.get_param("next_url")) is None:
            return redirect(url_for("index"))

        else:
            session_data_service.remove_param_from_session("next_url")
            return redirect(next_url)


def get_role_service():
    data_service = SessionDataStorage()
    role_service = RoleService(data_service)
    return role_service


@get_role_service().lti_role_accepted(ContextInstructorRole)
def create_test():

    test_guid = "7262dd22-ae2b-4a88-8d29-dfcf728b2c11"
    test_label = "test ugugugu"
    test_tag = "test tag"
    test_maximum_score = 100
    test_start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    test_end_time = (datetime.now() + timedelta(seconds=3600)).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )

    data_service = SessionDataStorage()
    grade_service = GradeService(data_service, config)
    lineitems = LineItem(
        id=None,
        label=test_label,
        score_maximum=test_maximum_score,
        resource_id=test_guid,
        tag=test_tag,
        start_date_time=test_start_time,
        end_date_time=test_end_time,
    )

    grade_service.create_or_set_lineitem(lineitems)
    return ""


def get_grade():
    guid = "7262dd22-ae2b-4a88-8d29-dfcf728b2c11"
    data_service = SessionDataStorage()
    grade_service = GradeService(data_service, config)
    print(grade_service.get_grade(guid))
    return ""


def set_grade():
    data_service = SessionDataStorage()
    guid = "7262dd22-ae2b-4a88-8d29-dfcf728b2c11"
    grade_service = GradeService(data_service, config)
    progress = Progress(
        score_given=50,
        score_maximum=100,
        activity_progress="Completed",
        grading_progress="FullyGraded",
        user_id=data_service.sub,
        comment="comment",
        timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    grade_service.set_grade(progress, guid)
    return ""
