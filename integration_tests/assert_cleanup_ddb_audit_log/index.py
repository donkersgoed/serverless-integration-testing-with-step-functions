"""Lambda Function for the Assert and Clean Up steps of the DDB test."""

# Standard library imports
import json
import os
from datetime import datetime, timedelta

# Third party imports
import boto3


logs_client = boto3.client("logs")
log_group_name = os.environ.get("LOG_STREAM_NAME")

ddb_table_name = os.environ.get("DDB_TABLE")
ddb_table = boto3.resource("dynamodb").Table(name=ddb_table_name)


def event_handler(event, _context):
    """Assert and Clean Up: verify the metadata and delete the object."""
    # If the arrange / act step returned an error, bail early
    if not event["arrange_act_payload"]["act_success"]:
        return error_response(event["arrange_act_payload"]["error_message"])

    test_user_key = event["arrange_act_payload"]["test_user_key"]
    test_user_pk = test_user_key["PK"]
    test_user_sk = test_user_key["SK"]

    expected_json = {
        "EventType": "UserCreated",
        "PK": {"S": test_user_pk},
        "SK": {"S": test_user_sk},
    }

    # 3. Assert

    # Filter the sought event from the CloudWatch Log Group
    filter_pattern = (
        f'{{ ($.EventType = "UserCreated") && ($.SK.S = "{test_user_pk}") '
        f'&& ($.PK.S = "{test_user_sk}") }}'
    )

    # Set the search horizon to one minute ago
    start_time = int((datetime.today() - timedelta(minutes=1)).timestamp()) * 1000

    # Execute the search
    response = logs_client.filter_log_events(
        logGroupName=log_group_name, startTime=start_time, filterPattern=filter_pattern
    )

    # Assert exactly one event matching the pattern is found
    if "events" not in response:
        return clean_up_with_error_response(
            test_user_pk, test_user_sk, "events not found"
        )

    if len(response["events"]) == 0:
        return clean_up_with_error_response(
            test_user_pk, test_user_sk, "event not found"
        )

    if len(response["events"]) != 1:
        return clean_up_with_error_response(
            test_user_pk, test_user_sk, "more than one event found"
        )

    if json.loads(response["events"][0]["message"]) != expected_json:
        return clean_up_with_error_response(
            test_user_pk, test_user_sk, "log event does not match expected JSON"
        )

    # Return success
    return clean_up_with_success_response(test_user_pk, test_user_sk)


def error_response(error_message):
    """Return a well-formed error message."""
    return {
        "success": False,
        "test_name": "ddb_user_audit_log",
        "error_message": error_message,
    }


def clean_up_with_error_response(test_user_pk, test_user_sk, error_message):
    """Remove the file from DDB and return an error message."""
    ddb_table.delete_item(
        Key={
            "PK": test_user_pk,
            "SK": test_user_sk,
        }
    )
    return error_response(error_message)


def clean_up_with_success_response(test_user_pk, test_user_sk):
    """Remove the file from DDB and return a success message."""
    ddb_table.delete_item(
        Key={
            "PK": test_user_pk,
            "SK": test_user_sk,
        }
    )
    return {"success": True, "test_name": "ddb_user_audit_log"}
