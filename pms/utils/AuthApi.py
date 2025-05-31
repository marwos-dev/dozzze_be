import src
from src.helper.PMSHelper import PMSHelper
from src.utils.externals.ApiCall import ApiCall
from src.utils.logger import grLogger
from src.utils.SingletonMeta import SingletonMeta


class AuthApi(metaclass=SingletonMeta):
    def __init__(self):
        pass
        # self._initialize()

    def _initialize(self):
        try:
            # Attempt to get pms_config from Redis
            pms_config = src.hybridCache.get("pms_config")
            if pms_config:
                self.pms_config = pms_config
                grLogger.info("FNS pms_config _initialize from redis")
            else:
                # If there is nothing in Redis, fetch from PMSHelper and set it
                self.pms_config = PMSHelper().get_pms(pms_id=2)
                src.hybridCache.set("pms_config", self.pms_config)
                grLogger.info("FNS pms_config _initialize from DB")
        except Exception as e:
            grLogger.error(f"Failed to initialize with Redis pms config {e.args}")
            self.pms_config = PMSHelper().get_pms(pms_id=2)
            grLogger.info("FNS pms_config _initializ from DB")

    def init_call(self, domain=""):
        return ApiCall(domain=domain)

        #########################
        #########################
