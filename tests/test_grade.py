import datetime
import json

from mimilti.config import Config
from mimilti.grade import GradeService
from mimilti.grade import LineItem, LineItemSchema
from mimilti.data_storage import SessionDataStorage
from test_config import rsa_key, config_path

config = Config(config_path, rsa_key)


class FakeLMSClient:
    def __init__(self, value):
        self._data_service = SessionDataStorage(
            lti_session={
                "lineitems": "",
                "iss": "http://localhost/moodle",
                "aud": "asdasdasdfrfrfrfrfrfrfrfrre",
            }
        )
        self.value = value
        self._grade_service = GradeService(self._data_service, config)

    def json(self):
        return self.value

    @property
    def lms_client(self):
        return self._grade_service.client

    @property
    def grade_service(self):
        return self._grade_service


def test_fake_refresh_lineitems(mocker):
    time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    lineitems1 = LineItem(
        id="fake_id1",
        label="fake_label1",
        score_maximum=100,
        resource_id="fake_rid1",
        tag="fake_tag1",
        resource_link_id="fake_rlid1",
        lti_link_id="1",
        start_date_time=time,
        end_date_time=time,
    )

    lineitem_schema = LineItemSchema()

    value = [json.loads(lineitem_schema.dumps(lineitems1))]
    fake_client = FakeLMSClient(value)
    mocker.patch.object(
        fake_client.lms_client, "send_request_to_lms", return_value=fake_client
    )
    assert [lineitems1] == fake_client.grade_service.refresh_lineitems()
    assert [lineitems1] == fake_client.grade_service.lineitems


def test_find_lineitem_by_resource_id(mocker):
    time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    lineitem1 = LineItem(
        id="fake_id1",
        label="fake_label1",
        score_maximum=100,
        resource_id="fake_rid1",
        tag="fake_tag1",
        resource_link_id="fake_rlid1",
        lti_link_id="1",
        start_date_time=time,
        end_date_time=time,
    )

    lineitem2 = LineItem(
        id="fake_id2",
        label="fake_label2",
        score_maximum=100,
        resource_id="fake_rid2",
        tag="fake_tag1",
        resource_link_id="fake_rlid2",
        lti_link_id="2",
        start_date_time=time,
        end_date_time=time,
    )

    lineitem_schema = LineItemSchema()
    value = [
        json.loads(lineitem_schema.dumps(lineitem1)),
        json.loads(lineitem_schema.dumps(lineitem2)),
    ]

    fake_client = FakeLMSClient(value)
    mocker.patch.object(
        fake_client.lms_client, "send_request_to_lms", return_value=fake_client
    )
    fake_client.grade_service.refresh_lineitems()

    lineitem_index_by_resource_id = (
        fake_client.grade_service.find_lineitem_index_by_resource_id("fake_rid1")
    )
    nonexistent_lineitem_index_by_resource_id = (
        fake_client.grade_service.find_lineitem_index_by_resource_id("123123")
    )

    lineitems_by_tag = fake_client.grade_service.find_lineitems_by_tag("fake_tag1")
    nonexistent_lineitem_by_tag = fake_client.grade_service.find_lineitems_by_tag(
        "123123"
    )

    assert (
        lineitem1 == fake_client.grade_service.lineitems[lineitem_index_by_resource_id]
    )
    assert nonexistent_lineitem_index_by_resource_id is None
    assert lineitems_by_tag == [lineitem1, lineitem2]
    assert nonexistent_lineitem_by_tag == []
