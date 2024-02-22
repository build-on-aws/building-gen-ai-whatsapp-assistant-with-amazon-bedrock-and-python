
from langchain import LLMMathChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.agents import load_tools, initialize_agent, AgentType,Tool


def match_function(model_id,bedrock_client):
    math_chain_llm = Bedrock(model_id=model_id,model_kwargs={"temperature":0,"stop_sequences" : ["```output"]},client=bedrock_client)
    llm_math_chain = LLMMathChain(llm=math_chain_llm, verbose=True)

    llm_math_chain.llm_chain.prompt.template = """Human: Given a question with a math problem, provide only a single line mathematical expression that solves the problem in the following format. Don't solve the expression only create a parsable expression.
    ```text
    ${{single line mathematical expression that solves the problem}}
    ```

    Assistant:
    Here is an example response with a single line mathematical expression for solving a math problem:
    ```text
    37593**(1/5)
    ```

    Human: {question}
    Assistant:"""
    return Tool.from_function(
        func=llm_math_chain.run,
        name="Calculator",
        description="Useful for when you need to answer questions about math.",
    )

def memory_dynamodb(id,table_name_session):
    message_history = DynamoDBChatMessageHistory(table_name=table_name_session, session_id=id)
    memory = ConversationBufferMemory(
        memory_key="chat_history", chat_memory=message_history, return_messages=True,ai_prefix="A",human_prefix="H"
    )
    return memory

def langchain_agent(memory,tools,llm):
    zero_shot_agent=initialize_agent(
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    tools=tools,
    #verbose=True,
    max_iteration=1,
    #return_intermediate_steps=True,
    #handle_parsing_errors=True,
    memory=memory
)
    return zero_shot_agent