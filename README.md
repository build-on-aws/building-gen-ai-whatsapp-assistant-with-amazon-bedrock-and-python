# Building a WhatsApp generative AI assistant with Amazon Bedrock and Python.

With this WhatsApp app, you can chat in any language with a [Large language models (LLM)](https://community.aws/posts/how-to-choose-your-llm) on Amazon Bedrock. Send voice notes and receive transcriptions. By making a minor change in the code, you can also send the transcription to the model.

Your data will be securely stored in your AWS account and will not be shared or used for model training. It is not recommended to share private information because the security of data with WhatsApp is not guaranteed.

![Digrama parte 1](/imagenes/gif_001.gif)     
![Digrama parte 1](/imagenes/image_claude_v2.gif)**          




### ** UPDATE: Power with [Anthropic's Claude 3](https://aws.amazon.com/bedrock/claude/?th=tile&tile=anthropic&p=1)


✅ **AWS Level**: Intermediate - 200   

**Prerequisites:**

- [AWS Account](https://aws.amazon.com/resources/create-account/?sc_channel=el&sc_campaign=datamlwave&sc_content=cicdcfnaws&sc_geo=mult&sc_country=mult&sc_outcome=acq) 
-  [Foundational knowledge of Python](https://catalog.us-east-1.prod.workshops.aws/workshops/3d705026-9edc-40e8-b353-bdabb116c89c/) 

💰 **Cost to complete**: 
- [Amazon Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Amazon Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Amazon Transcribe Pricing](https://aws.amazon.com/transcribe/pricing/)
- [Amazon DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)
- [Amazon APIGateway Pricing](https://aws.amazon.com/api-gateway/pricing/)
- [Whatsapp pricing](https://developers.facebook.com/docs/whatsapp/pricing/)

## How The App Works
![Digrama parte 1](/imagenes/flow.jpg)

### 1- Message input:

![Digrama parte 1](/imagenes/1_step.jpg)

1. WhatsApp receives the message: voice/text/image.
2. [Amazon API Gateway](https://aws.amazon.com/api-gateway/) receives the message from the [WhatsApp webhook](https://business.whatsapp.com/blog/how-to-use-webhooks-from-whatsapp-business-api) (previously authenticated).
3. Then, an [AWS Lambda Functions](https://aws.amazon.com/es/pm/lambda) named [whatsapp_in](/private-assistant/lambdas/code/whatsapp_in/lambda_function.py) processes the message and sends it to an [Amazon DynamoDB](https://aws.amazon.com/pm/dynamodb/) table named whatsapp-metadata to store it.
4. The DynamoDB table whtsapp-metadata has a [DynamoDB streaming](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html) configured, which triggers the [process_stream](/private-assistant/lambdas/code/process_stream/lambda_function.py) Lambda Function.

### 2 - Message processing:

#### Text Message:

![Digrama parte 1](/imagenes/2_step.jpg)
[process_stream](/private-assistant/lambdas/code/process_stream/lambda_function.py) Lambda Function sends the text of the message to a Lambda Function . 

In this application are 2 Lambda Functions that can fulfill this function, one that uses LangChain to handle the conversations and Amazon Bedrock to invoke the LLM, named [langchain_agent_text](/private-assistant/lambdas/code/langchain_agent_text/lambda_function.py), another that uses the Amazon Bedrock API call directly named [agent_text_v3](https://github.com/build-on-aws/building-gen-ai-whatsapp-assistant-with-amazon-bedrock-and-python/blob/main/private-assistant/lambdas/code/agent_text_v3/lambda_function.py) with [Claude 3 Sonnet](https://www.anthropic.com/news/claude-3-family) , which one to use is up to you.

#### Voice Message:

![Digrama parte 1](/imagenes/2_1_step.jpg)

1. The [audio_job_transcriptor](/private-assistant/lambdas/code/audio_job_transcriptor/lambda_function.py) Lambda Function is triggered. This Lambda Function downloads the WhatsApp audio from the link in the message in an [Amazon S3](https://aws.amazon.com/es/s3/) bucket, using Whatsapp Token authentication, then converts the audio to text using the Amazon Transcribe [start_transcription_job](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/transcribe/client/start_transcription_job.html) API, which leaves the transcript file in an Output Amazon S3 bucket.

Function that invokes audio_job_transcriptor looks like this:

```python
def start_job_transciptor (jobName,s3Path_in,OutputKey,codec):
    response = transcribe_client.start_transcription_job(
            TranscriptionJobName=jobName,
            IdentifyLanguage=True,
            MediaFormat=codec,
            Media={
            'MediaFileUri': s3Path_in
            },
            OutputBucketName = BucketName,
            OutputKey=OutputKey 
            )
```
            
> 💡  Notice that the IdentifyLanguage parameter is configured to True. Amazon Transcribe can determine the primary language in the audio.
  
![Digrama parte 1](/imagenes/2_2_step.jpg)

2. The [transcriber_done](/private-assistant/lambdas/code/transcriber_done/lambda_function.py) Lambda Function is triggered with an [Amazon S3 Event Notification put item](https://docs.aws.amazon.com/AmazonS3/latest/userguide/EventNotifications.html) once the Transcribe Job is complete. It extracts the transcript from the Output S3 bucket and sends it to [whatsapp_out](/private-assistant/lambdas/code/transcriber_done/lambda_function.py) Lambda Function to respond to WhatsApp.

> ✅ You have the option to uncomment the code in the [transcriber_done](/private-assistant/lambdas/code/transcriber_done/lambda_function.py) Lambda Function and send the voice note transcription to [langchain_agent_text](/private-assistant/lambdas/code/langchain_agent_text/lambda_function.py) Lambda Function. 

```Python
try:       
    response_3 = lambda_client.invoke(
        FunctionName = LAMBDA_AGENT_TEXT,
        InvocationType = 'Event' ,#'RequestResponse', 
        Payload = json.dumps({
            'whats_message': text,
            'whats_token': whats_token,
            'phone': phone,
            'phone_id': phone_id,
            'messages_id': messages_id

        })
    )

    print(f'\nRespuesta:{response_3}')

    return response_3
    
except ClientError as e:
    err = e.response
    error = err
    print(err.get("Error", {}).get("Code"))
    return f"Un error invocando {LAMBDA_AGENT_TEXT}
```

#### Image Message:

![Digrama parte 1](/imagenes/image_step.jpg)

[process_stream](/private-assistant/lambdas/code/process_stream/lambda_function.py) Lambda Function sends the text of the message to a Lambda Function named [agent_image_v3](https://github.com/build-on-aws/building-gen-ai-whatsapp-assistant-with-amazon-bedrock-and-python/blob/main/private-assistant/lambdas/code/agent_image_v3/lambda_function.py). 



### 3- LLM Processing:

![Digrama parte 1](/imagenes/3_step.jpg)

The agent receives the text and performs the following:
1. Queries the Amazon DynamoDB table called `user_metadata` to see if the `session` has expired. If it is active, it recovers the `SessionID`, necessary for the next step, if it expires it creates a new session timer. In Lambda Function named [langchain_agent_text](/private-assistant/lambdas/code/langchain_agent_text/lambda_function.py)the chat history is managed with the Lanchain memory class, in the Lambdas Functions [agent_text_v3](https://github.com/build-on-aws/building-gen-ai-whatsapp-assistant-with-amazon-bedrock-and-python/blob/main/private-assistant/lambdas/code/agent_text_v3/lambda_function.py) and [agent_image_v3](https://github.com/build-on-aws/building-gen-ai-whatsapp-assistant-with-amazon-bedrock-and-python/blob/main/private-assistant/lambdas/code/agent_image_v3/lambda_function.py) it is solved with a Json array that is fed with the history of the conversation.
2. Queries the Amazon DynamoDB table called session Table to see if there is any previous conversation history.
3. Consult the LLM through Amazon Bedrock using the following prompt:

```
The following is a friendly conversation between a human and an AI. 
    The AI is talkative and provides lots of specific details from its context. 
    If the AI does not know the answer to a question, it truthfully says it does not know.
    Always reply in the original user language.
```
4. Send the response to WhatsApp through `whatsapp_out` the Lambda Function.

> 💡 The phrase **"Always reply in the original user language"** ensures that it always responds in the original language and the multilingual capacity is provided by [Anthropic Claude](https://aws.amazon.com/bedrock/claude/), which is the model used in this application.


## Let's build!

### Step 0: Activate WhatsApp account Facebook Developers

1- [Get Started with the New WhatsApp Business Platform](https://www.youtube.com/watch?v=CEt_KMMv3V8&list=PLX_K_BlBdZKi4GOFmJ9_67og7pMzm2vXH&index=2&t=17s&pp=gAQBiAQB)

2- [How To Generate a Permanent Access Token — WhatsApp API](https://www.youtube.com/watch?v=LmoiCMJJ6S4&list=PLX_K_BlBdZKi4GOFmJ9_67og7pMzm2vXH&index=1&t=158s&pp=gAQBiAQB)

3- [Get started with the Messenger API for Instagram](https://www.youtube.com/watch?v=Pi2KxYeGMXo&list=PLX_K_BlBdZKi4GOFmJ9_67og7pMzm2vXH&index=5&t=376s&pp=gAQBiAQB)


### Step 1:  APP Set Up 

✅ **Clone the repo**

```
git clone https://github.com/build-on-aws/building-gen-ai-whatsapp-assistant-with-amazon-bedrock-and-python
```

✅ **Go to**: 

```
cd private-assistant
```

### Step 2: Deploy architecture with CDK.

In [private_assistant_stack.py](/private-assistant/private_assistant/private_assistant_stack.py) edit this line with the whatsapp Facebook Developer app number: 

`
DISPLAY_PHONE_NUMBER = 'YOU-NUMBER'
`

This agent manages conversation memory, and you must set the session time [here](/private-assistant/lambdas/code/langchain_agent_text/lambda_function.py) in this line:

`
if diferencia > 240:  #session time in seg
`

> **Tip:** [Kenton Blacutt](https://github.com/KBB99), an AWS Associate Cloud App Developer, collaborated with Langchain, creating the [Amazon Dynamodb based memory class](https://github.com/langchain-ai/langchain/pull/1058) that allows us to store the history of a langchain agent in an [Amazon DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html?sc_channel=el&sc_campaign=genaiwave&sc_content=working-with-your-live-data-using-langchain&sc_geo=mult&sc_country=mult&sc_outcome=acq).

**To use the Lambda Function** [langchain_agent_text](https://github.com/build-on-aws/building-gen-ai-whatsapp-assistant-with-amazon-bedrock-and-python/blob/main/private-assistant/lambdas/code/langchain_agent_text/lambda_function.py): change the `LAMBDA_AGENT_TEXT` environment variable in Lambda Function [process_stream](https://github.com/build-on-aws/building-gen-ai-whatsapp-assistant-with-amazon-bedrock-and-python/tree/main/private-assistant/lambdas/code/process_stream) in [private_assistant_stack](https://github.com/build-on-aws/building-gen-ai-whatsapp-assistant-with-amazon-bedrock-and-python/blob/main/private-assistant/private_assistant/private_assistant_stack.py): 

```python
#Line 77
Fn.process_stream.add_environment(key='ENV_LAMBDA_AGENT_TEXT', value=Fn.langchain_agent_text.function_name)
```

- Configure the [AWS Command Line Interface](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

- Deploy architecture with CDK [Follow steps:](/private-assistant/README.md)

![Digrama parte 1](/imagenes/arquitectura.jpg)

✅ **Create The Virtual Environment**: by following the steps in the [README](/private-assistant/README.md)

```
python3 -m venv .venv
```

```
source .venv/bin/activate
```
for windows: 

```
.venv\Scripts\activate.bat
```

✅ **Install The Requirements**:

```
pip install -r requirements.txt
```

✅ **Synthesize The Cloudformation Template With The Following Command**:

```
cdk synth
```

✅🚀 **The Deployment**:

```
cdk deploy
```

![Deployment Time](/imagenes/deployment_time.jpg)

### Step 3: WhatsApp Configuration

Edit WhatsApp configuration values in Facebook Developer in [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) [console](https://console.aws.amazon.com/secretsmanager/).

![Digrama parte 1](/imagenes/secret.png)

> ✅ The **verification token** is any value, but it must be the same in step 3 and 4.

### Step 4: Webhook Configuration

1. Go to [Amazon API Gateway Console](https://console.aws.amazon.com/apigateway)
2. Click on `myapi`.
3. Go to **Stages** -> **prod** -> **/cloudapi** -> **GET**, and copy **Invoke URL**. 

![Invoke Url](/imagenes/invoke_url.jpg)

4. Configure Webhook in the Facebook developer application. 
    - Set **Invoke URL**.
    - Set **verification token**.


![Digrama parte 1](/imagenes/webhook.png)

----


## Enjoy the app!:

✅  Chat and ask follow-up questions. Test your multi-language skills.

![Digrama parte 1](/imagenes/memory_2.gif)

✅ Send and transcribe voice notes. Test the app's capabilities for transcribing multiple languages.

![Digrama parte 1](/imagenes/voice-note-2.gif)

✅ Send photos and test the app's capabilities to describe and identify what's in the images. Play with prompts

![Digrama parte 1](/imagenes/image_claude_v2.gif)

## 🚀 Keep testing the app, play with the prompt [langchain_agent_text](/private-assistant/lambdas/code/langchain_agent_text/lambda_function.py) Amazon Lambda function and adjust it to your need. 


## Clean the house!:

If you finish testing and want to clean the application, you just have to follow these two steps:

1. Delete the files from the Amazon S3 bucket created in the deployment. 
2. Run this command in your terminal:

```
cdk destroy
```


## Conclusion: 

In this tutorial, you deployed a serverless WhatsApp application that allows users to interact with an LLM through Amazon Bedrock. This architecture uses API Gateway as a connection between WhatsApp and the application. Amazon Lambda functions process code to handle conversations. Amazon DynamoDB tables manage and store message information, session details, and conversation history.

You now have the essential code to improve the application. One option moving forward is to incorporate [Retrieval-Augmented Generation (RAG)](https://aws.amazon.com/what-is/retrieval-augmented-generation/?nc1=h_ls) to generate more sophisticated responses depending on the context.

To handle customer service scenarios, the application could connect to [Amazon Connect](https://aws.amazon.com/connect/features/) and transfer calls to an agent if the LLM cannot resolve an issue.

With further development, this serverless architecture demonstrates how conversational AI can power engaging and useful chat experiences on popular messaging platforms.

## 🚨 Did you like this blog? 👩🏻‍💻 Do you have comments?🎤 tell me every thing[here](https://www.pulse.aws/survey/6V3IYE9H)

## 🚀 Some links for you to continue learning and building:

- [Get started with Amazon Connect](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-connect-get-started.html)
- [Elevating Customer Support With a Whatsapp Assistant.](https://community.aws/content/2bgPgouKvLhinu8bcE4LZQ1nnwv/elevating-customer-support-with-a-whatsapp-travel-assistant-from-las-vegas-mexico-to-las-vegas-nevada-a-re-invent-2023-history)
- [RAG with history memory agents using Amazon Bedrock, Amazon Kendra, Amazon Lambda Function, and Amazon DynamoDB](https://github.com/build-on-aws/qa-agent-with-bedrock-kendra-and-history-memory)
- [How To Choose Your LLM](https://community.aws/posts/how-to-choose-your-llm)
- [Working With Your Live Data Using LangChain](https://community.aws/posts/working-with-your-live-data-using-langchain)



----

## 🇻🇪🇨🇱 ¡Gracias!

---

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
