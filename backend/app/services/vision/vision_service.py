from __future__ import annotations

import logging
from typing import Any

from google.cloud import vision_v1
from google.cloud.vision_v1 import types
from google.api_core.exceptions import GoogleAPIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.domain.interfaces.external_services import IVisionService, VisionAnalysis

logger = logging.getLogger(__name__)


class GoogleVisionService(IVisionService):
    def __init__(self) -> None:
        self._client: vision_v1.ImageAnnotatorClient | None = None
        self._initialized = False
        self._initialize()

    def _initialize(self) -> None:
        try:
            self._client = vision_v1.ImageAnnotatorClient()
            self._initialized = True
            logger.info("GoogleVisionService initialized")
        except Exception:
            logger.exception("Failed to initialize GoogleVisionService")
            self._initialized = False

    def _load_image(self, image_data: bytes) -> vision_v1.Image:
        return vision_v1.Image(content=image_data)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def analyze_image(
        self,
        image_data: bytes,
        features: list[str] | None = None,
    ) -> VisionAnalysis:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleVisionService not initialized")

        image = self._load_image(image_data)

        requested_features = features or [
            "LABEL_DETECTION",
            "OBJECT_LOCALIZATION",
            "TEXT_DETECTION",
            "SAFE_SEARCH_DETECTION",
            "IMAGE_PROPERTIES",
        ]

        feature_map: dict[str, vision_v1.Feature] = {
            "LABEL_DETECTION": vision_v1.Feature(
                type_=vision_v1.Feature.Type.LABEL_DETECTION,
                max_results=20,
            ),
            "OBJECT_LOCALIZATION": vision_v1.Feature(
                type_=vision_v1.Feature.Type.OBJECT_LOCALIZATION,
                max_results=20,
            ),
            "TEXT_DETECTION": vision_v1.Feature(
                type_=vision_v1.Feature.Type.TEXT_DETECTION,
                max_results=10,
            ),
            "SAFE_SEARCH_DETECTION": vision_v1.Feature(
                type_=vision_v1.Feature.Type.SAFE_SEARCH_DETECTION,
            ),
            "FACE_DETECTION": vision_v1.Feature(
                type_=vision_v1.Feature.Type.FACE_DETECTION,
                max_results=20,
            ),
            "LANDMARK_DETECTION": vision_v1.Feature(
                type_=vision_v1.Feature.Type.LANDMARK_DETECTION,
                max_results=10,
            ),
            "IMAGE_PROPERTIES": vision_v1.Feature(
                type_=vision_v1.Feature.Type.IMAGE_PROPERTIES,
            ),
            "LOGO_DETECTION": vision_v1.Feature(
                type_=vision_v1.Feature.Type.LOGO_DETECTION,
                max_results=10,
            ),
        }

        vision_features = [
            feature_map[f]
            for f in requested_features
            if f in feature_map
        ]

        request = vision_v1.AnnotateImageRequest(
            image=image,
            features=vision_features,
        )

        response = self._client.annotate_image(request=request)

        if response.error.message:
            raise RuntimeError(f"Vision API error: {response.error.message}")

        labels = []
        for label in response.label_annotations:
            labels.append({
                "description": label.description,
                "score": label.score,
                "topicality": label.topicality,
            })

        objects = []
        for obj in response.localized_object_annotations:
            vertices = []
            for vertex in obj.bounding_poly.normalized_vertices:
                vertices.append({"x": vertex.x, "y": vertex.y})
            objects.append({
                "name": obj.name,
                "score": obj.score,
                "bounding_poly": vertices,
            })

        text_detected = None
        if response.full_text_annotation:
            text_detected = response.full_text_annotation.text

        safety_labels = []
        if response.safe_search_annotation:
            safe = response.safe_search_annotation
            safety_labels = [
                {"category": "adult", "likelihood": vision_v1.Likelihood(safe.adult).name},
                {"category": "violence", "likelihood": vision_v1.Likelihood(safe.violence).name},
                {"category": "spoof", "likelihood": vision_v1.Likelihood(safe.spoof).name},
                {"category": "medical", "likelihood": vision_v1.Likelihood(safe.medical).name},
                {"category": "racy", "likelihood": vision_v1.Likelihood(safe.racy).name},
            ]

        return VisionAnalysis(
            labels=labels,
            objects=objects,
            text_detected=text_detected,
            safety_labels=safety_labels,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def detect_crowd_density(
        self,
        image_data: bytes,
        sector_hint: str | None = None,
    ) -> dict[str, Any]:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleVisionService not initialized")

        image = self._load_image(image_data)

        feature = vision_v1.Feature(
            type_=vision_v1.Feature.Type.LABEL_DETECTION,
            max_results=50,
        )

        request = vision_v1.AnnotateImageRequest(
            image=image,
            features=[feature],
        )

        response = self._client.annotate_image(request=request)

        crowd_indicators = {
            "crowd": 0.0, "people": 0.0, "person": 0.0, "audience": 0.0,
            "gathering": 0.0, "group": 0.0, "packed": 0.0, "standing": 0.0,
        }

        for label in response.label_annotations:
            desc_lower = label.description.lower()
            for indicator in crowd_indicators:
                if indicator in desc_lower:
                    crowd_indicators[indicator] = max(
                        crowd_indicators[indicator], label.score
                    )

        density_score = sum(crowd_indicators.values()) / max(len(crowd_indicators), 1)

        if density_score > 0.7:
            density_level = "high"
        elif density_score > 0.4:
            density_level = "medium"
        elif density_score > 0.1:
            density_level = "low"
        else:
            density_level = "minimal"

        object_count = 0
        object_request = vision_v1.AnnotateImageRequest(
            image=image,
            features=[vision_v1.Feature(
                type_=vision_v1.Feature.Type.OBJECT_LOCALIZATION,
                max_results=50,
            )],
        )
        obj_response = self._client.annotate_image(request=object_request)
        object_count = len(obj_response.localized_object_annotations)

        return {
            "density_score": round(density_score, 3),
            "density_level": density_level,
            "crowd_indicators": {k: v for k, v in crowd_indicators.items() if v > 0},
            "detected_objects": object_count,
            "sector_hint": sector_hint,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def detect_objects(
        self,
        image_data: bytes,
        object_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleVisionService not initialized")

        image = self._load_image(image_data)

        feature = vision_v1.Feature(
            type_=vision_v1.Feature.Type.OBJECT_LOCALIZATION,
            max_results=50,
        )

        request = vision_v1.AnnotateImageRequest(
            image=image,
            features=[feature],
        )

        response = self._client.annotate_image(request=request)

        objects: list[dict[str, Any]] = []
        for obj in response.localized_object_annotations:
            if object_types:
                if not any(
                    ot.lower() in obj.name.lower() for ot in object_types
                ):
                    continue

            vertices = []
            for vertex in obj.bounding_poly.normalized_vertices:
                vertices.append({"x": vertex.x, "y": vertex.y})

            objects.append({
                "name": obj.name,
                "score": obj.score,
                "bounding_poly": vertices,
            })

        return objects

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(GoogleAPIError),
        reraise=True,
    )
    async def ocr(self, image_data: bytes) -> str:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleVisionService not initialized")

        image = self._load_image(image_data)

        feature = vision_v1.Feature(
            type_=vision_v1.Feature.Type.TEXT_DETECTION,
        )

        request = vision_v1.AnnotateImageRequest(
            image=image,
            features=[feature],
        )

        response = self._client.annotate_image(request=request)

        if response.error.message:
            raise RuntimeError(f"Vision API error: {response.error.message}")

        if response.full_text_annotation:
            return response.full_text_annotation.text

        return ""

    async def detect_faces(self, image_data: bytes) -> list[dict[str, Any]]:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleVisionService not initialized")

        image = self._load_image(image_data)

        feature = vision_v1.Feature(
            type_=vision_v1.Feature.Type.FACE_DETECTION,
            max_results=20,
        )

        request = vision_v1.AnnotateImageRequest(
            image=image,
            features=[feature],
        )

        response = self._client.annotate_image(request=request)

        faces: list[dict[str, Any]] = []
        for face in response.face_annotations:
            vertices = []
            for vertex in face.bounding_poly.vertices:
                vertices.append({"x": vertex.x, "y": vertex.y})
            faces.append({
                "confidence": face.detection_confidence,
                "joy": vision_v1.Likelihood(face.joy_likelihood).name,
                "sorrow": vision_v1.Likelihood(face.sorrow_likelihood).name,
                "anger": vision_v1.Likelihood(face.anger_likelihood).name,
                "surprise": vision_v1.Likelihood(face.surprise_likelihood).name,
                "bounding_poly": vertices,
            })

        return faces

    async def detect_landmarks(self, image_data: bytes) -> list[dict[str, Any]]:
        if not self._initialized or self._client is None:
            raise RuntimeError("GoogleVisionService not initialized")

        image = self._load_image(image_data)

        feature = vision_v1.Feature(
            type_=vision_v1.Feature.Type.LANDMARK_DETECTION,
            max_results=10,
        )

        request = vision_v1.AnnotateImageRequest(
            image=image,
            features=[feature],
        )

        response = self._client.annotate_image(request=request)

        landmarks: list[dict[str, Any]] = []
        for landmark in response.landmark_annotations:
            location = {}
            if landmark.locations:
                loc = landmark.locations[0]
                if hasattr(loc, "lat_lng"):
                    location = {
                        "latitude": loc.lat_lng.latitude,
                        "longitude": loc.lat_lng.longitude,
                    }
            landmarks.append({
                "description": landmark.description,
                "score": landmark.score,
                "location": location,
            })

        return landmarks
