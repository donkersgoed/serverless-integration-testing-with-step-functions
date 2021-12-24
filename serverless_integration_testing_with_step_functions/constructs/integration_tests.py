# Standard library imports
import time

# Related third party imports
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


class IntegrationTests(cdk.Construct):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        s3_event_notification: S3EventNotification,
        **kwargs,
    ) -> None:
        """Construct a new IntegrationTests."""
        super().__init__(scope, construct_id, **kwargs)

        # Create a Lambda Function to upload an image to the bucket
        arrange_act_s3_upload = LambdaFunction(
            scope=self,
            construct_id=f"ArrangeAndActS3UploadFunction",
            code=lambda_.Code.from_asset("integration_tests/arrange_act_s3_upload"),
            environment={"S3_BUCKET": s3_event_notification.s3_bucket.bucket_name},
        )
        s3_event_notification.s3_bucket.grant_read_write(arrange_act_s3_upload.function)

        # Create a Lambda Function to assert the image metadata and clean up the file
        assert_cleanup_s3_upload = LambdaFunction(
            scope=self,
            construct_id=f"AssertAndCleanUpS3UploadFunction",
            code=lambda_.Code.from_asset("integration_tests/assert_cleanup_s3_upload"),
            environment={"S3_BUCKET": s3_event_notification.s3_bucket.bucket_name},
        )
        s3_event_notification.s3_bucket.grant_read_write(
            assert_cleanup_s3_upload.function
        )

        # The State Machine step to execute Arrange & Act
        arrange_step = sfn_tasks.LambdaInvoke(
            scope=self,
            id="Arrange & Act",
            lambda_function=arrange_act_s3_upload.function,
        )

        # Wait two seconds for the metadata to be written
        sleep_step = sfn.Wait(
            scope=self,
            id="Wait two seconds",
            time=sfn.WaitTime.duration(cdk.Duration.seconds(2)),
        )

        # The State Machine step to execute Assert & Clean Up
        assert_step = sfn_tasks.LambdaInvoke(
            scope=self,
            id="Assert & Clean Up",
            lambda_function=assert_cleanup_s3_upload.function,
            payload=sfn.TaskInput.from_object(
                {
                    "arrange_act_payload": sfn.JsonPath.string_at("$.Payload"),
                }
            ),
        )

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

        # Parallel step to contain the tests and catch errors
        parallel = sfn.Parallel(
            scope=self, id="Parallel Container", output_path="$[*].Payload"
        )
        parallel.branch(arrange_step.next(sleep_step).next(assert_step))
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
