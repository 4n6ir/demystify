from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)

from constructs import Construct

class DemystifyStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        