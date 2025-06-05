class AbstractConnectionManager:
    def _action(self, req):
        raise NotImplementedError

    def _get(self, url, params=None):
        raise NotImplementedError

    def _post(self, url, data=None, **kwargs):
        raise NotImplementedError

    def _put(self, url, data=None):
        raise NotImplementedError

    def _delete(self, url):
        raise NotImplementedError
