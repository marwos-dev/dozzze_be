from ninja import Schema


class SuccessSchema(Schema):
    message: str
    success: bool = True


class ErrorSchema(Schema):
    detail: str
    status_code: int = 400

    @staticmethod
    def resolve_error_code(obj):
        return obj.status_code if hasattr(obj, "status_code") else 400
