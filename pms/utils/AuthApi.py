from utils.SingletonMeta import SingletonMeta

from .ApiCall import ApiCall


class AuthApi(metaclass=SingletonMeta):

    def init_call(self, domain="", authorization=None):
        return ApiCall(domain=domain, authorization=authorization)
