"""
Plant.id API Service - Get detailed plant information by scientific name
https://plant.id
"""

import httpx
from typing import Dict, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PlantIdService:
    """Plant.id API for getting plant details by scientific name"""

    def __init__(self):
        self.api_key = settings.PLANT_ID_KEY
        self.api_url = settings.PLANT_ID_URL

        if self.api_key:
            logger.info("✅ Plant.id API configured (for plant details)")
        else:
            logger.warning("⚠️ Plant.id API key not configured")

    async def get_plant_details(
        self, scientific_name: str, lang: str = "tr"
    ) -> Optional[Dict]:
        """
        Get detailed plant information by scientific name.

        Args:
            scientific_name: Scientific name of the plant (e.g., "Rosa gallica")
            lang: Language code for common names (default: Turkish)

        Returns:
            Dict with plant details: description, common_names, taxonomy, care info, etc.
        """
        if not self.api_key:
            logger.warning("Plant.id API key not configured, skipping")
            return None

        try:
            headers = {
                "Api-Key": self.api_key,
                "Content-Type": "application/json",
            }

            # Try the knowledge base endpoint
            async with httpx.AsyncClient(
                timeout=float(settings.PLANT_ID_API_TIMEOUT)
            ) as client:
                # First try: KB search endpoint
                response = await client.get(
                    f"{self.api_url}/kb/plants/name_search",
                    params={"q": scientific_name, "limit": 1},
                    headers=headers,
                )

                if response.status_code == 200:
                    result = response.json()
                    entities = result.get("entities", [])

                    if entities:
                        entity = entities[0]
                        access_token = entity.get("access_token")

                        if access_token:
                            # Get full details using access token
                            detail_response = await client.get(
                                f"{self.api_url}/kb/plants/{access_token}",
                                params={
                                    "details": "common_names,url,description,taxonomy,image,watering"
                                },
                                headers=headers,
                            )

                            if detail_response.status_code == 200:
                                details = detail_response.json()

                                plant_info = {
                                    "scientific_name": scientific_name,
                                    "common_names": details.get("common_names", []),
                                    "description": details.get("description", {}).get(
                                        "value", ""
                                    ),
                                    "taxonomy": details.get("taxonomy", {}),
                                    "watering": details.get("watering", {}),
                                    "image_url": details.get("image", {}).get(
                                        "value", ""
                                    ),
                                    "url": details.get("url", ""),
                                    "source": "plant.id",
                                }

                                logger.info(
                                    f"✅ Plant.id details retrieved for: {scientific_name}"
                                )
                                return plant_info

                # Fallback: Return basic info if API doesn't return details
                logger.info(f"ℹ️ Plant.id: No detailed info for {scientific_name}")
                return None

        except httpx.HTTPStatusError as e:
            logger.error(f"Plant.id API HTTP error: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Plant.id get_plant_details error: {e}")
            return None

    async def enrich_plant_data(self, plants: list) -> list:
        """
        Enrich a list of plants with detailed information from Plant.id.

        Args:
            plants: List of plant dicts with 'scientificName' field

        Returns:
            Same list with added 'details' field containing Plant.id info
        """
        if not self.api_key:
            return plants

        for plant in plants[:3]:  # Only enrich top 3 to save API calls
            scientific_name = plant.get("scientificName", "")
            if scientific_name:
                details = await self.get_plant_details(scientific_name)
                if details:
                    plant["plant_id_details"] = details
                    # Add description if available
                    if details.get("description"):
                        plant["description"] = details["description"]
                    # Add common names if missing
                    if not plant.get("commonName") and details.get("common_names"):
                        plant["commonName"] = (
                            details["common_names"][0]
                            if details["common_names"]
                            else ""
                        )

        return plants


# Global instance
plant_id_service = PlantIdService()
