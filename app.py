#!/usr/bin/env python3
import os

import aws_cdk as cdk

from demystify.demystify_stack import DemystifyStack

app = cdk.App()

DemystifyStack(
    app, 'DemystifyStack',
    env = cdk.Environment(
        account = os.getenv('CDK_DEFAULT_ACCOUNT'),
        region = 'us-west-2'
    ),
    synthesizer = cdk.DefaultStackSynthesizer(
        qualifier = '4n6ir'
    )
)

cdk.Tags.of(app).add('demystify','demystify')

app.synth()
