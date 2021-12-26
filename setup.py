"""Project setup."""

import setuptools

with open(file="README.md", encoding="utf-8") as fp:
    long_description = fp.read()

setuptools.setup(
    name="Serverless Integration Testing with Step Functions",
    version="0.0.1",
    description="Bite-Sized Serverless: Serverless Integration Testing with Step Functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Bite-Sized Serverless",
    package_dir={"": "serverless_integration_testing_with_step_functions"},
    packages=setuptools.find_packages(
        where="serverless_integration_testing_with_step_functions"
    ),
    install_requires=[
        "aws-cdk.aws_dynamodb==1.137.0",
        "aws-cdk.aws_lambda==1.137.0",
        "aws-cdk.aws_logs==1.137.0",
        "aws-cdk.aws_s3_notifications==1.137.0",
        "aws-cdk.aws_s3==1.137.0",
        "aws-cdk.aws_stepfunctions_tasks==1.137.0",
        "aws-cdk.aws_stepfunctions==1.137.0",
        "aws-cdk.core==1.137.0",
        "black==21.6b0",
        "boto3==1.20.26",
        "pylint==2.10.2",
        "python-dotenv==0.17.0",
        "stringcase==1.2.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
)
