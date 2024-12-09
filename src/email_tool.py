import re
from dotenv import load_dotenv
import os
from typing import List, Annotated
from typing_extensions import TypedDict
from langchain_core.tools import BaseTool
from langchain_community.tools.office365.utils import authenticate
from langchain_community.tools.office365.send_message import O365SendMessage
from langchain_core.tools import tool
from O365 import Account, FileSystemTokenBackend
from pydantic import BaseModel, Field, ConfigDict
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import O365Toolkit

load_dotenv()

llm = ChatOpenAI(model_name="gpt-3.5-turbo")

# Set CLIENT_ID and CLIENT_SECRET as environment variables
os.environ["CLIENT_ID"] = os.getenv('CLIENT_ID')  # Ensure userdata is defined earlier
os.environ["CLIENT_SECRET"] = os.getenv('CLIENT_SECRET')

# Define credentials using environment variables
credentials = (os.environ["CLIENT_ID"], os.environ["CLIENT_SECRET"])
class CustomO365SendMessage(O365SendMessage):
    account: Account = Field(default_factory=authenticate)
CustomO365SendMessage.model_rebuild()

class CustomO365Toolkit(O365Toolkit):
    """Toolkit for interacting with Office 365 services using custom settings."""

    account: Account = Field(default_factory=authenticate)

    def get_tools(self) -> List[BaseTool]:
        """Return instances of the Office 365 tools, ensuring each is properly initialized."""
        # Initialize each tool with the authenticated account
        tools = [
            CustomO365SendMessage()
        ]
        return tools

CustomO365Toolkit.model_rebuild()
toolkit = CustomO365Toolkit()

from langchain.agents import AgentType, initialize_agent
agent = initialize_agent(
    tools=toolkit.get_tools(),
    llm=llm,
    verbose=False,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
)

@tool
def email_tool(
    email: Annotated[str, "The user's email address"],
    apartment_listings: Annotated[list, "The data needed sent to the user"]
):
    """Use this to send an email."""
    emailInfo = llm.invoke(f"""Send an email to the email address: {email}.
                           The subject should be: Your Interested Apartments.
                           You should describe each apartment in the data {apartment_listings} in the email body using human language.
                           The columns of data are: 'address', 'bedrooms', 'bathrooms', 'square_feet', 'price_display'.
                           For each row, you should start with 'Apartment' and its index, different columns should be seperated by comma.
                           For bedrooms and bathrooms info, it should be integer.
                           The body should start with 'Hi, below is your interested apartment listings.'
                           The output format should be json, the keys are: recipient_email, subject, body.
                           """).content

    try:
        agent.run(emailInfo)
        print(f"Email sent successfully! the email information is{emailInfo}")
        return f"Email sent successfully! the email information is{emailInfo}"
    except Exception as e:
        # If there's an error, return a failure message
        return f"Failed to send email. Error: {repr(e)}"
    
def validate_email(email):
    # Regular expression pattern for validating an email address
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    return False

def send_email(st, email, apartment_listings):
    print("the listings is: ", apartment_listings)
    email_tool.invoke({'email': email, 'apartment_listings':apartment_listings})
    st.success(f"Email sent successfully!")