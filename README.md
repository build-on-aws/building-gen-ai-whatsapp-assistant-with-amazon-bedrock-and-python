# AWS Generative AI WhatsApp Assistant Samples

Sample implementations using [AWS Cloud Development Kit (CDK)](https://aws.amazon.com/cdk/?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el) and Python for building WhatsApp AI assistants powered by Amazon Bedrock.

## Projects

| Project | Description | Stack |
|---------|-------------|-------|
| [private-assistant](./private-assistant/) | WhatsApp assistant with multi-language conversations, voice transcription, and image understanding via Claude 3.5 and LangChain | ![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white) ![CDK](https://img.shields.io/badge/AWS_CDK-2.188.0-orange?logo=amazon-aws&logoColor=white) ![Claude](https://img.shields.io/badge/Claude_3.5-Sonnet%20%7C%20Haiku-blueviolet) |
| [private-assistant-v2](./private-assistant-v2/) | Advanced multimodal assistant (images, video, audio, documents) using Amazon Nova Pro and Amazon Bedrock Agents, integrated via AWS End User Messaging — no extra API layer needed | ![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white) ![CDK](https://img.shields.io/badge/AWS_CDK-2.188.0-orange?logo=amazon-aws&logoColor=white) ![Nova](https://img.shields.io/badge/Amazon_Nova-Pro-orange) |

---

## private-assistant

Classic serverless architecture using API Gateway as a WhatsApp webhook. Supports text, voice, and image messages. Conversation memory is managed via Amazon DynamoDB sessions.

**Models:** `anthropic.claude-3-5-sonnet-20241022-v2:0` · `anthropic.claude-3-5-haiku-20241022-v1:0`

**AWS Services:** Amazon Bedrock · AWS Lambda · Amazon DynamoDB · Amazon API Gateway · Amazon Transcribe · Amazon S3

**Key features:**
- Multi-language conversations (Claude replies in the user's language)
- Voice note transcription with Amazon Transcribe (`IdentifyLanguage=True`)
- Image analysis via Claude 3.5 Sonnet using the Bedrock `invoke_model` API
- Session-based conversation history stored in DynamoDB
- Two text agent options: LangChain-based (`langchain_agent_text`) or direct Bedrock API (`agent_text_v3`)

---

## private-assistant-v2

Next-generation architecture using [AWS End User Messaging](https://aws.amazon.com/end-user-messaging/?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el) for native WhatsApp integration (no API Gateway required). Messages arrive via SNS, are routed to Lambda, and processed by an Amazon Bedrock Agent that maintains full conversation context.

**Models:** `amazon.nova-pro-v1:0` (agent) · `us.amazon.nova-pro-v1:0` (multimodal via Converse API)

**AWS Services:** Amazon Bedrock (Agents + Converse API) · AWS Lambda · Amazon DynamoDB · Amazon S3 · Amazon Transcribe · AWS End User Messaging · Amazon SNS

**Key features:**
- Processes images, video, audio, and documents in a single conversation thread
- Amazon Bedrock Agent maintains context across message types
- Video processed via S3 URI; images and documents via bytes
- Audio transcribed with Amazon Transcribe then forwarded to the agent
- Conversation history stored as `ConversationHistory` in DynamoDB for the Bedrock Agent session state

---

---

## 🇻🇪🇨🇱 ¡Gracias!

**[Eli](https://www.linkedin.com/in/lizfue/)**

---

## Contributing

Contributions are welcome! See [CONTRIBUTING](CONTRIBUTING.md) for more information.

---

## Security

If you discover a potential security issue in this project, notify AWS/Amazon Security via the [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el). Please do **not** create a public GitHub issue.

---

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file for details.
