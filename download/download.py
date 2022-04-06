### https://awspolicygen.s3.amazonaws.com/policygen.html ###

import boto3
import datetime
import json
import logging
import os
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    
    orig = datetime.datetime.now()
    
    r = requests.get('https://awspolicygen.s3.amazonaws.com/js/policies.js')
    logger.info('Download Status Code: '+str(r.status_code))

    if r.status_code == 200:
        
        with open('/tmp/policies.js', 'wb') as f:
            f.write(r.content)
        f.close()
    
        f = open('/tmp/policies.js','r')
        
        reading = f.readline()
        output = reading.split('HasResource')
        output = output[1:-1]

        for item in output:
            parsedstart = item.split('[')
            named = parsedstart[0].split(':')
            longname = named[1].split('"')
            thelongname = longname[1]
            shortname = named[3].split('"')
            theshortname = shortname[1]
            parsedend = parsedstart[1].split(']')
            parsedlist = parsedend[0].split(',')
            table.put_item(
                Item= {  
                    'pk': 'AWS#',
                    'sk': 'SERVICE#'+theshortname,
                    'name': thelongname,
                    'service': theshortname,
                    'lastseen': str(orig)
                }
            )      
            for action in parsedlist:
                theaction = action[1:-1]
                table.put_item(
                    Item= {
                        'pk': 'AWS#',
                        'sk': 'ACTION#'+theshortname+'#'+theaction,
                        'name': thelongname,
                        'service': theshortname,
                        'action': theaction,
                        'lastseen': str(orig)
                    }
                ) 

    return {
        'statusCode': 200,
        'body': json.dumps('Download IAM Permissions')
    }
