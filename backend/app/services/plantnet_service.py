import httpx
from app.core.config import settings
from typing import Optional, Dict, Any, List
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


def _ensure_jpeg(image_data: bytes) -> bytes:
    """Ensure image is in JPEG format for PlantNet API compatibility"""
    try:
        img = Image.open(io.BytesIO(image_data))
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")

        # Convert to JPEG
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=95)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Image conversion error: {e}")
        return image_data


class PlantNetService:
    def __init__(self):
        self.api_key = settings.PLANTNET_API_KEY
        self.api_url = settings.PLANTNET_API_URL

    async def identify_plant(
        self, image_data: bytes, organ: str = "auto"
    ) -> List[Dict]:
        """
        Identify plant from image and return results.

        Args:
            image_data: Raw image bytes
            organ: Plant organ type - "leaf", "flower", "fruit", "bark", "auto" (default)

        Returns:
            List of plant matches with scientific_name, family, score
        """
        if not self.api_key:
            logger.warning("PlantNet API key not configured, skipping")
            return []

        try:
            # Convert image to proper JPEG format
            jpeg_data = _ensure_jpeg(image_data)

            # PlantNet API v2 requires 'organs' parameter
            files = {"images": ("plant.jpg", jpeg_data, "image/jpeg")}

            # Build data with organs parameter
            data = {"organs": organ}

            params = {"api-key": self.api_key}

            async with httpx.AsyncClient(
                timeout=float(settings.PLANTNET_API_TIMEOUT)
            ) as client:
                response = await client.post(
                    self.api_url, files=files, data=data, params=params
                )
                response.raise_for_status()
                result = response.json()

                # Parse results
                plants = []
                for r in result.get("results", [])[:5]:
                    species = r.get("species", {})

                    plant_data = {
                        "scientific_name": species.get(
                            "scientificNameWithoutAuthor", "Unknown"
                        ),
                        "scientificName": species.get(
                            "scientificNameWithoutAuthor", "Unknown"
                        ),
                        "common_name": species.get("commonNames", [""])[0]
                        if species.get("commonNames")
                        else "",
                        "commonName": species.get("commonNames", [""])[0]
                        if species.get("commonNames")
                        else "",
                        "family": species.get("family", {}).get(
                            "scientificNameWithoutAuthor", ""
                        ),
                        "genus": species.get("genus", {}).get("scientificName", ""),
                        "score": r.get("score", 0),
                        "certainty": r.get("score", 0),
                        "source": "plantnet",
                        "gbif_id": r.get("gbif", {}).get("id"),
                    }

                    plants.append(plant_data)
                    logger.info(
                        f"✅ PlantNet found: {plant_data['scientific_name']} (score: {plant_data['score']:.2%})"
                    )

                return plants

        except httpx.HTTPStatusError as e:
            logger.error(
                f"PlantNet API HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return []
        except Exception as e:
            logger.error(f"PlantNet identify error: {e}")
            return []

    async def get_plant_details(self, scientific_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed plant information from PlantNet API by scientific name.
        """
        if not self.api_key:
            logger.warning("PlantNet API key not configured")
            return None

        try:
            # PlantNet doesn't have a direct "get by name" endpoint
            logger.info(f"PlantNet: Would fetch details for {scientific_name}")
            return None

        except Exception as e:
            logger.error(f"PlantNet get_plant_details error: {e}")
            return None

    async def get_detailed_results(
        self, image_data: bytes, top_k: int = 3, organ: str = "auto"
    ) -> list:
        """
        Get detailed plant identification results with all available information.
        """
        if not self.api_key:
            logger.warning("PlantNet API key not configured, skipping")
            return []

        try:
            files = {"images": ("plant.jpg", image_data, "image/jpeg")}
            data = {"organs": organ}
            params = {"api-key": self.api_key}

            async with httpx.AsyncClient(
                timeout=float(settings.PLANTNET_API_TIMEOUT)
            ) as client:
                response = await client.post(
                    self.api_url, files=files, data=data, params=params
                )
                response.raise_for_status()
                result = response.json()

                # Detailed parse
                plants = []
                for r in result.get("results", [])[:top_k]:
                    species = r.get("species", {})

                    plant_data = {
                        "scientific_name": species.get(
                            "scientificNameWithoutAuthor", "Unknown"
                        ),
                        "scientific_name_full": species.get("scientificName", ""),
                        "common_names": species.get("commonNames", []),
                        "family": species.get("family", {}).get(
                            "scientificNameWithoutAuthor", ""
                        ),
                        "genus": species.get("genus", {}).get("scientificName", ""),
                        "score": r.get("score", 0),
                        "images": [
                            img.get("url", {}).get("o", "")
                            for img in r.get("images", [])[:3]
                        ],
                        "gbif_id": r.get("gbif", {}).get("id"),
                    }

                    plants.append(plant_data)
                    logger.info(
                        f"PlantNet found: {plant_data['scientific_name']} (score: {plant_data['score']:.2f})"
                    )

                return plants

        except httpx.HTTPStatusError as e:
            logger.error(f"PlantNet API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"PlantNet detailed results error: {e}")
            return []


plantnet_service = PlantNetService()
