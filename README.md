# AWS Generative AI WhatsApp Assistant Samples

This repository provides sample implementations using [AWS AWS Cloud Development Kit (CDK)](https://aws.amazon.com/cdk/) Python for building WhatsApp AI assistants using AWS services and Amazon Bedrock. 


Here is a list of available samples:

| Use Case | Description | Key Features | AWS Services | Languages |
|----------|------------|--------------|--------------|-----------|
| [Basic WhatsApp AI Assistant](private-assistant/README.md) | Build an AI assistant with multi-language support and voice processing |<ul><li>Multi-language conversations with Claude 3.5</li><li>Voice note transcription and processing</li><li>Text message handling with [Langchain](https://python.langchain.com/)</li><li> Implements conversation memory and session handling through Amazon DynamoDB, allowing for context retention and history tracking across interactions</li></ul> | <ul><li>[Amazon Bedrock](https://aws.amazon.com/bedrock/)</li><li>[AWS Lambda](https://aws.amazon.com/lambda/)</li><li>[Amazon DynamoDB](https://aws.amazon.com/dynamodb/)</li><li>[Amazon API Gateway](https://aws.amazon.com/api-gateway/)</li><li>[Amazon Transcribe](https://aws.amazon.com/transcribe/)</li><li>[Amazon S3](https://aws.amazon.com/s3/)</li></ul>| Multilanguage |
| [Enhanced Media Processing Assistant](private-assistant-v2/README.md) | Create an advanced assistant for multimedia content analysis | <ul><li>A WhatsApp assistant that processes multimedia content (images, video, audio, documents) using [Amazon Nova Model](https://aws.amazon.com/ai/generative-ai/nova/) and Amazon Bedrock Agents to maintains conversation context.</li><li>Document information extraction</li><li>Audio transcription with context</li><li>Includes conversation memory management, session handling, and the ability to process different media types while maintaining context throughout interaction.</li><li>Amazon Transcribe</li></ul>| <ul><li>[Amazon Bedrock](https://aws.amazon.com/bedrock/)</li><li>[AWS Lambda](https://aws.amazon.com/lambda/)</li><li>[Amazon DynamoDB](https://aws.amazon.com/dynamodb/)</li><li>[Amazon S3](https://aws.amazon.com/s3/)</li><li>[Amazon Transcribe](https://aws.amazon.com/transcribe/)</li><li>[AWS End User Messaging](https://aws.amazon.com/end-user-messaging/)</li><li>[Amazon SNS](https://aws.amazon.com/sns/)</li></ul> | Multilanguage |


---

**🇻🇪🇨🇱 ¡Gracias!**

**Best,**

[Eli](https://www.linkedin.com/in/lizfue/)

---

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
