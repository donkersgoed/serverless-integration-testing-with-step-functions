"""Function to process DynamoDB stream events."""


# Standard library imports
import json
import os
from dataclasses import dataclass
from typing import Optional

# Third party imports
import boto3
from botocore.exceptions import ClientError

# Local application/library specific imports
# -


# Example payload
# {
#     "Records": [
#         {
#             "eventID": "f29b79cca72c0d21942eba17352ed089",
#             "eventName": "INSERT",
#             "eventVersion": "1.1",
#             "eventSource": "aws:dynamodb",
#             "awsRegion": "eu-west-1",
#             "dynamodb": {
#                 "ApproximateCreationDateTime": 1640381675,
#                 "Keys": {
#                     "SK": {
#                         "S": "USER#1"
#                     },
#                     "PK": {
#                         "S": "USER#1"
#                     }
#                 },
#                 "NewImage": {
#                     "SK": {
#                         "S": "USER#1"
#                     },
#                     "PK": {
#                         "S": "USER#1"
#                     }
#                 },
#                 "SequenceNumber": "112700000000031026986431",
#                 "SizeBytes": 32,
#                 "StreamViewType": "NEW_IMAGE"
#             },
#             "eventSourceARN": "arn:aws:dynamodb:eu-west-1:739178438747:table/ServerlessIntegrationTestingWithStepFunctionsStack-DynamoDbStreamsConstructTable157C6B88-CQALKZ11Z4NY/stream/2021-12-24T21:26:23.287"
#         }
#     ]
# }

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
