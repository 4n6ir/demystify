from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_dynamodb as _dynamodb,
    aws_events as _events,
    aws_events_targets as _targets,
    aws_iam as _iam,
    aws_lambda as _lambda,
    aws_logs as _logs,
    aws_ssm as _ssm,
)

from constructs import Construct

class DemystifyStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

### DynamoDB Table ###

        table = _dynamodb.Table(
            self, 'iam',
            partition_key = {
                'name': 'pk',
                'type': _dynamodb.AttributeType.STRING
            },
            sort_key = {
                'name': 'sk',
                'type': _dynamodb.AttributeType.STRING
            },
            billing_mode = _dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery = True,
            removal_policy = RemovalPolicy.DESTROY
        )
        
        parameter = _ssm.StringParameter(
            self, 'parameter',
            description = 'Demystify DynamoDB Table',
            parameter_name = '/demystify/dynamodb/table',
            string_value = table.table_name,
            tier = _ssm.ParameterTier.STANDARD,
        )
        
### IAM Role ###
        
        role = _iam.Role(
            self, 'role',
            assumed_by = _iam.ServicePrincipal(
                'lambda.amazonaws.com'
            )
        )
        
        role.add_managed_policy(
            _iam.ManagedPolicy.from_aws_managed_policy_name(
                'service-role/AWSLambdaBasicExecutionRole'
            )
        )
        
        role.add_to_policy(
            _iam.PolicyStatement(
                actions = [
                    'dynamodb:PutItem',
                    'dynamodb:Query',
                ],
                resources = [
                    '*'
                ]
            )
        )

### Download Lambda ###

        download = _lambda.DockerImageFunction(
            self, 'download',
            code = _lambda.DockerImageCode.from_image_asset('download'),
            timeout = Duration.seconds(900),
            role = role,
            environment = dict(
                DYNAMODB_TABLE = table.table_name
            ),
            memory_size = 512
        )

        downloadlogs = _logs.LogGroup(
            self, 'downloadlogs',
            log_group_name = '/aws/lambda/'+download.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
        )

        downloadmonitor = _ssm.StringParameter(
            self, 'downloadmonitor',
            description = 'Demystify Download Monitor',
            parameter_name = '/demystify/monitor/download',
            string_value = '/aws/lambda/'+download.function_name,
            tier = _ssm.ParameterTier.STANDARD,
        )

        event = _events.Rule(
            self, 'event',
            schedule = _events.Schedule.cron(
                minute = '0',
                hour = '11',
                month = '*',
                week_day = '*',
                year = '*'
            )
        )
        event.add_target(_targets.LambdaFunction(download))

### SEARCH LEX V1 ###

        search = _lambda.Function(
            self, 'search',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('search'),
            handler = 'search.handler',
            role = role,
            environment = dict(
                DYNAMODB_TABLE = table.table_name
            ),
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(30),
            memory_size = 512
        )

        searchlogs = _logs.LogGroup(
            self, 'searchlogs',
            log_group_name = '/aws/lambda/'+search.function_name,
            retention = _logs.RetentionDays.INFINITE,
            removal_policy = RemovalPolicy.DESTROY
        )

        searchmonitor = _ssm.StringParameter(
            self, 'searchmonitor',
            description = 'Demystify Search Monitor',
            parameter_name = '/demystify/monitor/search',
            string_value = '/aws/lambda/'+search.function_name,
            tier = _ssm.ParameterTier.STANDARD,
        )
