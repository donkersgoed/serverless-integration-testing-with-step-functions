"""Module for the DynamoDB integration test CDK construct."""

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

from serverless_integration_testing_with_step_functions.constructs.dynamo_db_streams import (
    DynamoDbStreams,
)


class IntegrationTestDdb(cdk.Construct):
    """CDK Construct for the DynamoDB integration test."""

    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        dynamo_db_streams: DynamoDbStreams,
        **kwargs,
    ) -> None:
        """Construct a new IntegrationTestS3."""
        super().__init__(scope, construct_id, **kwargs)

        # Create a Lambda Function to upload an image to the bucket
        arrange_act_ddb_audit_log = LambdaFunction(
            scope=self,
            construct_id="ArrangeAndActDdbAudit",
            code=lambda_.Code.from_asset("integration_tests/arrange_act_ddb_audit_log"),
            environment={"DDB_TABLE": dynamo_db_streams.table.table_name},
        )
        dynamo_db_streams.table.grant_read_write_data(
            arrange_act_ddb_audit_log.function
        )

        # Create a Lambda Function to assert the image metadata and clean up the file
        assert_cleanup_ddb_audit_log = LambdaFunction(
            scope=self,
            construct_id="AssertAndCleanUpDdbAudit",
            code=lambda_.Code.from_asset(
                "integration_tests/assert_cleanup_ddb_audit_log"
            ),
            environment={
                "DDB_TABLE": dynamo_db_streams.table.table_name,
                "LOG_STREAM_NAME": dynamo_db_streams.audit_log_group.log_group_name,
            },
        )
        dynamo_db_streams.table.grant_read_write_data(
            assert_cleanup_ddb_audit_log.function
        )
        dynamo_db_streams.audit_log_group.grant(
            assert_cleanup_ddb_audit_log.function, "logs:FilterLogEvents"
        )

        # The State Machine step to execute Arrange & Act
        arrange_step = sfn_tasks.LambdaInvoke(
            scope=self,
            id="DDB - Arrange & Act",
            lambda_function=arrange_act_ddb_audit_log.function,
        )

        # Wait ten seconds for the audit log to be written
        sleep_step = sfn.Wait(
            scope=self,
            id="Wait ten seconds",
            time=sfn.WaitTime.duration(cdk.Duration.seconds(10)),
        )

        # The State Machine step to execute Assert & Clean Up
        assert_step = sfn_tasks.LambdaInvoke(
            scope=self,
            id="DDB - Assert & Clean Up",
            lambda_function=assert_cleanup_ddb_audit_log.function,
            payload=sfn.TaskInput.from_object(
                {
                    "arrange_act_payload": sfn.JsonPath.string_at("$.Payload"),
                }
            ),
        )

        self.steps = arrange_step.next(sleep_step).next(assert_step)
