import logging
from concurrent.futures import ThreadPoolExecutor

import requests

logger = logging.getLogger(__name__)
_EXEC = ThreadPoolExecutor(max_workers=2)
LOG_ENDPOINT = "https://flo.cosylab.at/eddie/inspectors_v1/logNik.php"


def log_external(participant_id: int, state: int, comment: str = ""):
    params = {
        "participant_id": participant_id,
        "state": state,
        "comment": comment or "0",
    }

    def _send():
        try:
            requests.get(LOG_ENDPOINT, params=params, timeout=1.5)
        except Exception as e:
            logger.debug("external log failed: %s", e)

    _EXEC.submit(_send)
