"""Topology helper for IDFM."""
import asyncio
import logging
import aiohttp
from typing import List, Dict, Optional, Tuple

_LOGGER: logging.Logger = logging.getLogger(__package__)

class LineTopology:
    """Helper to fetch and cache line topology from Navitia."""

    def __init__(self, client):
        self._client = client
        self._topology_cache = {}  # Cache by line_id -> Dict[TerminusID, List[StopID]]

    async def get_ordered_stops(self, line_id: str) -> Dict[str, List[str]]:
        """
        Fetch stop sequences for the line.
        Returns a dictionary: {Terminus_ID: [Stop_ID_1, Stop_ID_2, ...]}
        """
        if line_id in self._topology_cache:
            return self._topology_cache[line_id]

        _LOGGER.debug(f"Fetching topology for line {line_id}")

        url = f"https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/lines/line:IDFM:{line_id}/routes"
        routes_data = await self._navitia_request(url)

        if not routes_data or "routes" not in routes_data:
            _LOGGER.error("Failed to fetch routes from Navitia")
            return {}

        topology = {}

        for route in routes_data["routes"]:
            route_id = route["id"]
            points_url = f"https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/routes/{route_id}/stop_points"
            points_data = await self._navitia_request(points_url)

            if points_data and "stop_points" in points_data:
                ordered_stops = []
                for sp in points_data["stop_points"]:
                    stop_id = self._extract_stif_id(sp["id"])
                    if stop_id:
                        ordered_stops.append(stop_id)

                if ordered_stops:
                    terminus = ordered_stops[-1]
                    if terminus not in topology:
                        topology[terminus] = []
                    topology[terminus].append(ordered_stops)

        self._topology_cache[line_id] = topology
        return topology

    async def _navitia_request(self, url):
        try:
             async with self._client._session.get(
                url,
                headers={
                    "apiKey": self._client._apikey,
                    "Content-Type": "application/json",
                    "Accept-encoding": "gzip, deflate",
                },
            ) as response:
                if response.status != 200:
                    _LOGGER.warn(f"Error fetching {url}: {response.status}")
                    return None
                return await response.json()
        except Exception as e:
            _LOGGER.error(f"Error in navitia request: {e}")
            return None

    def _extract_stif_id(self, navitia_id):
        # We want to normalize to the numeric code if possible to avoid prefix mismatches
        # (StopPoint vs StopArea etc)
        try:
            if "IDFM:" in navitia_id:
                stif_part = navitia_id.split("IDFM:")[1]
            else:
                stif_part = navitia_id

            # Now extract number from STIF:StopPoint:Q:43114:
            # It's usually the second to last element if split by :
            return stif_part.split(":")[-2]
        except (IndexError, AttributeError):
            return None

    def check_stop_on_path(self, topology: Dict[str, List[List[str]]], start_id: str, target_id: str, terminus_id: str) -> bool:
        """
        Check if target_id is between start_id and terminus_id for any route ending at terminus_id.
        """
        if terminus_id not in topology:
            return False

        possible_routes = topology[terminus_id]

        for route in possible_routes:
            try:
                idx_start = route.index(start_id)
                idx_target = route.index(target_id)
                idx_end = route.index(terminus_id)

                if idx_start < idx_target <= idx_end:
                    return True
            except ValueError:
                continue

        return False
