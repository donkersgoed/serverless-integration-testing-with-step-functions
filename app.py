#!/usr/bin/env python3
"""The main app. Contains all the stacks."""

# Standard library imports
# -

# Third party imports
# -

# Local application/library specific imports
from aws_cdk import core as cdk
from serverless_integration_testing_with_step_functions.serverless_integration_testing_with_step_functions_stack import (
    ServerlessIntegrationTestingWithStepFunctionsStack,
)


app = cdk.App()
ServerlessIntegrationTestingWithStepFunctionsStack(
    scope=app,
    construct_id="ServerlessIntegrationTestingWithStepFunctionsStack",
)

app.synth()
