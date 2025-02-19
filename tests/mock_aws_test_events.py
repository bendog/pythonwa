import random
import string
import uuid
from datetime import datetime
from hashlib import md5


def md5_str(body):
    """make a md5 of the string"""
    # noinspection InsecureHash
    return str(md5(body.encode("utf-8")).hexdigest())


class AWSTestEvent(object):
    account_id = "123456789012"
    region = "ap-southeast-2"
    _id = None
    _xray_id = None

    @property
    def timestamp(self):
        return datetime.now().timestamp()

    @property
    def datetime(self):
        return str(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

    @property
    def id(self):
        if not self._id:
            self._id = self.generate_id()
        return self._id

    @property
    def xray_id(self):
        if not self._xray_id:
            self._xray_id = f"Root={self.generate_id()}"
        return self._xray_id

    @staticmethod
    def generate_id():
        """generate a random uuid"""
        return str(uuid.uuid4())

    @staticmethod
    def random_string(string_length):
        letters_and_digits = string.ascii_letters + string.digits
        return "".join((random.choice(letters_and_digits) for _ in range(string_length)))

    # noinspection PyMethodMayBeStatic
    def event(self, **kwargs) -> dict:
        """always return a dict"""
        return {**kwargs}


class APIGatewayTestEvent(AWSTestEvent):
    allowed_methods = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    stage = "api"
    api_id = "apitest123"

    @staticmethod
    def __to_api_gateway_structure(parameters: dict[str, str] | None = None) -> dict:
        query_string_parameters = {}
        multi_value_query_string_parameters = {}

        if parameters:
            for key, value in parameters.items():
                if "," in value:
                    values = value.split(",")
                else:
                    values = [value]

                query_string_parameters[key] = values
                multi_value_query_string_parameters[key] = values

        return {
            "queryStringParameters": query_string_parameters,
            "multiValueQueryStringParameters": multi_value_query_string_parameters,
        }

    def event(
        self,
        method: str = "GET",
        path: str = "/",
        body: str | None = None,
        query_string_parameters: dict[str, str | list[str]] | None = None,
        path_parameters: dict[str, str] | None = None,
        headers=None,
        base_64encoded: bool | None = False,
        roles=None,
    ) -> dict:
        if headers is None:
            headers = {}

        if roles is None:
            roles = []

        method = method.upper()

        return {
            "resource": path,
            "path": path,
            "httpMethod": method,
            "methodArn": f"arn:aws:execute-api:{self.region}:{self.account_id}:{self.api_id}/default/$connect",
            "headers": {
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9,en-AU;q=0.8",
                "content-type": "application/json",
                "Host": f"{self.api_id}.execute-api.{self.region}.amazonaws.com",
                "requestContext": {},
                **headers,
            },
            "multiValueHeaders": {
                "Accept": ["*/*"],
                "content-type": ["application/json"],
                "Host": [f"{self.api_id}.execute-api.{self.region}.amazonaws.com"],
                "User-Agent": ["insomnia/7.1.1"],
                "X-Amzn-Trace-Id": [self.xray_id],
            },
            "requestContext": {
                "resourceId": "ben123",
                "authorizer": {
                    "name": "Test, User",
                    "roles": ",".join(roles),
                    "email": "user.test@test.com",
                    "jobTitle": "Test Operator",
                },
                "resourcePath": path,
                "httpMethod": method,
                "extendedRequestId": "BenTest12345678=",
                "requestTime": f"{self.datetime}",
                "path": f"/{self.stage}{path}",
                "accountId": self.account_id,
                "protocol": "HTTP/1.1",
                "stage": self.stage,
                "domainPrefix": self.api_id,
                "requestTimeEpoch": self.timestamp,
                "requestId": self.id,
                "identity": {
                    "sourceIp": "10.10.10.10",
                },
                "domainName": f"{self.api_id}.execute-api.{self.region}.amazonaws.com",
                "deploymentId": "ben123",
                "apiId": self.api_id,
            },
            "body": body,
            "pathParameters": path_parameters,
            "stageVariables": None,
            "isBase64Encoded": base_64encoded,
            **APIGatewayTestEvent.__to_api_gateway_structure(query_string_parameters),
        }

    def get(
        self,
        path: str = "/",
        query_string_parameters: dict[str, str | list[str]] | None = None,
        path_parameters: dict[str, str] | None = None,
        headers=None,
        roles=None,
    ) -> dict:
        return self.event(
            "GET",
            path=path,
            query_string_parameters=query_string_parameters,
            path_parameters=path_parameters,
            headers=headers,
            roles=roles,
        )

    def put(
        self,
        path: str = "/",
        body: str | None = None,
        path_parameters: dict[str, str] | None = None,
        headers=None,
        roles=None,
    ) -> dict:
        return self.event(
            "PUT",
            path=path,
            body=body,
            path_parameters=path_parameters,
            headers=headers,
            roles=roles,
        )

    def delete(
        self,
        path: str = "/",
        query_string_parameters: dict[str, str | list[str]] | None = None,
        path_parameters: dict[str, str] | None = None,
        headers=None,
        roles=None,
    ) -> dict:
        return self.event(
            "DELETE",
            path=path,
            query_string_parameters=query_string_parameters,
            path_parameters=path_parameters,
            headers=headers,
            roles=roles,
        )

    def post(
        self,
        path: str = "/",
        body: str | None = None,
        path_parameters: dict[str, str] | None = None,
        headers=None,
        roles=None,
    ) -> dict:
        return self.event(
            "POST",
            path=path,
            body=body,
            path_parameters=path_parameters,
            headers=headers,
            roles=roles,
        )


class SQSTestEvent(AWSTestEvent):
    sqs_name = "default_sqs_name"

    def __init__(self, name=None):
        if name:
            self.sqs_name = name

    @property
    def sqs_arn(self):
        return f"arn:aws:sqs:{self.region}:{self.account_id}:{self.sqs_name}"

    # noinspection PyDefaultArgument
    def make_record(self, body, attributes=None, message_attributes=None):
        if message_attributes is None:
            message_attributes = {}
        if attributes is None:
            attributes = {}
        body_md5 = md5_str(body)
        message_id = self.generate_id()
        return {
            "messageId": message_id,
            "receiptHandle": "MessageReceiptHandle",
            "body": body,
            "attributes": {
                "ApproximateReceiveCount": "1",
                "SentTimestamp": self.datetime,
                "SenderId": self.account_id,
                "ApproximateFirstReceiveTimestamp": str(self.timestamp),
                **attributes,
            },
            "messageAttributes": {**message_attributes},
            "md5OfBody": body_md5,
            "eventSource": "aws:sqs",
            "eventSourceARN": self.sqs_arn,
            "awsRegion": self.region,
        }

    def event(self, body_list: list[str]) -> dict:
        return {"Records": [self.make_record(body) for body in body_list]}


class EventBridgeEvent(AWSTestEvent):
    pass
