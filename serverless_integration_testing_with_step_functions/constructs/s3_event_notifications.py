# Standard library imports
# -

# Third party imports
from aws_cdk import (
    core as cdk,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_logs as logs,
    aws_lambda as lambda_,
)

# Local application/library specific imports
from serverless_integration_testing_with_step_functions.constructs.lambda_function import (
    LambdaFunction,
)


class S3EventNotification(cdk.Construct):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        """Construct a new S3EventNotification."""
        super().__init__(scope, construct_id, **kwargs)

        # Create a Lambda Function to process image uploads
        upload_processor = LambdaFunction(
            scope=self,
            construct_id=f"UploadProcessor",
            code=lambda_.Code.from_asset("lambda_functions/s3_upload_processor"),
        )

        # Create an S3 bucket to upload images to
        self.s3_bucket = s3.Bucket(
            scope=self, id="EventBucket", removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Send out an event when images are uploaded
        supported_extensions = ["jpeg", "jpg", "gif", "png"]
        for ext in supported_extensions:
            self.s3_bucket.add_event_notification(
                s3.EventType.OBJECT_CREATED,
                s3n.LambdaDestination(fn=upload_processor.function),
                s3.NotificationKeyFilter(
                    suffix=f".{ext}",
                ),
            )

        # Allow the Lambda Function to write metadata to the bucket
        self.s3_bucket.grant_read_write(upload_processor.function)
