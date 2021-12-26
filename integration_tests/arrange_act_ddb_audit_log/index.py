"""Lambda Function for the Arrange and Act steps of the DDB test."""

# Standard library imports
import os
import time

# Third party imports
import boto3


ddb_table_name = os.environ.get("DDB_TABLE")
ddb_table = boto3.resource("dynamodb").Table(name=ddb_table_name)


def event_handler(_event, _context):
    """Arrange and Act: create a user in DDB."""
    # 1. Arrange
    now = time.time()
    user_object = {"PK": f"USER#{now}", "SK": f"USER#{now}"}

    # 2. Act
    try:
        ddb_table.put_item(Item=user_object)
        return {"act_success": True, "test_user_key": user_object}
    except Exception:  # pylint: disable=broad-except
        return {"act_success": False, "error_message": "failed to write to DDB"}
