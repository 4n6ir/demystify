import boto3
import json
import os
from boto3.dynamodb.conditions import Key

def handler(event, context):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    try:

        parsed = event['item'].split(':')

        if parsed[1][-1] == '*':
            action = parsed[1][:-1]
        else:
            action = parsed[1]

        response = table.query(
            KeyConditionExpression = Key('pk').eq('AWS#') & Key('sk').begins_with('ACTION#'+parsed[0].lower()+'#'+action)
        )
        responsedata = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=Key('pk').eq('AWS#') & Key('sk').begins_with('ACTION#'+parsed[0].lower()+'#'+action),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            responsedata.extend(response['Items'])

        output = {}
        output['search'] = event['item']
        output['count'] = len(responsedata)
        items = []
        for item in responsedata:
            items.append(item['service']+':'+item['action'])
        output['items'] = items

    except:
        responsedata = []
        pass

    if len(responsedata) == 0:
        output = {"RequiredFormat": {"item": "s3:GetObject*"}}

    return {
        'statusCode': 200,
        'body': json.dumps(output)
    }