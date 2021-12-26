# Standard library imports
import os
import time

# Third party imports
import boto3


s3 = boto3.resource("s3")
s3_bucket_name = os.environ.get("S3_BUCKET")


def event_handler(_event, _context):
    """Arrange and Act: put the example file in the S3 Bucket."""
    # 1. Arrange
    now = time.time()
    object_key = f"test_file_{now}.png"

    # 2. Act
    try:
        s3.Bucket(s3_bucket_name).upload_file("example.png", object_key)
        return {"act_success": True, "test_object_key": object_key}
    except Exception as exc:  # pylint: disable=broad-except
        return {"act_success": False, "error_message": "failed to put object"}
