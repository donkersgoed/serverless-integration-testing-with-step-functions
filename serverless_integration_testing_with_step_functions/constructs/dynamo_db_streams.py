"""Module for the DynamoDB Streams L3 Pattern."""

# Standard library imports
import json

# Third party imports
from aws_cdk import (
    core as cdk,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_lambda as lambda_,
)

# Local application/library specific imports
from serverless_integration_testing_with_step_functions.constructs.lambda_function import (
    LambdaFunction,
)


class DynamoDbStreams(cdk.Construct):
    """CDK Construct for the DDB Audit Log demo."""

    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        """Construct a new S3EventNotification."""
        super().__init__(scope, construct_id, **kwargs)

        # Create the DynamoDB Table
        self.table = dynamodb.Table(
            scope=self,
            id="Table",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            partition_key=dynamodb.Attribute(
                name="PK", type=dynamodb.AttributeType.STRING
            ),
            point_in_time_recovery=True,
            sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
            removal_policy=cdk.RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_IMAGE,
        )

        # Create the Audit Log Group
        self.audit_log_group = logs.LogGroup(
            scope=self,
            id="AuditLogGroup",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # Create a Lambda Function to process changes in DDB
        stream_processor = LambdaFunction(
            scope=self,
            construct_id="StreamProcessor",
            code=lambda_.Code.from_asset("lambda_functions/ddb_stream_processor"),
            environment={"AUDIT_LOG_GROUP_NAME": self.audit_log_group.log_group_name},
        )

        # Allow function to write to the Log Group
        self.audit_log_group.grant_write(stream_processor.function)

        # Allow function to read the DDB Stream
        self.table.grant_stream_read(stream_processor.function)

        # Stream changes in the DynamoDB Table to a Lambda Event Source Mapping
        event_source_mapping = lambda_.EventSourceMapping(
            scope=self,
            id="DdbLambdaEventSourceMapping",
            target=stream_processor.function,
            event_source_arn=self.table.table_stream_arn,
            max_batching_window=cdk.Duration.seconds(1),
            starting_position=lambda_.StartingPosition.TRIM_HORIZON,
            batch_size=1,
        )

        # Use a CDK escape hatch to configure FilterCriteria so we
        # only receive user creation events.
        cfn_event_source_mapping: lambda_.CfnEventSourceMapping = (
            event_source_mapping.node.default_child
        )
        cfn_event_source_mapping.add_property_override(
            property_path="FilterCriteria",
            value={
                "Filters": [
                    {
                        "Pattern": json.dumps(
                            {
                                "eventName": ["INSERT"],
                                "dynamodb": {
                                    "NewImage": {"PK": {"S": [{"prefix": "USER#"}]}}
                                },
                            }
                        )
                    },
                ],
            },
        )
