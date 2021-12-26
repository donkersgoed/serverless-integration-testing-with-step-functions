"""Module for the main ServerlessIntegrationTestingWithStepFunctions Stack."""

# Standard library imports
# -

# Third party imports
from aws_cdk import core as cdk

# Local application/library specific imports
from serverless_integration_testing_with_step_functions.constructs.s3_event_notifications import (
    S3EventNotification,
)
from serverless_integration_testing_with_step_functions.constructs.dynamo_db_streams import (
    DynamoDbStreams,
)
from serverless_integration_testing_with_step_functions.constructs.integration_tests import (
    IntegrationTests,
)


class ServerlessIntegrationTestingWithStepFunctionsStack(cdk.Stack):
    """The ServerlessIntegrationTestingWithStepFunctions Stack."""

    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        """Construct a new ServerlessIntegrationTestingWithStepFunctionsStack."""
        super().__init__(scope, construct_id, **kwargs)

        s3_event_notification = S3EventNotification(
            scope=self, construct_id="S3EventConstruct"
        )

        dynamo_db_streams = DynamoDbStreams(
            scope=self, construct_id="DynamoDbStreamsConstruct"
        )

        IntegrationTests(
            scope=self,
            construct_id="IntegrationTests",
            s3_event_notification=s3_event_notification,
            dynamo_db_streams=dynamo_db_streams,
        )
