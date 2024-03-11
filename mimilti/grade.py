import dataclasses
import datetime
from marshmallow import Schema, fields, post_load

from mimilti.lms_client import LMSClient
from dataclasses import dataclass
from mimilti.data_storage import DataStorage
from mimilti.config import Config


@dataclass
class LineItem:
    id: str | None = None
    label: str | None = None
    score_maximum: int | None = None
    resource_id: str | None = None
    tag: str | None = None
    resource_link_id: str | None = None
    lti_link_id: str | None = None
    start_date_time: str | None = None
    end_date_time: str | None = None


class LineItemSchema(Schema):
    id = fields.String(data_key="id")
    label = fields.String(data_key="label")
    score_maximum = fields.Integer(data_key="scoreMaximum")
    resource_id = fields.String(data_key="resourceId")
    tag = fields.String(data_key="tag")
    resource_link_id = fields.String(data_key="resourceLinkId")
    lti_link_id = fields.String(data_key="ltiLinkId")
    start_date_time = fields.String(data_key="startDateTime")
    end_date_time = fields.String(data_key="endDateTime")

    @post_load
    def make_lineitem(self, data, **kwargs):
        _ = kwargs
        return LineItem(**data)


class ProgressSchema(Schema):
    score_given = fields.Number(data_key="scoreGiven")
    score_maximum = fields.Number(data_key="scoreMaximum")
    activity_progress = fields.String(data_key="activityProgress")
    grading_progress = fields.String(data_key="gradingProgress")
    user_id = fields.String(data_key="userId")
    comment = fields.String(data_key="comment")
    timestamp = fields.String(data_key="timestamp")

    @post_load
    def make_progress(self, data, **kwargs):
        _ = kwargs
        return Progress(**data)


@dataclass
class Progress:
    score_given: int | None = None
    score_maximum: int | None = None
    activity_progress: str | None = None
    grading_progress: str | None = None
    user_id: str | None = None
    comment: str | None = None
    timestamp: str | None = None


@dataclass
class Grade:
    id: int | None = None
    user_id: int | None = None
    result_score: str | None = None
    result_maximum: str | None = None
    score_of: int | None = None
    timestamp: str | None = None


class GradeSchema(Schema):
    id = fields.String(data_key="id")
    user_id = fields.String(data_key="userId")
    result_score = fields.Number(data_key="resultScore")
    result_maximum = fields.Number(data_key="resultMaximum")
    score_of = fields.String(data_key="scoreOf")
    timestamp = fields.String(data_key="timestamp")

    @post_load
    def make_grade(self, data, **kwargs):
        _ = kwargs
        return Grade(**data)


class GradeService:
    def __init__(self, data_service: DataStorage, config: Config):
        self._lms_client = LMSClient(data_service, config)
        self._data_service = data_service
        self._scopes = [
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
        ]
        self._lineitem_schema = LineItemSchema()
        self._lineitems: list[LineItem] = []
        self._grade_schema = GradeSchema()
        self._progress_schema = ProgressSchema()
        self._grades: list[Grade] = []
        self._lineitem_expires = datetime.timedelta(seconds=0)
        self._grade_expires = datetime.timedelta(seconds=0)

    @property
    def client(self):
        return self._lms_client

    @property
    def lineitems(self):
        return self._lineitems

    @lineitems.setter
    def lineitems(self, lineitems: list[LineItem]):
        self._lineitems = lineitems

    def refresh_lineitems(self):
        lineitems_url = self._data_service.lineitems

        if lineitems_url is None:
            return None

        response = self._lms_client.send_request_to_lms(
            self._scopes,
            lineitems_url,
            accept="application/vnd.ims.lis.v2.lineitemcontainer+json",
            content_type="application/json",
            request_type="GET",
            need_token=True,
        )

        if response is None:
            return None

        lineitems = LMSClient.get_json(response)

        self._lineitems = [
            self._lineitem_schema.load(lineitem) for lineitem in lineitems
        ]

        return self._lineitems

    def find_lineitem_index_by_resource_id(self, resource_id: str) -> int | None:
        for index, lineitem in enumerate(self._lineitems):
            if lineitem.resource_id == resource_id:
                return index
        return None

    def find_lineitems_by_tag(self, tag) -> list[LineItem]:
        return [lineitem for lineitem in self._lineitems if lineitem.tag == tag]

    @staticmethod
    def get_payload(data, schema: Schema) -> str:
        data = {x: y for x, y in data.items() if y is not None}
        return schema.dumps(data)

    def create_or_set_lineitem(self, lineitem: LineItem) -> LineItem:
        target_index = self.find_lineitem_index_by_resource_id(lineitem.resource_id)

        is_new_lineitem = True

        url = self._data_service.lineitems

        if target_index is None:
            self._lineitems = self.refresh_lineitems()

            target_index = self.find_lineitem_index_by_resource_id(lineitem.resource_id)

            if target_index is not None:
                target: LineItem = self._lineitems[target_index]
                lineitem.resource_id = target.resource_id
                lineitem.resource_label = target.resource_link_id
                lineitem.tag = target.tag
                lineitem.lti_link_id = target.lti_link_id
                lineitem.id = target.id
            else:
                is_new_lineitem = True

        if is_new_lineitem:

            data = GradeService.get_payload(
                dataclasses.asdict(lineitem), self._lineitem_schema
            )

            _ = self._lms_client.send_request_to_lms(
                scopes=self._scopes,
                url=url,
                accept="application/vnd.ims.lis.v2.lineitem+json",
                content_type="application/vnd.ims.lis.v2.lineitem+json",
                request_type="POST",
                data=data,
                need_token=True,
            )

            self._lineitems.append(lineitem)
            return lineitem

        self._lineitems[target_index] = lineitem
        return lineitem

    def find_grade_index_by_score_of(self, score_of: str) -> int | None:
        for index, grade in enumerate(self._grades):
            if grade.score_of == score_of:
                return index

    def get_grade(self, lineitem_id: str):
        index = self.find_lineitem_index_by_resource_id(lineitem_id)

        if index is None:
            return None

        lineitem = self._lineitems[index]
        url = lineitem.id

        index = self.find_grade_index_by_score_of(url)

        if index is not None:
            return self._grades[index]

        url = GradeService._moodle_url_handler(url, "results")

        response = self._lms_client.send_request_to_lms(
            self._scopes,
            url,
            accept="application/vnd.ims.lis.v2.resultcontainer+json",
            content_type="application/json",
            request_type="GET",
            need_token=True,
        )

        grades = LMSClient.get_json(response)
        for grade in grades:
            self._grades.append(self._grade_schema.load(grade))

        return self._grades

    # 'http://127.0.0.1/moodle/mod/lti/services.php/2/lineitems?type_id=4' ->
    # 'http://127.0.0.1/moodle/mod/lti/services.php/2/lineitems/scores?type_id=4'
    @staticmethod
    def _moodle_url_handler(url: str, end: str) -> str:
        if "?" in url:
            url, url_end = url.split("?")
            end += "?" + url_end
        url += "" if url[-1] == "/" else "/"
        return url + end

    def set_grade(
        self,
        progress: Progress,
        lineitem_id: str,
    ):
        index = self.find_lineitem_index_by_resource_id(lineitem_id)

        if index is None:
            return None

        lineitem = self._lineitems[index]
        url = lineitem.id
        url = GradeService._moodle_url_handler(url, "scores")

        data = GradeService.get_payload(
            dataclasses.asdict(progress), self._progress_schema
        )

        _ = self._lms_client.send_request_to_lms(
            self._scopes,
            url,
            accept="application/json",
            content_type="application/vnd.ims.lis.v1.score+json",
            request_type="POST",
            data=data,
            need_token=True,
        )

        return progress
