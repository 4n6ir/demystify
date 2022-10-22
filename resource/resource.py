import boto3
import json

def handler(event, context):

    findings = []

    client = boto3.client('accessanalyzer')
    
    paginator = client.get_paginator('validate_policy')
    
    response_iterator = paginator.paginate(
        locale = 'EN',
        policyDocument = json.dumps(event),
        policyType = 'RESOURCE_POLICY'
    )

    for page in response_iterator:
        for finding in page['findings']:
            findings.append(finding)

    return {
        'statusCode': 200,
        'body': json.dumps(findings)
    }