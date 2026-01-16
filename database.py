import os
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Optional
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor

# Database connection pool
_pool: Optional[SimpleConnectionPool] = None




def get_database_url() -> str:
    """Get database URL from environment variable."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    return database_url


def init_pool():
    """Initialize the connection pool."""
    global _pool
    if _pool is None:
        database_url = get_database_url()
        _pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=database_url
        )


@contextmanager
def get_connection():
    """Context manager for database connections."""
    init_pool()
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)

def init_database():
    """Initialize database connection to check for problems"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            if result:
                print("Database connection successful")
            else:
                print("Database connection failed")


def init_database_tables():
    """Initialize database tables and form_counters."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create form_counters table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS form_counters (
                    form_id INTEGER PRIMARY KEY,
                    submission_count INTEGER NOT NULL DEFAULT 0,
                    last_assigned TIMESTAMP
                )
            """)
            
            # Create submissions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    form_id INTEGER NOT NULL,
                    session_id VARCHAR(255) NOT NULL,
                    submission_datetime TIMESTAMP NOT NULL DEFAULT NOW(),
                    question_1_answer VARCHAR(255) NOT NULL,
                    question_2_answer VARCHAR(255) NOT NULL,
                    question_3_answer VARCHAR(255) NOT NULL,
                    question_4_answer VARCHAR(255) NOT NULL,
                    question_5_answer VARCHAR(255) NOT NULL,
                    top_choice TEXT,
                    bottom_choice TEXT
                )
            """)
            
            # Initialize form_counters if empty
            cur.execute("SELECT COUNT(*) FROM form_counters")
            count = cur.fetchone()[0]
            
            if count == 0:
                # Insert initial form counters (1-6)
                for form_id in range(1, 7):
                    cur.execute("""
                        INSERT INTO form_counters (form_id, submission_count, last_assigned)
                        VALUES (%s, 0, NULL)
                    """, (form_id,))
            
            # Migration: Add new optional columns if they don't exist
            cur.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='submissions' AND column_name='top_choice'
                    ) THEN
                        ALTER TABLE submissions ADD COLUMN top_choice TEXT;
                    END IF;
                    
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='submissions' AND column_name='bottom_choice'
                    ) THEN
                        ALTER TABLE submissions ADD COLUMN bottom_choice TEXT;
                    END IF;
                END $$;
            """)
            
            conn.commit()


def get_least_submitted_form() -> int:
    """
    Get the form_id with the least submissions.
    Returns form_id (1-6).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            # First check what's in the table
            cur.execute("SELECT form_id, submission_count FROM form_counters ORDER BY form_id")
            all_forms = cur.fetchall()
            print(f"Current form_counters state: {all_forms}")
            
            # Find form with minimum submission count, break ties by oldest last_assigned
            cur.execute("""
                SELECT form_id 
                FROM form_counters 
                ORDER BY submission_count ASC, 
                         COALESCE(last_assigned, '1970-01-01'::timestamp) ASC
                LIMIT 1
            """)
            result = cur.fetchone()
            
            if result:
                form_id = result[0]
                print(f"Assigning form {form_id} (least submitted)")
                # Update last_assigned timestamp
                cur.execute("""
                    UPDATE form_counters 
                    SET last_assigned = NOW() 
                    WHERE form_id = %s
                """, (form_id,))
                conn.commit()
                return form_id
            else:
                # If no forms exist, initialize them now
                print("WARNING: No forms found in form_counters, initializing now...")
                try:
                    for form_id in range(1, 7):
                        cur.execute("""
                            INSERT INTO form_counters (form_id, submission_count, last_assigned)
                            VALUES (%s, 0, NULL)
                            ON CONFLICT (form_id) DO NOTHING
                        """, (form_id,))
                    conn.commit()
                    print("Initialized form_counters with forms 1-6")
                    return 1  # Return form 1 as default
                except Exception as e:
                    print(f"Error initializing form_counters: {e}")
                    return 1


def save_submission(
    form_id: int,
    session_id: str,
    answers: Dict[str, str],
    top_choice: Optional[str] = None,
    bottom_choice: Optional[str] = None
) -> bool:
    """
    Save a submission to the database and increment form counter.
    
    Args:
        form_id: The form ID (1-6)
        session_id: User's session ID
        answers: Dictionary with keys 'q1', 'q2', 'q3', 'q4', 'q5' and their selected names
        top_choice: Optional open-ended response about top choice
        bottom_choice: Optional open-ended response about confusing/untrustworthy names
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Insert submission
                cur.execute("""
                    INSERT INTO submissions (
                        form_id, session_id, submission_datetime,
                        question_1_answer, question_2_answer, question_3_answer,
                        question_4_answer, question_5_answer,
                        top_choice, bottom_choice
                    ) VALUES (
                        %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    form_id,
                    session_id,
                    answers['q1'],
                    answers['q2'],
                    answers['q3'],
                    answers['q4'],
                    answers['q5'],
                    top_choice,
                    bottom_choice
                ))

                print(f"Submission saved for form {form_id} with session {session_id}")
                
                # Increment form counter with error handling
                try:
                    # First ensure the form_counter row exists
                    cur.execute("""
                        INSERT INTO form_counters (form_id, submission_count, last_assigned)
                        VALUES (%s, 0, NULL)
                        ON CONFLICT (form_id) DO NOTHING
                    """, (form_id,))
                    insert_affected = cur.rowcount
                    if insert_affected > 0:
                        print(f"Inserted new row for form_id {form_id} in form_counters")
                    
                    # Now increment it
                    cur.execute("""
                        UPDATE form_counters 
                        SET submission_count = submission_count + 1 
                        WHERE form_id = %s
                    """, (form_id,))
                    
                    update_affected = cur.rowcount
                    if update_affected > 0:
                        # Get the new count
                        cur.execute("SELECT submission_count FROM form_counters WHERE form_id = %s", (form_id,))
                        new_count = cur.fetchone()[0]
                        print(f"Form counter incremented for form {form_id}: now at {new_count} submissions")
                    else:
                        print(f"WARNING: UPDATE didn't affect any rows for form_id {form_id}")
                except Exception as counter_error:
                    print(f"Error updating form counter for form {form_id}: {counter_error}")
                    print(f"Error type: {type(counter_error).__name__}")
                    import traceback
                    traceback.print_exc()
                    print(f"Submission was still saved successfully")
                
                conn.commit()
                return True
    except Exception as e:
        print(f"Error saving submission: {e}")
        return False


def get_form_statistics() -> Dict[int, int]:
    """
    Get submission counts for all forms.
    Returns dict mapping form_id to submission_count.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT form_id, submission_count 
                FROM form_counters 
                ORDER BY form_id
            """)
            results = cur.fetchall()
            return {row['form_id']: row['submission_count'] for row in results}


def get_worst_performing_names(question_num: int):
    """
    Get the 3 worst performing names for a specific question based on exposure vs votes gap.
    Names with the largest gap between exposures and votes are the worst performers.
    
    Args:
        question_num: Question number (1-5)
    
    Returns:
        List of dicts with name, exposure_count, vote_count, and gap
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Build the exposure counting query dynamically based on forms_config
            # This maps each form to its names
            form_names = {
                1: ['Philanthrifind', 'Give-io', 'Donathropy', 'Kinderfully'],
                2: ['Philanthrifound', 'Causenex', 'Givanthropy', 'Tomatchin'],
                3: ['Philanthri', 'Give Connects', 'Donanthropy', 'Humanitable'],
                4: ['Givio Gives', 'Philanthrifound', 'Givanthropy', 'Humanitable'],
                5: ['Give Connects', 'Philanthrifind', 'Give-io', 'Tomatchin'],
                6: ['Philanthri', 'Givio Gives', 'Kinderfully', 'Causenex']
            }
            
            column_name = f"question_{question_num}_answer"
            
            cur.execute(f"""
                WITH name_exposures AS (
                    -- Count how many times each name was exposed (shown on a form that was submitted)
                    SELECT 
                        name,
                        COUNT(*) as exposure_count
                    FROM (
                        -- Form 1
                        SELECT 'Philanthrifind' as name FROM submissions WHERE form_id = 1
                        UNION ALL SELECT 'Give-io' FROM submissions WHERE form_id = 1
                        UNION ALL SELECT 'Donathropy' FROM submissions WHERE form_id = 1
                        UNION ALL SELECT 'Kinderfully' FROM submissions WHERE form_id = 1
                        -- Form 2
                        UNION ALL SELECT 'Philanthrifound' FROM submissions WHERE form_id = 2
                        UNION ALL SELECT 'Causenex' FROM submissions WHERE form_id = 2
                        UNION ALL SELECT 'Givanthropy' FROM submissions WHERE form_id = 2
                        UNION ALL SELECT 'Tomatchin' FROM submissions WHERE form_id = 2
                        -- Form 3
                        UNION ALL SELECT 'Philanthri' FROM submissions WHERE form_id = 3
                        UNION ALL SELECT 'Give Connects' FROM submissions WHERE form_id = 3
                        UNION ALL SELECT 'Donanthropy' FROM submissions WHERE form_id = 3
                        UNION ALL SELECT 'Humanitable' FROM submissions WHERE form_id = 3
                        -- Form 4
                        UNION ALL SELECT 'Givio Gives' FROM submissions WHERE form_id = 4
                        UNION ALL SELECT 'Philanthrifound' FROM submissions WHERE form_id = 4
                        UNION ALL SELECT 'Givanthropy' FROM submissions WHERE form_id = 4
                        UNION ALL SELECT 'Humanitable' FROM submissions WHERE form_id = 4
                        -- Form 5
                        UNION ALL SELECT 'Give Connects' FROM submissions WHERE form_id = 5
                        UNION ALL SELECT 'Philanthrifind' FROM submissions WHERE form_id = 5
                        UNION ALL SELECT 'Give-io' FROM submissions WHERE form_id = 5
                        UNION ALL SELECT 'Tomatchin' FROM submissions WHERE form_id = 5
                        -- Form 6
                        UNION ALL SELECT 'Philanthri' FROM submissions WHERE form_id = 6
                        UNION ALL SELECT 'Givio Gives' FROM submissions WHERE form_id = 6
                        UNION ALL SELECT 'Kinderfully' FROM submissions WHERE form_id = 6
                        UNION ALL SELECT 'Causenex' FROM submissions WHERE form_id = 6
                    ) AS all_exposures
                    GROUP BY name
                ),
                name_votes AS (
                    -- Count how many votes each name received for this specific question
                    SELECT 
                        {column_name} as name,
                        COUNT(*) as vote_count
                    FROM submissions
                    GROUP BY {column_name}
                )
                SELECT 
                    ne.name,
                    ne.exposure_count,
                    COALESCE(nv.vote_count, 0) as vote_count,
                    ne.exposure_count - COALESCE(nv.vote_count, 0) as gap
                FROM name_exposures ne
                LEFT JOIN name_votes nv ON ne.name = nv.name
                ORDER BY gap DESC, ne.name
                LIMIT 3
            """)
            
            return cur.fetchall()


def get_question_rankings():
    """
    Get top 3 and bottom 3 names for each question.
    Returns a dict with question IDs as keys and rankings as values.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            rankings = {}
            
            for question_num in range(1, 6):
                column_name = f"question_{question_num}_answer"
                
                # Get top 3
                cur.execute(f"""
                    SELECT {column_name} as name, COUNT(*) as count
                    FROM submissions
                    GROUP BY {column_name}
                    ORDER BY count DESC, {column_name}
                    LIMIT 3
                """)
                top_3 = cur.fetchall()
                
                # Get bottom 3 (worst performers based on exposure vs votes gap)
                worst_3 = get_worst_performing_names(question_num)
                
                rankings[f"q{question_num}"] = {
                    "top_3": [{"name": row["name"], "count": row["count"]} for row in top_3],
                    "bottom_3": [{"name": row["name"], "exposure_count": row["exposure_count"], 
                                  "vote_count": row["vote_count"], "gap": row["gap"]} for row in worst_3]
                }
            
            return rankings