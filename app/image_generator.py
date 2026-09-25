# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import uuid
import logging
from typing import Any
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# Hardcoded project ID and bucket name per requirements
PROJECT_ID = "qwiklabs-gcp-03-5e6e400fb101"
BUCKET_NAME = "lifesync-assets-5e6e400fb101"
LOCATION = "global"
MODEL_NAME = "gemini-3.1-flash-lite-image"


async def generate_domain_image(
    prompt: str,
    category: str = "meal",
    tool_context: ToolContext | None = None,
) -> dict[str, Any]:
    """Generate an image for an item in LifeSync's domain (healthy meal, recipe, desk mobility stretch, or workout posture) using gemini-3.1-flash-lite-image in the global region.

    Saves the generated image as an artifact in the session (so it appears in the Playground's Artifacts panel)
    and uploads the in-memory bytes directly to public Cloud Storage, returning the public https URL.

    Args:
        prompt: Detailed visual prompt describing the item (e.g. 'Avocado and poached egg toast with microgreens, professional food photography' or 'Seated desk worker doing neck and shoulder stretch, minimalist fitness illustration').
        category: Item category ('meal', 'recipe', 'workout', 'mobility', 'badge').
        tool_context: ADK ToolContext injected by the agent runtime.

    Returns:
        A dictionary containing the public Cloud Storage https URL (https://storage.googleapis.com/<bucket>/<object>), status, and metadata.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=LOCATION,
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        img_bytes = None
        mime_type = "image/png"
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        img_bytes = part.inline_data.data
                        if getattr(part.inline_data, "mime_type", None):
                            mime_type = part.inline_data.mime_type
                        break
            if img_bytes:
                break

        if not img_bytes:
            return {
                "status": "error",
                "message": "Model generated text response but did not return image bytes.",
                "prompt": prompt,
            }

        ext = "jpg" if "jpeg" in mime_type.lower() else "png"
        file_id = uuid.uuid4().hex[:8]
        filename = f"{category}_{file_id}.{ext}"

        # 1. Save with tool_context.save_artifact so it shows in Playground's Artifacts panel
        if tool_context is not None:
            try:
                artifact_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
                await tool_context.save_artifact(filename=filename, artifact=artifact_part)
                logger.info("Saved artifact %s in tool_context", filename)
            except Exception as e:
                logger.warning("Failed to save artifact in tool_context: %s", e)

        # 2. Upload in-memory image bytes to Cloud Storage (no local file written)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob_name = f"images/{filename}"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(img_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_name}"

        return {
            "status": "success",
            "image_url": public_url,
            "url": public_url,
            "filename": filename,
            "category": category,
            "prompt": prompt,
            "note": "Image saved to Playground Artifacts and publicly hosted on Cloud Storage.",
        }

    except Exception as e:
        logger.exception("Failed to generate image: %s", e)
        return {
            "status": "error",
            "message": f"Failed to generate domain image: {str(e)}",
            "prompt": prompt,
        }


# Backwards compatibility alias
generate_visual_asset = generate_domain_image
