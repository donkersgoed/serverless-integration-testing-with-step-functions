#!/usr/bin/env python3
"""The main app. Contains all the stacks."""

# Third party imports
from aws_cdk import core as cdk

# Local application/library specific imports
from serverless_integration_testing_with_step_functions.serverless_integration_testing_with_step_functions_stack import (  # pylint: disable=line-too-long
    ServerlessIntegrationTestingWithStepFunctionsStack,
)


app = cdk.App()
ServerlessIntegrationTestingWithStepFunctionsStack(
    scope=app,
    construct_id="ServerlessIntegrationTestingWithStepFunctionsStack",
)

app.synth()
