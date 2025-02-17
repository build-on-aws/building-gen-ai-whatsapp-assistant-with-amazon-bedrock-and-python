"""Environment variables for Lambda functions."""

BEDROCK_AGENT_ENV_VARS = {
    'BEDROCK_AGENT_ID': '${TOKEN[AWS.BearerToken.BEDROCK_AGENT_ID]}',
    'BEDROCK_AGENT_ALIAS_ID': '${TOKEN[AWS.BearerToken.BEDROCK_AGENT_ALIAS_ID]}'
}