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


class IntegrationTestS3(cdk.Construct):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        s3_event_notification: S3EventNotification,
        **kwargs,
    ) -> None:
        """Construct a new IntegrationTestS3."""
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
            id="S3 - Arrange & Act",
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
            id="S3 - Assert & Clean Up",
            lambda_function=assert_cleanup_s3_upload.function,
            payload=sfn.TaskInput.from_object(
                {
                    "arrange_act_payload": sfn.JsonPath.string_at("$.Payload"),
                }
            ),
        )

        self.steps = arrange_step.next(sleep_step).next(assert_step)
