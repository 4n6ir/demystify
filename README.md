# demystify

AWS SDK for JavaScript contains a list of all Actions available for every Service to grant IAM access permissions. 

 - https://aws.amazon.com/sdk-for-javascript/

The download information originates from the AWS Policy Generator 

 - https://awspolicygen.s3.amazonaws.com/policygen.html

```python
import json
import sys

if __name__ == '__main__':
    json.dump(json.load(sys.stdin),sys.stdout)
```
