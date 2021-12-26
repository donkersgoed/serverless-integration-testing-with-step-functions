# Standard library imports
import os

# Third party imports
import boto3


s3_client = boto3.client("s3")
s3_bucket_name = os.environ.get("S3_BUCKET")


def event_handler(event, _context):
    """Assert and Clean Up: verify the metadata and delete the object."""
    # If the arrange / act step returned an error, bail early
    if not event["arrange_act_payload"]["act_success"]:
        return error_response(event["arrange_act_payload"]["error_message"])

    test_object_key = event["arrange_act_payload"]["test_object_key"]

    # 3. Assert
    image_object = s3_client.get_object(Bucket=s3_bucket_name, Key=test_object_key)

    # Assert metadata is present
    if "Metadata" not in image_object:
        return clean_up_with_error_response(test_object_key, "metadata not found")
    # Assert image_height is present
    if "image_height" not in image_object["Metadata"]:
        return clean_up_with_error_response(
            test_object_key, "'image_height' metadata not found"
        )
    # Assert image_width is present
    if "image_width" not in image_object["Metadata"]:
        return clean_up_with_error_response(
            test_object_key, "'image_width' metadata not found"
        )
    # Assert image_height matches expected value
    if image_object["Metadata"]["image_height"] != "178":
        return clean_up_with_error_response(test_object_key, "'image_height' incorrect")
    # Assert image_width matches expected value
    if image_object["Metadata"]["image_width"] != "172":
        return clean_up_with_error_response(test_object_key, "'image_width' incorrect")

    # Return success
    return clean_up_with_success_response(test_object_key)


def error_response(error_message):
    """Return a well-formed error message."""
    return {
        "success": False,
        "test_name": "s3_png_metadata",
        "error_message": error_message,
    }


def clean_up_with_error_response(test_object_key, error_message):
    """Remove the file from S3 and return an error message."""
    s3_client.delete_object(Bucket=s3_bucket_name, Key=test_object_key)
    return error_response(error_message)


def clean_up_with_success_response(test_object_key):
    """Remove the file from S3 and return a success message."""
    s3_client.delete_object(Bucket=s3_bucket_name, Key=test_object_key)
    return {"success": True, "test_name": "s3_png_metadata"}
