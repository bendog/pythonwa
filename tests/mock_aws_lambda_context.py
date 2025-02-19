from dataclasses import dataclass


@dataclass
class MockLambdaContext:
    function_name: str = "test"
    memory_limit_in_mb: int = 128
    aws_request_id: str = "9aa7a77e-95ce-4e03-8f83-375a2882809a"

    @property
    def invoked_function_arn(self) -> str:
        return f"arn:aws:lambda:ap-southeast-2:123456789012:function:{self.function_name}"
