# demystify

AWS SDK for JavaScript contains a list of all Actions available for every Service to grant IAM access permissions. 

 - https://aws.amazon.com/sdk-for-javascript/

The download information originates from the AWS Policy Generator 

 - https://awspolicygen.s3.amazonaws.com/policygen.html

Demystify provides AWS Chatbot integration with Slack Channels for IAM action and service lookups.

```
@aws invoke action --payload {"item": "s3:GetObject*”}
```

```
@aws invoke service --payload {"item": "sso*”}
```

IAM Access Analyzer provides the security validation for identity, resource, and service control JSON policies. 

```
@aws invoke iam --payload <json>
```

```
@aws invoke resource --payload <json>
```

```
@aws invoke scp --payload <json>
```

Convert multi-line JSON to a single line with Python for compatibility.

```python
import json
import sys

if __name__ == '__main__':
    json.dump(json.load(sys.stdin),sys.stdout)
```
