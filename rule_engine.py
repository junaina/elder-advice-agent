from typing import Optional

def rule_engine_reply(user_text: str) -> Optional[str]:
    """
    Small rule-based engine that returns a canned response for a few
    common elder-care intents. Returns None if no rule matches.
    """
    text = user_text.lower()

    if "remind" in text and "medication" in text:
        return (
            "I can help you plan safe times to take your medication, but I can't "
            "change your prescription. Has a doctor given you instructions "
            "for when to take it?"
        )

    if "feeling lonely" in text or "feel lonely" in text:
        return (
            "I'm sorry you're feeling lonely. We can talk about ways to stay "
            "connected with friends, family, or local groups. Would you like "
            "some ideas?"
        )

    if "exercise" in text and ("safe" in text or "okay" in text):
        return (
            "Gentle activities such as walking or stretching are often helpful, "
            "but it depends on your health. It's best to ask your doctor what "
            "level of activity is safe for you."
        )

    return None
