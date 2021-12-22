#!/usr/bin/env python3
"""The main app. Contains all the stacks."""

# Standard library imports
# -

# Related third party imports
# -

# Local application/library specific imports
from aws_cdk import core as cdk
from config import Config
from serverless_integration_testing_with_step_functions.serverless_integration_testing_with_step_functions_stack import (
    ServerlessIntegrationTestingWithStepFunctionsStack,
)

config = Config()

app = cdk.App()
ServerlessIntegrationTestingWithStepFunctionsStack(
    scope=app,
    construct_id="ServerlessIntegrationTestingWithStepFunctionsStack",
    config=config.base(),
)

app.synth()
