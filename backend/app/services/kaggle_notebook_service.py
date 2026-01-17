"""
Kaggle Notebook Integration Service - Gradio API
Sends user images to Kaggle Gradio API for processing with PlantCLEF dataset
"""

import os
import io
import json
import base64
import httpx
from typing import Dict, Any, List
from PIL import Image
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class KaggleNotebookService:
    """
    Kaggle Notebook Gradio API integration
    Uses Kaggle notebook with Gradio as inference server for PlantCLEF 2025 dataset
    """

    def __init__(self):
        self.notebook_url = os.getenv("KAGGLE_NOTEBOOK_URL", "").strip()
        from app.core.config import settings

        self.timeout = float(settings.KAGGLE_API_TIMEOUT)
        self._available = False
        if self.notebook_url:
            logger.info(f"Kaggle URL loaded: {self.notebook_url[:50]}...")

    async def check_availability(self) -> bool:
        """Check if Kaggle Gradio API is available"""
        if not self.notebook_url:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.notebook_url}/config", timeout=10.0)
                self._available = response.status_code == 200
                return self._available
        except Exception as e:
            logger.error(f"Kaggle health check failed: {e}")
            self._available = False
            return False

    async def identify_plant(
        self, image_bytes: bytes, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Identify plant using Kaggle Gradio API"""
        if not self.notebook_url:
            logger.warning("Kaggle notebook URL not configured")
            return []

        try:
            # Convert image to base64
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")

            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()

            async with httpx.AsyncClient() as client:
                # Gradio 5.x: POST to /gradio_api/call/predict returns event_id
                endpoint = f"{self.notebook_url}/gradio_api/call/predict"

                # Image payload format for Gradio
                payload = {
                    "data": [
                        {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "meta": {"_type": "gradio.FileData"},
                        }
                    ]
                }

                logger.info(f"Calling Kaggle: {endpoint}")

                # Step 1: Submit the request
                response = await client.post(
                    endpoint,
                    json=payload,
                    timeout=self.timeout,
                )

                logger.info(f"Gradio call response: {response.status_code}")

                if response.status_code != 200:
                    logger.error(f"Gradio API error: {response.text[:200]}")
                    return []

                # Step 2: Get event_id from response
                call_result = response.json()
                logger.info(f"Call result: {json.dumps(call_result)[:200]}")

                event_id = call_result.get("event_id")
                if not event_id:
                    logger.error("No event_id in Gradio response")
                    return []

                # Step 3: Fetch the result using event_id
                result_endpoint = (
                    f"{self.notebook_url}/gradio_api/call/predict/{event_id}"
                )
                logger.info(f"Fetching result: {result_endpoint}")

                result_response = await client.get(
                    result_endpoint,
                    timeout=self.timeout,
                )

                logger.info(f"Result response: {result_response.status_code}")

                if result_response.status_code != 200:
                    logger.error(f"Result fetch error: {result_response.text[:200]}")
                    return []

                # Parse SSE response (Server-Sent Events format)
                result_text = result_response.text
                logger.info(f"Result text: {result_text[:300]}")

                # SSE format: "data: {...}\n\n"
                predictions = self._parse_sse_response(result_text, top_k)
                return predictions

        except httpx.TimeoutException:
            logger.error("Kaggle Gradio API timeout")
            return []
        except Exception as e:
            logger.error(f"Kaggle Gradio API error: {e}")
            return []

    def _parse_sse_response(self, text: str, top_k: int) -> List[Dict[str, Any]]:
        """Parse Server-Sent Events response from Gradio"""
        try:
            # Find data lines in SSE format
            for line in text.split("\n"):
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str:
                        data = json.loads(data_str)

                        # Gradio returns: [{"label": ..., "confidences": [...]}]
                        if isinstance(data, list) and len(data) > 0:
                            result = data[0]

                            # Label component output format
                            if isinstance(result, dict):
                                # Direct label dict: {"species1": 0.9, "species2": 0.1}
                                if "confidences" in result:
                                    # Format: {"label": "top", "confidences": [{"label": "...", "confidence": 0.9}]}
                                    return self._format_confidences(
                                        result["confidences"], top_k
                                    )
                                else:
                                    # Direct dict format
                                    return self._format_dict_predictions(result, top_k)

            logger.warning("No valid data found in SSE response")
            return []
        except Exception as e:
            logger.error(f"SSE parsing error: {e}")
            return []

    def _format_confidences(
        self, confidences: List[Dict], top_k: int
    ) -> List[Dict[str, Any]]:
        """Format Gradio Label component confidences output"""
        formatted = []
        for conf in confidences[:top_k]:
            formatted.append(
                {
                    "scientificName": conf.get("label", "Unknown"),
                    "commonName": conf.get("label", "Unknown"),
                    "score": conf.get("confidence", 0.0),
                    "certainty": conf.get("confidence", 0.0),
                    "source": "kaggle-plantclef",
                    "model": "ResNet-PlantCLEF2025",
                }
            )
        return formatted

    def _format_dict_predictions(
        self, predictions: Dict, top_k: int
    ) -> List[Dict[str, Any]]:
        """Format direct dict predictions"""
        formatted = []
        sorted_preds = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]
        for species, confidence in sorted_preds:
            formatted.append(
                {
                    "scientificName": species,
                    "commonName": species,
                    "score": float(confidence),
                    "certainty": float(confidence),
                    "source": "kaggle-plantclef",
                    "model": "ResNet-PlantCLEF2025",
                }
            )
        return formatted

    @property
    def is_available(self) -> bool:
        return bool(self.notebook_url) and self._available


kaggle_notebook_service = KaggleNotebookService()
