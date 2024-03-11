from mimilti.data_storage import SessionDataStorage


def test_lti_data_service():
    data_service = SessionDataStorage(lti_session={})

    data_service.save_param_to_session(123, "param")
    assert data_service.get_param("param") == 123
    assert data_service.session_validate(123, "param")
    data_service.remove_param_from_session("param")
    assert data_service.get_param("param") is None

    lti_data = {
        "nonce": "519e0358a32b4fb9aeebadf2190cbaa181e21178cd2711ee900e752d331c1a83",
        "iat": 1708128006,
        "exp": 1708128066,
        "iss": "http://localhost/moodle",
        "aud": "qwewqwqeqwewqewq",
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "4",
        "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "http://127.0.0.1:9002/launch",
        "sub": "2",
        "https://purl.imsglobal.org/spec/lti/claim/lis": {
            "person_sourcedid": "",
            "course_section_sourcedid": "",
        },
        "https://purl.imsglobal.org/spec/lti/claim/roles": [
            "http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator",
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor",
            "http://purl.imsglobal.org/vocab/lis/v2/system/person#Administrator",
        ],
        "https://purl.imsglobal.org/spec/lti/claim/context": {
            "id": "2",
            "label": "aaaa",
            "title": "Aaaa",
            "type": ["CourseSection"],
        },
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
        "https://purl.imsglobal.org/spec/lti/claim/resource_link": {
            "title": "ad",
            "description": "",
            "id": "7",
        },
        "https://purl.imsglobal.org/spec/lti-bo/claim/basicoutcome": {
            "lis_result_sourcedid": '{"data":{"instanceid":"7","userid":"2","typeid":"4","launchid":295466899},'
            '"hash":"4c8230bb7113f6410fc9664451b01ee0915b012e235d21323aaf8cf2081cd694"}',
            "lis_outcome_service_url": "http://localhost/moodle/mod/lti/service.php",
        },
        "given_name": "Admin",
        "family_name": "User",
        "name": "Admin User",
        "https://purl.imsglobal.org/spec/lti/claim/ext": {
            "user_username": "admin",
            "lms": "moodle-2",
        },
        "email": "eeuriset@gmail.com",
        "https://purl.imsglobal.org/spec/lti/claim/launch_presentation": {
            "locale": "en",
            "document_target": "window",
            "return_url": "http://localhost/moodle/mod/lti/return.php?course=2&launch_container=4&instanceid=7"
            "&sesskey=lcaBrFzpIX",
        },
        "https://purl.imsglobal.org/spec/lti/claim/tool_platform": {
            "product_family_code": "moodle",
            "version": "2023100903",
            "guid": "localhost",
            "name": "moodle",
            "description": "mooodle",
        },
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint": {
            "scope": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            ],
            "lineitems": "http://localhost/moodle/mod/lti/services.php/2/lineitems?type_id=4",
            "lineitem": "http://localhost/moodle/mod/lti/services.php/2/lineitems/11/lineitem?type_id=4",
        },
        "https://purl.imsglobal.org/spec/lti/claim/custom": {
            "context_memberships_url": "http://localhost/moodle/mod/lti/services.php/CourseSection/2/bindings/4"
            "/memberships",
            "system_setting_url": "http://localhost/moodle/mod/lti/services.php/tool/4/custom",
            "context_setting_url": "http://localhost/moodle/mod/lti/services.php/CourseSection"
            "/2/bindings/tool/4/custom",
            "link_setting_url": "http://localhost/moodle/mod/lti/services.php/links/{link_id}/custom",
        },
        "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice": {
            "context_memberships_url": "http://localhost/moodle/mod/lti/services.php/CourseSection/2/bindings/4"
            "/memberships",
            "service_versions": ["1.0", "2.0"],
        },
    }
    data_service.update_params(lti_data)
    assert data_service.iss == "http://localhost/moodle"
    assert (
        data_service.lineitems
        == "http://localhost/moodle/mod/lti/services.php/2/lineitems?type_id=4"
    )

    assert data_service.aud == "qwewqwqeqwewqewq"
    data_service.aud = "bebra"
    assert data_service.aud == "bebra"

    assert data_service.sub == "2"
    data_service.sub = 3
    assert data_service.sub == 3

    assert data_service.roles == {
        "context": "Instructor",
        "institution": "Administrator",
        "system": "Administrator",
    }

    assert data_service.context == {
        "id": "2",
        "label": "aaaa",
        "title": "Aaaa",
        "type": ["CourseSection"],
    }

    data_service.update_params({"roles": {"context": "Administrator"}})
    assert data_service.main_context_role_name == "Administrator"

    data_service.update_params({"roles": {"context": "Instructor"}})
    assert data_service.main_context_role_name == "Instructor"

    data_service.update_params({"roles": {"context": "Learner"}})
    assert data_service.main_context_role_name == "Learner"
