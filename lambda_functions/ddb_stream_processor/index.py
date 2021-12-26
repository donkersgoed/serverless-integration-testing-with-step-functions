"""Function to process DynamoDB stream events."""


# Standard library imports
import json
import os
from dataclasses import dataclass
from typing import Optional

# Third party imports
import boto3
from botocore.exceptions import ClientError


logs_client = boto3.client("logs")
log_group_name = os.environ.get("AUDIT_LOG_GROUP_NAME")


@dataclass
class SequenceToken:
    """Container for a sequence token."""

    token: Optional[str] = None


sequence_token = SequenceToken()


def event_handler(event, context):
    """Write audit logs to CloudWatch."""
    # Create a log stream if it doesn't exist yet
    try:
        logs_client.create_log_stream(
            logGroupName=log_group_name,
            logStreamName=context.log_stream_name,
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceAlreadyExistsException":
            raise

    # Prepare the parameters for put_log_events()
    put_log_params = {
        "logGroupName": log_group_name,
        "logStreamName": context.log_stream_name,
        "logEvents": [
            {
                # Fetch the creation timestamp from the DDB item
                "timestamp": int(
                    record["dynamodb"]["ApproximateCreationDateTime"] * 1000
                ),
                # Create a dictionary combining the EventType and the data from DDB
                "message": json.dumps(
                    {"EventType": "UserCreated"} | record["dynamodb"]["NewImage"]
                ),
            }
            for record in event["Records"]
        ],
    }

    # Add the sequence token if we have one
    if sequence_token.token:
        put_log_params["sequenceToken"] = sequence_token.token

    # Write the audit log to the CloudWatch Log Group
    response = logs_client.put_log_events(**put_log_params)

    # Store the sequence token for the next iteration
    sequence_token.token = response["nextSequenceToken"]
