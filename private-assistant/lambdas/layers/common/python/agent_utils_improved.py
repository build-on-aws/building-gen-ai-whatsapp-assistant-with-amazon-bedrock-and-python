# Improved implementation of agent utilities
# The original implementation had several areas for improvement:
# 1. Limited error handling
# 2. Basic memory management
# 3. No type hints
# 4. Limited configuration options
# 5. Hardcoded prompt templates
# 6. No proper logging

import logging
from typing import List, Optional, Any, Dict
from dataclasses import dataclass

from langchain import LLMMathChain
from langchain.llms.bedrock import Bedrock
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import DynamoDBChatMessageHistory
from langchain.agents import load_tools, initialize_agent, AgentType, Tool
from langchain.schema import BaseMemory
from langchain.callbacks.base import BaseCallbackHandler

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dataclass
class ModelConfig:
    """Configuration for the LLM model."""
    model_id: str
    temperature: float = 0.0
    top_p: float = 0.9
    max_tokens: int = 2000
    stop_sequences: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to model kwargs dictionary."""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens_to_sample": self.max_tokens,
            "stop_sequences": self.stop_sequences
        }

class CustomCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for logging and monitoring."""
    
    def on_llm_start(self, *args, **kwargs):
        logger.info("Starting LLM call")
        
    def on_llm_end(self, *args, **kwargs):
        logger.info("Completed LLM call")
        
    def on_llm_error(self, error: Exception, *args, **kwargs):
        logger.error(f"LLM error occurred: {str(error)}")

class AgentToolFactory:
    """Factory class for creating and managing agent tools."""
    
    @staticmethod
    def create_math_tool(
        model_config: ModelConfig,
        bedrock_client: Any,
        custom_prompt: Optional[str] = None
    ) -> Tool:
        """Create an improved math tool with better error handling and customization."""
        try:
            math_chain_llm = Bedrock(
                model_id=model_config.model_id,
                model_kwargs={"temperature": 0, "stop_sequences": ["```output"]},
                client=bedrock_client,
                callbacks=[CustomCallbackHandler()]
            )
            
            llm_math_chain = LLMMathChain(llm=math_chain_llm, verbose=True)
            
            # Use custom prompt if provided, otherwise use improved default prompt
            llm_math_chain.llm_chain.prompt.template = custom_prompt or """Human: Given a mathematical problem, provide a clear and precise solution.
            Please format your response as:
            ```text
            ${{mathematical expression}}
            ```
            
            Guidelines:
            - Use standard mathematical notation
            - Keep expressions concise and clear
            - Handle edge cases appropriately
            
            Human: {question}
            Assistant:"""
            
            return Tool.from_function(
                func=llm_math_chain.run,
                name="Enhanced Calculator",
                description="Precise mathematical calculations with improved error handling and notation.",
            )
            
        except Exception as e:
            logger.error(f"Failed to create math tool: {str(e)}")
            raise

class MemoryManager:
    """Enhanced memory management for conversation history."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        
    def create_memory(
        self,
        session_id: str,
        memory_key: str = "chat_history",
        ai_prefix: str = "A",
        human_prefix: str = "H"
    ) -> BaseMemory:
        """Create an improved memory instance with better configuration options."""
        try:
            message_history = DynamoDBChatMessageHistory(
                table_name=self.table_name,
                session_id=session_id
            )
            
            return ConversationBufferMemory(
                memory_key=memory_key,
                chat_memory=message_history,
                return_messages=True,
                ai_prefix=ai_prefix,
                human_prefix=human_prefix,
            )
            
        except Exception as e:
            logger.error(f"Failed to create memory instance: {str(e)}")
            raise

def create_langchain_agent(
    memory: BaseMemory,
    tools: List[Tool],
    llm: Any,
    agent_type: AgentType = AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose: bool = True
):
    """Create an improved LangChain agent with better configuration and error handling."""
    try:
        return initialize_agent(
            tools=tools,
            llm=llm,
            agent=agent_type,
            memory=memory,
            verbose=verbose,
            handle_parsing_errors=True,
            callbacks=[CustomCallbackHandler()]
        )
    except Exception as e:
        logger.error(f"Failed to create LangChain agent: {str(e)}")
        raise

# Example usage:
"""
# Create model configuration
model_config = ModelConfig(
    model_id="anthropic.claude-v2",
    temperature=0.0,
    top_p=0.9,
    max_tokens=2000
)

# Initialize components
memory_manager = MemoryManager(table_name="conversation_history")
memory = memory_manager.create_memory(session_id="user123")

# Create tools
math_tool = AgentToolFactory.create_math_tool(model_config, bedrock_client)
tools = [math_tool]

# Create agent
agent = create_langchain_agent(memory, tools, llm)
"""