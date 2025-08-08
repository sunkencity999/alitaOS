"""Email drafting tool for composing personalized messages."""

import chainlit as cl
from pydantic import BaseModel, Field
from utils.ai_models import get_llm
from utils.common import logger


class EmailDraft(BaseModel):
    """Email draft generated from context."""

    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")


draft_email_def = {
    "name": "draft_email",
    "description": "Drafts a personalized email based on recipient and context.",
    "parameters": {
        "type": "object",
        "properties": {
            "to": {
                "type": "string",
                "description": "Name or title of the recipient (e.g., 'John Smith', 'HR Manager')",
            },
            "context": {
                "type": "string",
                "description": "Description of what the email should be about (e.g., 'Thank them for their recent purchase and offer a 10% discount on their next order')",
            },
        },
        "required": ["to", "context"],
    },
}


async def draft_email_handler(to: str, context: str):
    """Drafts a personalized email using recipient info and context."""
    try:
        logger.info(f"📧 Drafting email to: {to}")
        logger.info(f"Context: {context}")

        llm = get_llm("email_generation")
        structured_llm = llm.with_structured_output(EmailDraft)

        system_template = """
        You are an expert email composer. Draft a professional and engaging email based on the recipient and context provided.
        
        # Recipient
        {to}
        
        # Purpose/Context
        {context}
        
        # Guidelines
        1. Keep the tone professional but friendly
        2. Be concise and clear
        3. Include a clear call-to-action when appropriate
        4. Personalize the content for the recipient
        5. Make sure the subject line is attention-grabbing and relevant
        6. Use appropriate greetings and closings
        
        Return both the subject and body of the email.
        """

        chain_input = {"to": to, "context": context}

        email_draft = structured_llm.invoke(system_template.format(**chain_input))

        # Send the draft email as a message
        await cl.Message(
            content=f"📧 **Draft Email**\n\n**To:** {to}\n**Subject:** {email_draft.subject}\n\n{email_draft.body}"
        ).send()

        return {
            "subject": email_draft.subject,
            "body": email_draft.body,
        }

    except Exception as e:
        error_message = f"Error drafting email: {str(e)}"
        logger.error(f"❌ {error_message}")
        await cl.Message(content=error_message, type="error").send()
        return {"error": error_message}


draft_email = (draft_email_def, draft_email_handler)
