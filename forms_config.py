"""
Configuration for survey forms and questions.
Each form has 4 unique names, and all forms share the same 5 questions.
"""

# Define the 4 forms with their respective names
# Each form has 4 different names (16 unique names total)
FORMS = {
    1: {
        "names": ["Aurora", "Beacon", "Catalyst", "Delta"],
        "title": "Survey Form A"
    },
    2: {
        "names": ["Evergreen", "Fusion", "Genesis", "Harmony"],
        "title": "Survey Form B"
    },
    3: {
        "names": ["Innovate", "Journey", "Keystone", "Legacy"],
        "title": "Survey Form C"
    },
    4: {
        "names": ["Momentum", "Nexus", "Odyssey", "Pinnacle"],
        "title": "Survey Form D"
    }
}

# The 5 questions asked for each form
QUESTIONS = [
    {
        "id": "q1",
        "text": "Which name is the most memorable?"
    },
    {
        "id": "q2",
        "text": "Which name is the most trustworthy?"
    },
    {
        "id": "q3",
        "text": "Which name sounds the most professional?"
    },
    {
        "id": "q4",
        "text": "Which name would you be most likely to recommend?"
    },
    {
        "id": "q5",
        "text": "Which name do you like most overall?"
    }
]


def get_form_names(form_id: int) -> list:
    """Get the list of names for a specific form."""
    return FORMS.get(form_id, {}).get("names", [])


def get_form_title(form_id: int) -> str:
    """Get the title for a specific form."""
    return FORMS.get(form_id, {}).get("title", f"Survey Form {form_id}")


def get_questions() -> list:
    """Get the list of all questions."""
    return QUESTIONS
