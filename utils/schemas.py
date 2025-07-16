from ninja import Schema


class SuccessSchema(Schema):
    message: str
    success: bool = True


class ErrorSchema(Schema):
    detail: str
    code: int | None = None
    status_code: int = 400

    @staticmethod
    def resolve_error_code(obj):
        if hasattr(obj, "code") and obj.code is not None:
            return obj.code
        return obj.status_code if hasattr(obj, "status_code") else 400
