"""Created by: Andrew R. DeFilippis"""

# Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.


from json import dumps
from base64 import b64encode


def lambda_handler(event, context):
    """Respond with the ingested event to echo back what is received. The response is formatted for Lambda Proxy
    Integration in API Gateway.
    """
    # Define the response parameters
    status_code = 200  # (int) Required
    response_headers = {  # (dict) Optional
        'Content-Type': 'application/json',
        'Lambda-Request-ID': context.aws_request_id
    }
    response_body = dumps(event)  # (str, bytes) Optional
    response_body_is_binary = False  # (boolean) Optional

    # Build the response object
    api_response = {'statusCode': status_code}
    if response_headers is not None:
        api_response['headers'] = response_headers
    if response_body is not None and response_body_is_binary is True:
        api_response['body'] = b64encode(response_body)
        api_response['isBase64Encoded'] = True
    elif response_body is not None:
        api_response['body'] = response_body

    # Return the response object
    return api_response
