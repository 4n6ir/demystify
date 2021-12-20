import boto3
import json
import logging
import os
from boto3.dynamodb.conditions import Key
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response

def default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)

def handler(event, context):
    
    logger.info(event)
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    
    session_attributes = event['sessionAttributes'] if event['sessionAttributes'] is not None else {}
    slots = event['currentIntent']['slots']
    awsiam = slots['awsiam']

    try:
        parsed = awsiam.split(':')
        if len(parsed) == 2:
            
            response = table.query(
                KeyConditionExpression = Key('pk').eq('AWS#') & Key('sk').begins_with('ACTION#'+parsed[0].lower()+'#'+parsed[1][:-1])
            )
            responsedata = response['Items']
            while 'LastEvaluatedKey' in response:
                response = table.query(
                    KeyConditionExpression=Key('pk').eq('AWS#') & Key('sk').begins_with('ACTION#'+parsed[0].lower()+'#'+parsed[1][:-1]),
                    ExclusiveStartKey=response['LastEvaluatedKey']
                )
                responsedata.extend(response['Items'])
            
            output = json.dumps(responsedata, default=default)
            clean = json.loads(output)
            
            permissions = []
            
            for item in clean:
                permissions.append(item['service']+':'+item['action'])    
                
            msg = permissions
            
        else:
            msg = 'Try s3:Get*'
    except:
        msg = 'Try s3:Get*'
        pass

    return close(
		session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': str(msg)
        }
	)
