"""Lambda function that reports the state machine results back to CFN."""
from dataclasses import dataclass
import json
import urllib3

http = urllib3.PoolManager()


@dataclass
class CfnProperties:
    cfn_url: str
    cfn_stack_id: str
    cfn_request_id: str
    logical_resource_id: str


def event_handler(event, _context):
    """Return a success or failure to the CFN Custom Resource."""
    print(json.dumps(event))
    cfn_props = CfnProperties(
        cfn_url=event["ExecutionInput"]["ResponseURL"],
        cfn_stack_id=event["ExecutionInput"]["StackId"],
        cfn_request_id=event["ExecutionInput"]["RequestId"],
        logical_resource_id=event["ExecutionInput"]["LogicalResourceId"],
    )

    # Successful Lambda executions will look like this:
    # {
    #     "ExecutionInput": {
    #         ...
    #     },
    #     "IntegrationTestResults": [
    #         {
    #             "success": true,
    #             "test_name": "s3_png_metadata"
    #         }
    #     ]
    # }

    #
    # While failing results look like this:
    # "IntegrationTestResults": {
    #     "Error": "RuntimeError",
    #     "Cause": "..."
    # }

    lambda_results = event["IntegrationTestResults"]
    parallel_success = isinstance(lambda_results, list)

    if not parallel_success:
        return error_response(
            msg="Execution error in parallel state", cfn_props=cfn_props
        )
    errors = []
    for result in lambda_results:
        if not result["success"]:
            errors.append(result["test_name"])

    if errors:
        return error_response(
            msg=f"Tests failed: [{', '.join(errors)}]", cfn_props=cfn_props
        )

    return success_response(cfn_props=cfn_props)


def error_response(msg: str, cfn_props: CfnProperties) -> None:
    print(f"Reporting error: {msg}")
    call_cloudformation(
        {
            "Status": "FAILED",
            "Reason": msg,
            "PhysicalResourceId": cfn_props.logical_resource_id,
            "StackId": cfn_props.cfn_stack_id,
            "RequestId": cfn_props.cfn_request_id,
            "LogicalResourceId": cfn_props.logical_resource_id,
        },
        cfn_props.cfn_url,
    )


def success_response(cfn_props: CfnProperties) -> None:
    print("Reporting success")
    call_cloudformation(
        {
            "Status": "SUCCESS",
            "PhysicalResourceId": cfn_props.logical_resource_id,
            "StackId": cfn_props.cfn_stack_id,
            "RequestId": cfn_props.cfn_request_id,
            "LogicalResourceId": cfn_props.logical_resource_id,
        },
        cfn_props.cfn_url,
    )


def call_cloudformation(body: dict, cfn_url: str) -> None:
    http.request(
        "PUT",
        cfn_url,
        headers={"Content-Type": "application/json"},
        body=json.dumps(body),
    )
