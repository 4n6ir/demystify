import boto3
import json
import os
from boto3.dynamodb.conditions import Key

def handler(event, context):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

    try:

        if event['item'][-1] == '*':
            service = event['item'][:-1]
        else:
            service = event['item']

        response = table.query(
            KeyConditionExpression = Key('pk').eq('AWS#') & Key('sk').begins_with('SERVICE#'+service.lower())
        )
        responsedata = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.query(
                KeyConditionExpression=Key('pk').eq('AWS#') & Key('sk').begins_with('SERVICEN#'+service.lower()),
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            responsedata.extend(response['Items'])

        output = {}
        output['search'] = event['item']
        output['count'] = len(responsedata)
        items = []
        for item in responsedata:
            items.append(item['service']+' --> '+item['name'])
        output['items'] = items

    except:
        responsedata = []
        pass

    if len(responsedata) == 0:
        output = {"RequiredFormat": {"item": "sso*"}}

    return {
        'statusCode': 200,
        'body': json.dumps(output)
    }