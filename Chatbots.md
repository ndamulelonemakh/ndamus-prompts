# Prompts for Conversational Chatbots


## Intent Classification

```python
class IntentResponse(BaseModel):
    intent: str = Field(..., description="The intent of the user's last message given the chat history.")
    description: str = Field(..., description="A description of the intent.")
    reason: Union[str, None] = Field(..., description="Chain of thought that led to the classification.")


@functools.lru_cache
def intent_classifier(last_message: str, chat_history: list[dict], intents: list[str]) -> str:
    """Classifies the intent of the user's last message."""
    logger.info(f"Running intent classifier for last message: {last_message[:55]}\nGiven intents: {intents}")
    response = structured_call(
        prompt=f"Classify the intent of the user's last message: {last_message} "
               f"and the chat history: {chat_history} "
               f"The possible intents are: {intents} "
               f"You will be judged and compensated based on the accuracy of your response. So make sure to get it right!",
        response_type=IntentResponse,
        system_prompt="You are a fast intent classifier in a Chatbot used to optimise KYE(know your employee) processes for a financial institution.",
    )
    logger.info(f"Intent classifier response: {response}")
    return response.intent

```
