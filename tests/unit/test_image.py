import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.image_generator import (
    generate_domain_image,
    BUCKET_NAME,
    PROJECT_ID,
    LOCATION,
    MODEL_NAME,
)


@pytest.mark.asyncio
async def test_generate_domain_image():
    assert BUCKET_NAME == "lifesync-assets-5e6e400fb101"
    assert PROJECT_ID == "qwiklabs-gcp-03-5e6e400fb101"
    assert LOCATION == "global"
    assert MODEL_NAME == "gemini-3.1-flash-lite-image"

    mock_candidate = MagicMock()
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake-jpeg-bytes"
    mock_part.inline_data.mime_type = "image/jpeg"
    mock_candidate.content.parts = [mock_part]

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    # Mock tool_context
    mock_tool_context = MagicMock()
    mock_tool_context.save_artifact = AsyncMock()

    with patch("google.genai.Client") as mock_genai_cls, patch(
        "google.cloud.storage.Client"
    ) as mock_storage_cls:
        mock_client = mock_genai_cls.return_value
        mock_client.models.generate_content.return_value = mock_response

        mock_storage = mock_storage_cls.return_value
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_storage.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        result = await generate_domain_image(
            prompt="Mediterranean Salmon with grilled asparagus",
            category="meal",
            tool_context=mock_tool_context,
        )

        # Verify genai client call with vertexai=True, project and global location
        mock_genai_cls.assert_called_with(
            vertexai=True,
            project="qwiklabs-gcp-03-5e6e400fb101",
            location="global",
        )
        mock_client.models.generate_content.assert_called_with(
            model="gemini-3.1-flash-lite-image",
            contents="Mediterranean Salmon with grilled asparagus",
        )

        # Verify tool_context.save_artifact was called with Part
        assert mock_tool_context.save_artifact.called
        saved_call = mock_tool_context.save_artifact.call_args
        assert "meal_" in saved_call.kwargs["filename"]
        assert saved_call.kwargs["artifact"].inline_data.data == b"fake-jpeg-bytes"

        # Verify storage upload (no local file)
        mock_storage.bucket.assert_called_with("lifesync-assets-5e6e400fb101")
        assert mock_blob.upload_from_string.called
        upload_args = mock_blob.upload_from_string.call_args
        assert upload_args[0][0] == b"fake-jpeg-bytes"
        assert upload_args[1]["content_type"] == "image/jpeg"

        # Verify returned public URL structure
        assert result["status"] == "success"
        expected_url_prefix = f"https://storage.googleapis.com/{BUCKET_NAME}/images/"
        assert result["image_url"].startswith(expected_url_prefix)
        assert result["url"].startswith(expected_url_prefix)
