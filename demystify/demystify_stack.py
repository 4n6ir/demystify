import boto3
import sys

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
    aws_logs_destinations as _destinations,
    aws_sns as _sns,
    aws_sns_subscriptions as _subs,
    aws_ssm as _ssm,
)

from constructs import Construct

class DemystifyStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        try:
            client = boto3.client('account')
            operations = client.get_alternate_contact(
                AlternateContactType='OPERATIONS'
            )
        except:
            print('Missing IAM Permission --> account:GetAlternateContact')
            sys.exit(1)
            pass

        operationstopic = _sns.Topic(
            self, 'operationstopic'
        )

        operationstopic.add_subscription(
            _subs.EmailSubscription(operations['AlternateContact']['EmailAddress'])
        )

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

        role.add_to_policy(
            _iam.PolicyStatement(
                actions = [
                    'sns:Publish'
                ],
                resources = [
                    operationstopic.topic_arn
                ]
            )
        )

### ERROR ###

        error = _lambda.Function(
            self, 'error',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('error'),
            handler = 'error.handler',
            role = role,
            environment = dict(
                SNS_TOPIC = operationstopic.topic_arn
            ),
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(7),
            memory_size = 128
        )

        errormonitor = _logs.LogGroup(
            self, 'errormonitor',
            log_group_name = '/aws/lambda/'+error.function_name,
            retention = _logs.RetentionDays.ONE_DAY,
            removal_policy = RemovalPolicy.DESTROY
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

        downloadsub = _logs.SubscriptionFilter(
            self, 'downloadsub',
            log_group = downloadlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        downloadtime= _logs.SubscriptionFilter(
            self, 'downloadtime',
            log_group = downloadlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
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

### ACTION ###

        action = _lambda.Function(
            self, 'action',
            function_name = 'action',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('action'),
            handler = 'action.handler',
            role = role,
            environment = dict(
                DYNAMODB_TABLE = table.table_name
            ),
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(30),
            memory_size = 512
        )

        actionlogs = _logs.LogGroup(
            self, 'actionlogs',
            log_group_name = '/aws/lambda/'+action.function_name,
            retention = _logs.RetentionDays.INFINITE,
            removal_policy = RemovalPolicy.DESTROY
        )

        actionsub = _logs.SubscriptionFilter(
            self, 'actionsub',
            log_group = actionlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        actiontime= _logs.SubscriptionFilter(
            self, 'actiontime',
            log_group = actionlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
        )

### SERVICE ###

        service = _lambda.Function(
            self, 'service',
            function_name = 'service',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('service'),
            handler = 'service.handler',
            role = role,
            environment = dict(
                DYNAMODB_TABLE = table.table_name
            ),
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(30),
            memory_size = 512
        )

        servicelogs = _logs.LogGroup(
            self, 'servicelogs',
            log_group_name = '/aws/lambda/'+service.function_name,
            retention = _logs.RetentionDays.INFINITE,
            removal_policy = RemovalPolicy.DESTROY
        )

        servicesub = _logs.SubscriptionFilter(
            self, 'servicesub',
            log_group = servicelogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        servicetime= _logs.SubscriptionFilter(
            self, 'servicetime',
            log_group = servicelogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
        )
