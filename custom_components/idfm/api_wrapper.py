"""Wrapper for IDFMApi to support multiple API keys."""
import logging
from typing import List, Optional

from .idfm_api import IDFMApi, RequestError
from .idfm_api.models import TrafficData, InfoData, ReportData, LineData, StopData, TransportType

_LOGGER = logging.getLogger(__name__)

class MultiKeyIDFMApi:
    """Wrapper around IDFMApi that handles multiple API keys."""

    def __init__(self, session, tokens: List[str], timeout: int = 300):
        """Initialize the wrapper."""
        self._session = session
        self._tokens = tokens
        self._timeout = timeout
        self._current_token_index = 0
        self._clients = [
            IDFMApi(session, token.strip(), timeout) for token in tokens
        ]

    @property
    def _current_client(self) -> IDFMApi:
        """Return the current client instance."""
        return self._clients[self._current_token_index]

    def _rotate_key(self):
        """Switch to the next available key."""
        old_index = self._current_token_index
        self._current_token_index = (self._current_token_index + 1) % len(self._tokens)
        _LOGGER.warning(
            "Switching API key from index %s to %s due to rate limit or error.",
            old_index,
            self._current_token_index,
        )

    async def _call_with_retry(self, func):
        """Call a function with retry logic for 429 errors."""
        attempts = 0
        max_attempts = len(self._tokens)

        while attempts < max_attempts:
            try:
                return await func(self._current_client)
            except RequestError as err:
                if err.code == 429:
                    _LOGGER.info("Rate limit hit (429), rotating key.")
                    self._rotate_key()
                    attempts += 1
                else:
                    raise err
            except Exception as e:
                 raise e

        raise RequestError(429, "All API keys are rate limited.")

    async def get_lines(self, transport: Optional[TransportType] = None) -> List[LineData]:
        return await self._current_client.get_lines(transport)

    async def get_stops(self, line_id: str) -> List[StopData]:
        return await self._current_client.get_stops(line_id)

    async def get_traffic(
        self,
        stop_id: str,
        destination_name: Optional[str] = None,
        direction_name: Optional[str] = None,
        line_id: Optional[str] = None,
    ) -> List[TrafficData]:
        return await self._call_with_retry(
            lambda client: client.get_traffic(stop_id, destination_name, direction_name, line_id)
        )

    async def get_destinations(
        self,
        stop_id: str,
        direction_name: Optional[str] = None,
        line_id: Optional[str] = None,
    ) -> List[str]:
        return await self._call_with_retry(
            lambda client: client.get_destinations(stop_id, direction_name, line_id)
        )

    async def get_directions(
        self, stop_id: str, line_id: Optional[str] = None
    ) -> List[str]:
        return await self._call_with_retry(
            lambda client: client.get_directions(stop_id, line_id)
        )

    async def get_infos(self, line_id: str) -> List[InfoData]:
         return await self._call_with_retry(
            lambda client: client.get_infos(line_id)
        )

    async def get_line_reports(
        self, line_id: str, exclude_elevator: bool = True
    ) -> List[ReportData]:
        return await self._call_with_retry(
            lambda client: client.get_line_reports(line_id, exclude_elevator)
        )
