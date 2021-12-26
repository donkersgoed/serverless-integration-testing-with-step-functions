"""Module for the Integration Test infrastructure."""

# Standard library imports
import time

# Third party imports
from aws_cdk import (
    core as cdk,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
)

# Local application/library specific imports
from serverless_integration_testing_with_step_functions.constructs.lambda_function import (
    LambdaFunction,
)
from serverless_integration_testing_with_step_functions.constructs.s3_event_notifications import (
    S3EventNotification,
)
from serverless_integration_testing_with_step_functions.constructs.dynamo_db_streams import (
    DynamoDbStreams,
)
from serverless_integration_testing_with_step_functions.constructs.integration_test_s3 import (
    IntegrationTestS3,
)
from serverless_integration_testing_with_step_functions.constructs.integration_test_ddb import (
    IntegrationTestDdb,
)


class IntegrationTests(cdk.Construct):
    """The supporting infrastructure for the integration tests, eg. the State Machine."""

    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        s3_event_notification: S3EventNotification,
        dynamo_db_streams: DynamoDbStreams,
        **kwargs,
    ) -> None:
        """Construct a new IntegrationTests."""
        super().__init__(scope, construct_id, **kwargs)

        # Lambda Function to call back to CloudFormation
        update_cfn_lambda = LambdaFunction(
            scope=self,
            construct_id="UpdateCfnLambda",
            code=lambda_.Code.from_asset("lambda_functions/update_cfn_custom_resource"),
        )

        # SFN Step for the CloudFormation Callback Function
        update_cfn_step = sfn_tasks.LambdaInvoke(
            scope=self,
            id="Update CloudFormation",
            lambda_function=update_cfn_lambda.function,
            # We pass both the original execution input AND the lambda execution
            # results to the Update CloudFormation Lambda. The function will use
            # the Lambda execution results to determine success or failure, and will
            # use the original Step Functions Execution Input to fetch the CloudFormation
            # callback parameters (ResponseURL, StackId, RequestId and LogicalResourceId).
            payload=sfn.TaskInput.from_object(
                {
                    "ExecutionInput": sfn.JsonPath.string_at("$$.Execution.Input"),
                    "IntegrationTestResults.$": "$",
                }
            ),
        )

        integration_test_s3 = IntegrationTestS3(
            scope=self,
            construct_id="TestS3",
            s3_event_notification=s3_event_notification,
        )

        integration_test_ddb = IntegrationTestDdb(
            scope=self,
            construct_id="TestDdb",
            dynamo_db_streams=dynamo_db_streams,
        )

        # Parallel step to contain the tests and catch errors
        parallel = sfn.Parallel(
            scope=self, id="Parallel Container", output_path="$[*].Payload"
        )
        parallel.branch(integration_test_s3.steps)
        parallel.branch(integration_test_ddb.steps)
        parallel.add_catch(handler=update_cfn_step, errors=["States.ALL"])

        state_machine = sfn.StateMachine(
            self,
            "StateMachine",
            definition=parallel.next(update_cfn_step),
            timeout=cdk.Duration.minutes(5),
        )

        # The Lambda Function backing the custom resource
        custom_resource_handler = LambdaFunction(
            scope=self,
            construct_id="CustomResourceHandler",
            code=lambda_.Code.from_asset("lambda_functions/custom_resource_handler"),
            environment={"STATE_MACHINE_ARN": state_machine.state_machine_arn},
        )
        state_machine.grant_start_execution(custom_resource_handler.function)

        # The CFN Custom Resource which triggers the State Machine on every deployment
        cdk.CustomResource(
            scope=self,
            id="CustomResource",
            service_token=custom_resource_handler.function.function_arn,
            # Passing the time as a parameter will trigger the custom
            # resource with every deployment.
            properties={"ExecutionTime": str(time.time())},
        )
