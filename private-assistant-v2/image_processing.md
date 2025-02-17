## Image Processing with Bedrock Agent

To handle images with the Bedrock Agent, the following has been implemented:

1. Both `invoke_agent` functions in `lambda_function.py` and `bedrock_agent.py` now accept an optional `image_data` parameter.
2. When `image_data` is provided, it is added to the request parameters as `inputImage` with the image bytes.
3. The image should be provided as bytes from an S3 bucket.

Example usage:
```python
import boto3

# Get image from S3
s3 = boto3.client('s3')
response = s3.get_object(Bucket='XXXXXXXXXXX', Key='path/to/image.jpg')
image_data = response['Body'].read()

# Call the agent with image
result = invoke_agent(agent_id, agent_alias_id, session_id, prompt, image_data=image_data)
```

Note: The image must be provided in a format supported by Bedrock Agent Runtime service (jpg/jpeg, png, etc.).