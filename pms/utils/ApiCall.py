from typing import Dict

from requests import HTTPError, Session

from .AbstractConnectionManager import AbstractConnectionManager
from .errors import PmsAccessDenied, PmsBadRequest, PmsNotFound, PmsUnauthorized


class ApiCall(AbstractConnectionManager):
    def __init__(self,
                 domain=None,
                 api_prefix='',
                 auth_type: str = 'header',
                 authorization: Dict = None, username: str = None,
                 password: str = None,
                 verify=True,
                 proxies=None,
                 auth_api=None
                 ):
        """Creates a wrapper to perform API actions.

        Instances:
          .requests:  the PMS API
        """
        if domain is None:
            raise AttributeError("Connect to PMS it´s not working")
        self.domain = domain
        self._api_prefix = domain + api_prefix
        self._session = Session()
        self._session.verify = verify
        self._session.proxies = proxies
        self.auth_api = auth_api

        # Configure authentication
        if auth_type == 'basic':
            self._session.auth = (username, password)
        elif auth_type == 'header' and authorization:
            self._session.headers.update(authorization)

    def _action(self, req, **kwargs):
        content_type = req.headers.get("Content-Type")
        try:
            if "application/json" in content_type:
                j = req.json()
            elif "application/xml" in content_type or "text/xml" in content_type:
                j = req.text
            else:
                print("Error formato desconocido")
                j = req.json()
        except ValueError:
            j = req.text
        except Exception as e:
            print(f"Error al procesar la respuesta: {e}")
            j = {}

        error_message = "PMS Request Failed"
        if "error" in j:
            error_message = "{}: {}".format(j.get("message"), j.get("error"))
        elif "message" in j:
            error_message = j.get("message")

        if req.status_code == 400:
            error_message = error_message + ('. Try sending '
                                             'json=payload not data=payload')
            raise PmsBadRequest(error_message)
        elif req.status_code == 401:
            print(error_message)
            raise PmsUnauthorized(error_message)
        elif req.status_code == 403:
            print(error_message)
            raise PmsAccessDenied(error_message)
        elif req.status_code == 404:
            print(error_message)
            raise PmsNotFound(error_message)

        elif req.status_code == 429:
            # TODO
            # raise errors.PmsRateLimited(
            #    "429 Rate Limit Exceeded: API rate-limit has been reached until {} seconds. See "
            #    "https://Avirato.com/api#ratelimit".format(req.headers.get("Retry-After"))
            # )
            print(error_message)

        elif 500 < req.status_code < 600:
            # raise errors.PmsServerError("{}: Server Error".format(req.status_code))
            print(error_message)

        # Catch any other errors
        try:
            req.raise_for_status()
        except HTTPError as e:
            # raise errors.PmsError("{}: {}".format(e, j))
            print("{}: {}".format(e, j))

        # pzLogger.error(j)
        return j

    def _get(self, url, params=None, **kwargs):
        """Wrapper around request.get() to use the API prefix. Returns a JSON response."""
        if params is None:
            params = {}

        print(f'Action: Get and url: {self._api_prefix + url}')
        req = self._session.get(self._api_prefix + url, params=params)

        return self._action(req, **kwargs)

    def _post(self, url, data=None, **kwargs):
        """Wrapper around request.post() to use the API prefix. Returns a JSON response."""
        if data is None:
            data = {}

        print(f'Action: Post and url: {self._api_prefix + url}')
        kwargs.pop('prop', None)
        # kwargs.pop('use_api_v1', None)
        # todo arreglar para cuando se intente enviar precios y el token haya expirado
        # TODO mantener la logica, que haga re-login y siga con lo que le toca.
        req = self._session.post(self._api_prefix + url, data=data, **kwargs)
        return self._action(req, **kwargs)

    def _put(self, url, data=None, **kwargs):
        """Wrapper around request.put() to use the API prefix. Returns a JSON response."""
        if data is None:
            data = {}

        print(f'Action: Put and url: {self._api_prefix + url}')
        req = self._session.put(self._api_prefix + url, data=data)
        return self._action(req, **kwargs)

    def _delete(self, url, **kwargs):
        """Wrapper around request.delete() to use the API prefix. Returns a JSON response."""
        req = self._session.delete(self._api_prefix + url)
        return self._action(req, **kwargs)
