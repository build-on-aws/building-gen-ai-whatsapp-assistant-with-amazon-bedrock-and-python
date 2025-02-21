# AWS Generative AI WhatsApp Assistant Samples

This repository provides sample implementations using [AWS AWS Cloud Development Kit (CDK)](https://aws.amazon.com/cdk/) Python for building WhatsApp AI assistants using AWS services and Amazon Bedrock. 


Here is a list of available samples:

| Use Case | Description | Key Features | AWS Services | Languages |
|----------|------------|--------------|--------------|-----------|
| [Basic WhatsApp AI Assistant](private-assistant/README.md) | Build an AI assistant with multi-language support and voice processing |<ul><li>Multi-language conversations with Claude 3.5</li><li>Voice note transcription and processing</li><li>Text message handling with [Langchain](https://python.langchain.com/)</li><li> Implements conversation memory and session handling through Amazon DynamoDB, allowing for context retention and history tracking across interactions</li></ul> | <ul><li>Amazon Bedrock</li><li>AWS Lambda</li><li>Amazon DynamoDB</li><li>Amazon API Gateway</li><li>Amazon Transcribe</li><li>Amazon S3</li></ul>| Multilanguage |
| [Enhanced Media Processing Assistant](private-assistant-v2/README.md) | Create an advanced assistant for multimedia content analysis | <ul><li>A WhatsApp assistant that processes multimedia content (images, video, audio, documents) using [Amazon Nova Model](https://aws.amazon.com/ai/generative-ai/nova/) and Amazon Bedrock Agents to maintains conversation context.</li><li>Document information extraction</li><li>Audio transcription with context</li><li>Includes conversation memory management, session handling, and the ability to process different media types while maintaining context throughout interaction.</li><li>Amazon Transcribe</li></ul>| <ul><li>Amazon Bedrock</li><li>AWS Lambda</li><li>Amazon DynamoDB</li><li>Amazon S3</li><li>Amazon Transcribe</li><li>AWS End User Messaging</li><li>Amazon SNS</li></ul> | Multilanguage |


---

**🇻🇪🇨🇱 ¡Gracias!**

**Best,**

[Eli](https://www.linkedin.com/in/lizfue/)

---

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
