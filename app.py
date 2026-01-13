import streamlit as st
import uuid
from datetime import datetime
import database
import forms_config

# Page configuration
st.set_page_config(
    page_title="Market Research Survey",
    page_icon="📊",
    layout="centered"
)


def init_session_state():
    """Initialize session state variables."""
    # Generate unique session_id for user tracking
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    # Track current form
    if 'current_form_id' not in st.session_state:
        st.session_state.current_form_id = None
    
    # Track if submission was successful
    if 'submission_success' not in st.session_state:
        st.session_state.submission_success = False
    
    # Track answers
    if 'answers' not in st.session_state:
        st.session_state.answers = {}


def load_new_form():
    """Load a new form (the one with least submissions)."""
    try:
        form_id = database.get_least_submitted_form()
        st.session_state.current_form_id = form_id
        st.session_state.submission_success = False
        st.session_state.answers = {}
        
        # Clear all previous question answers (for radio buttons)
        questions = forms_config.get_questions()
        for question in questions:
            answer_key = f"question_{question['id']}"
            if answer_key in st.session_state:
                del st.session_state[answer_key]
        
        return True
    except Exception as e:
        st.error(f"Error loading form: {e}")
        return False


def display_survey():
    """Display the survey form."""
    form_id = st.session_state.current_form_id
    
    if form_id is None:
        st.error("No form loaded. Please click 'Get New Form' button.")
        return
    
    # Get form data
    form_names = forms_config.get_form_names(form_id)
    form_title = forms_config.get_form_title(form_id)
    questions = forms_config.get_questions()
    
    # Create the form
    with st.form("survey_form"):
        st.write("### Please answer the following questions:")
        st.write("")
        
        answers = {}
        
        # Add CSS to style radio buttons in 2x2 grid
        st.markdown("""
            <style>
            div[data-testid="stRadio"] > div {
                display: grid !important;
                grid-template-columns: 1fr 1fr !important;
                gap: 0.5rem !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Display each question with radio buttons in a 2x2 grid
        for i, question in enumerate(questions, 1):
            st.write(f"**Question {i}:** {question['text']}")
            
            # Initialize answer in session state if not present
            answer_key = f"question_{question['id']}"
            
            # Radio buttons will display in 2x2 grid thanks to CSS
            answer = st.radio(
                label=f"Select your choice:",
                options=form_names,
                key=answer_key,
                label_visibility="collapsed",
                index=None  # No default selection
            )
            
            # Store the answer
            answers[question['id']] = answer
            st.write("")  # Add spacing
        
        # Optional open-ended questions
        st.write("---")
        st.write("### Optional Questions")
        st.write("*(You may skip these if you prefer)*")
        st.write("")
        
        st.write("**Which is your top choice and what stood out to you about it?**")
        top_choice = st.text_area(
            label="Top choice response:",
            max_chars=2000,
            key="top_choice",
            label_visibility="collapsed",
            placeholder="Optional: Share your thoughts here..."
        )
        st.write("")
        
        st.write("**Were there any names that felt confusing, untrustworthy, or off-putting? If so, which and why?**")
        bottom_choice = st.text_area(
            label="Bottom choice response:",
            max_chars=2000,
            key="bottom_choice",
            label_visibility="collapsed",
            placeholder="Optional: Share your thoughts here..."
        )
        st.write("")
        
        # Submit button
        submitted = st.form_submit_button("Submit Survey", use_container_width=True)
        
        # Display form title
        st.write("Note: this is " + form_title + ". This note will be removed when deploying to production.")

        if submitted:
            # Validate all questions are answered
            unanswered = [i+1 for i, (q_id, answer) in enumerate(answers.items()) if not answer]
            
            if not unanswered:
                # All questions answered - save to database
                success = database.save_submission(
                    form_id=form_id,
                    session_id=st.session_state.session_id,
                    answers=answers,
                    top_choice=top_choice if top_choice.strip() else None,
                    bottom_choice=bottom_choice if bottom_choice.strip() else None
                )
                
                if success:
                    st.session_state.submission_success = True
                    st.session_state.answers = answers
                    st.rerun()
                else:
                    st.error("Failed to save submission. Please try again.")
            else:
                # Show which questions need answers
                if len(unanswered) == 1:
                    st.error(f"⚠️ Please answer Question {unanswered[0]} before submitting.")
                else:
                    st.error(f"⚠️ Please answer all questions before submitting. Missing: Questions {', '.join(map(str, unanswered))}")


def display_success_message():
    """Display success message after submission."""
    st.success("✅ Thank you for completing the survey!")
    st.write("Your responses have been recorded.")
    st.write("")
    st.write("Click the 'Begin' button again to sample more potential names.")


def display_results_page():
    """Display the results/statistics page."""
    st.title("📊 Survey Results")
    st.write("")
    
    # Show form statistics
    try:
        stats = database.get_form_statistics()
        if stats:
            st.write("### Survey Statistics")
            for form_id, count in stats.items():
                form_title = forms_config.get_form_title(form_id)
                st.write(f"**{form_title}:** {count} submissions")
            st.write("")
            st.markdown("---")
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
    
    # Show question rankings
    try:
        rankings = database.get_question_rankings()
        questions = forms_config.get_questions()
        
        st.write("### Question Rankings")
        st.write("")
        
        for i, question in enumerate(questions, 1):
            question_id = question['id']
            st.write(f"**Question {i}:** {question['text']}")
            
            if question_id in rankings:
                data = rankings[question_id]
                
                # Display top 3
                st.write("**Top 3 Names:**")
                if data["top_3"]:
                    for j, item in enumerate(data["top_3"], 1):
                        st.write(f"{j}. {item['name']} - {item['count']} votes")
                else:
                    st.write("No data yet")
                
                st.write("")
                
                # Display bottom 3
                st.write("**Bottom 3 Names:**")
                if data["bottom_3"]:
                    for j, item in enumerate(data["bottom_3"], 1):
                        st.write(f"{j}. {item['name']} - {item['count']} votes")
                else:
                    st.write("No data yet")
                
                st.write("")
                st.markdown("---")
    except Exception as e:
        st.error(f"Error loading rankings: {e}")


def main():
    """Main application function."""
    # Initialize database on first run
    try:
        database.init_database()
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        st.write("Please ensure DATABASE_URL environment variable is set correctly.")
        st.stop()
    
    # Initialize session state
    init_session_state()
    
    # Check if accessing results page
    query_params = st.query_params
    if "page" in query_params and query_params["page"] == "resultsz":
        display_results_page()
        return
    
    # App header
    st.title("📊 Research Survey")
    st.write("This app is a matching platform designed to help people and companies discover nonprofits that align with their values and interests. We are looking for a name that appeals to both individual users and corporations, reflecting the app’s mission to connect them with meaningful causes. Please answer the following questions to help us find a name that captures these goals.")
    st.write("")
    
    # Button to get new form
    col1, col2, col3 = st.columns([1, 2, 1])
    # with col2:
    #     if st.button("📜 Begin", use_container_width=True):
    #         load_new_form()
    #         st.rerun()
    
    st.write("")
    
    # Load form if not loaded
    if st.session_state.current_form_id is None:
        with col2:
            if st.button("📜 Begin", use_container_width=True):
                load_new_form()
                st.rerun()
        st.info("👆 Click the 'Begin' button above to start the survey.")
    else:
        # Display success message if just submitted
        if st.session_state.submission_success:
            display_success_message()
            st.markdown("---")
            with col2:
                if st.button("📜 Begin", use_container_width=True):
                    load_new_form()
                    st.rerun()
        else:
            # st.markdown("---")
            # Display the survey
            display_survey()
    
    # Footer
    st.write("")
    st.write("")
    st.caption(f"Session ID: {st.session_state.session_id[:8]}...")


if __name__ == "__main__":
    main()
