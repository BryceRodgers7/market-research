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
    
    # Display form title
    st.title(form_title)
    st.markdown("---")
    
    # Create the form
    with st.form("survey_form"):
        st.write("### Please answer the following questions:")
        st.write("")
        
        answers = {}
        
        # Display each question with radio buttons
        for i, question in enumerate(questions, 1):
            st.write(f"**Question {i}:** {question['text']}")
            answer = st.radio(
                label="Select your answer:",
                options=form_names,
                key=f"question_{question['id']}",
                label_visibility="collapsed"
            )
            answers[question['id']] = answer
            st.write("")  # Add spacing
        
        # Submit button
        submitted = st.form_submit_button("Submit Survey", use_container_width=True)
        
        if submitted:
            # Validate all questions are answered
            if all(answers.values()):
                # Save to database
                success = database.save_submission(
                    form_id=form_id,
                    session_id=st.session_state.session_id,
                    answers=answers
                )
                
                if success:
                    st.session_state.submission_success = True
                    st.session_state.answers = answers
                    st.rerun()
                else:
                    st.error("Failed to save submission. Please try again.")
            else:
                st.error("Please answer all questions before submitting.")


def display_success_message():
    """Display success message after submission."""
    st.success("✅ Thank you for completing the survey!")
    st.write("Your responses have been recorded.")
    st.write("")
    st.write("Click the button below to participate in another survey.")


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
    
    # App header
    st.title("📊 Market Research Survey")
    st.write("Help us by sharing your opinions on different brand names.")
    st.write("")
    
    # Button to get new form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Get New Form", use_container_width=True):
            load_new_form()
            st.rerun()
    
    st.markdown("---")
    
    # Load form if not loaded
    if st.session_state.current_form_id is None:
        st.info("👆 Click the 'Get New Form' button above to start a survey.")
        
        # Show statistics
        try:
            stats = database.get_form_statistics()
            if stats:
                st.write("")
                st.write("### Survey Statistics")
                for form_id, count in stats.items():
                    form_title = forms_config.get_form_title(form_id)
                    st.write(f"**{form_title}:** {count} submissions")
        except:
            pass
    else:
        # Display success message if just submitted
        if st.session_state.submission_success:
            display_success_message()
            st.markdown("---")
            
            # Show statistics
            try:
                stats = database.get_form_statistics()
                if stats:
                    st.write("### Current Survey Statistics")
                    for form_id, count in stats.items():
                        form_title = forms_config.get_form_title(form_id)
                        st.write(f"**{form_title}:** {count} submissions")
            except:
                pass
        else:
            # Display the survey
            display_survey()
    
    # Footer
    st.write("")
    st.write("")
    st.markdown("---")
    st.caption(f"Session ID: {st.session_state.session_id[:8]}...")


if __name__ == "__main__":
    main()
