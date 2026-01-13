"""
Configuration for survey forms and questions.
Each form has 4 unique names, and all forms share the same 5 questions.
"""

FORMS = {
    1: {
        "names": ["Philanthrifind","Give-io","Donathropy","Kinderfully"],
        "title": "Survey Form A"
    },
    2: {
        "names": ["Philanthrifound","Causenex","Givanthropy","Tomatchin"],
        "title": "Survey Form B"
    },
    3: {
        "names": ["Philanthri","Give Connects","Donanthropy","Humanitable"],
        "title": "Survey Form C"
    },
    4: {
        "names": ["Givio Gives","Philanthrifound","Givanthropy","Humanitable"],
        "title": "Survey Form D"
    },
    5: {
        "names": ["Give Connects","Philanthrifind","Give-io","Tomatchin"],
        "title": "Survey Form E"
    },
    6: {
        "names": ["Philanthri","Givio Gives","Kinderfully","Causenex"],
        "title": "Survey Form F"
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
        "text": "Which name are you most curious to learn more about?"
    },
    {
        "id": "q4",
        "text": "Which name are you most likely to try or sign up for?"
    },
    {
        "id": "q5",
        "text": "Overall, which name do you like best?"
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
