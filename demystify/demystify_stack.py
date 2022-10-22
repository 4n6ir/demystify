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
    aws_sns_subscriptions as _subs,
    aws_ssm as _ssm,
)

from constructs import Construct

class DemystifyStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        account = Stack.of(self).account
        region = Stack.of(self).region

    ### LAMBDA LAYER ###

        if region == 'ap-northeast-1' or region == 'ap-south-1' or region == 'ap-southeast-1' or \
            region == 'ap-southeast-2' or region == 'eu-central-1' or region == 'eu-west-1' or \
            region == 'eu-west-2' or region == 'me-central-1' or region == 'us-east-1' or \
            region == 'us-east-2' or region == 'us-west-2': number = str(1)

        if region == 'af-south-1' or region == 'ap-east-1' or region == 'ap-northeast-2' or \
            region == 'ap-northeast-3' or region == 'ap-southeast-3' or region == 'ca-central-1' or \
            region == 'eu-north-1' or region == 'eu-south-1' or region == 'eu-west-3' or \
            region == 'me-south-1' or region == 'sa-east-1' or region == 'us-west-1': number = str(2)

        layer = _lambda.LayerVersion.from_layer_version_arn(
            self, 'layer',
            layer_version_arn = 'arn:aws:lambda:'+region+':070176467818:layer:getpublicip:'+number
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
                    'access-analyzer:ValidatePolicy',
                    'dynamodb:PutItem',
                    'dynamodb:Query',
                ],
                resources = [
                    '*'
                ]
            )
        )

    ### ERROR ###

        error = _lambda.Function.from_function_arn(
            self, 'error',
            'arn:aws:lambda:'+region+':'+account+':function:shipit-error'
        )

        timeout = _lambda.Function.from_function_arn(
            self, 'timeout',
            'arn:aws:lambda:'+region+':'+account+':function:shipit-timeout'
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
            destination = _destinations.LambdaDestination(timeout),
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
            timeout = Duration.seconds(60),
            memory_size = 512,
            layers = [
                layer
            ]
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
            destination = _destinations.LambdaDestination(timeout),
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
            timeout = Duration.seconds(60),
            memory_size = 512,
            layers = [
                layer
            ]
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
            destination = _destinations.LambdaDestination(timeout),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
        )

### IAM ###

        iam = _lambda.Function(
            self, 'iamrole',
            function_name = 'iam',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('iam'),
            handler = 'iam.handler',
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(60),
            memory_size = 512,
            role = role,
            layers = [
                layer
            ]
        )

        iamlogs = _logs.LogGroup(
            self, 'iamlogs',
            log_group_name = '/aws/lambda/'+iam.function_name,
            retention = _logs.RetentionDays.INFINITE,
            removal_policy = RemovalPolicy.DESTROY
        )

        iamsub = _logs.SubscriptionFilter(
            self, 'iamsub',
            log_group = iamlogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        iamtime= _logs.SubscriptionFilter(
            self, 'iamtime',
            log_group = iamlogs,
            destination = _destinations.LambdaDestination(timeout),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
        )

### RESOURCE ###

        resource = _lambda.Function(
            self, 'resource',
            function_name = 'resource',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('resource'),
            handler = 'resource.handler',
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(60),
            memory_size = 512,
            role = role,
            layers = [
                layer
            ]
        )

        resourcelogs = _logs.LogGroup(
            self, 'resourcelogs',
            log_group_name = '/aws/lambda/'+resource.function_name,
            retention = _logs.RetentionDays.INFINITE,
            removal_policy = RemovalPolicy.DESTROY
        )

        resourcesub = _logs.SubscriptionFilter(
            self, 'resourcesub',
            log_group = resourcelogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        resourcetime= _logs.SubscriptionFilter(
            self, 'resourcetime',
            log_group = resourcelogs,
            destination = _destinations.LambdaDestination(timeout),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
        )

### SCP ###

        scp = _lambda.Function(
            self, 'scp',
            function_name = 'scp',
            runtime = _lambda.Runtime.PYTHON_3_9,
            code = _lambda.Code.from_asset('scp'),
            handler = 'scp.handler',
            architecture = _lambda.Architecture.ARM_64,
            timeout = Duration.seconds(60),
            memory_size = 512,
            role = role,
            layers = [
                layer
            ]
        )

        scplogs = _logs.LogGroup(
            self, 'scplogs',
            log_group_name = '/aws/lambda/'+scp.function_name,
            retention = _logs.RetentionDays.INFINITE,
            removal_policy = RemovalPolicy.DESTROY
        )

        scpsub = _logs.SubscriptionFilter(
            self, 'scpsub',
            log_group = scplogs,
            destination = _destinations.LambdaDestination(error),
            filter_pattern = _logs.FilterPattern.all_terms('ERROR')
        )

        scptime= _logs.SubscriptionFilter(
            self, 'scptime',
            log_group = scplogs,
            destination = _destinations.LambdaDestination(timeout),
            filter_pattern = _logs.FilterPattern.all_terms('Task','timed','out')
        )
