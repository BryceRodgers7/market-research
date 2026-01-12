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
                    question_5_answer VARCHAR(255) NOT NULL
                )
            """)
            
            # Initialize form_counters if empty
            cur.execute("SELECT COUNT(*) FROM form_counters")
            count = cur.fetchone()[0]
            
            if count == 0:
                # Insert initial form counters (1-4)
                for form_id in range(1, 5):
                    cur.execute("""
                        INSERT INTO form_counters (form_id, submission_count, last_assigned)
                        VALUES (%s, 0, NULL)
                    """, (form_id,))
            
            conn.commit()


def get_least_submitted_form() -> int:
    """
    Get the form_id with the least submissions.
    Returns form_id (1-4).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
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
                # Update last_assigned timestamp
                cur.execute("""
                    UPDATE form_counters 
                    SET last_assigned = NOW() 
                    WHERE form_id = %s
                """, (form_id,))
                conn.commit()
                return form_id
            else:
                # Fallback to form 1 if no forms found (shouldn't happen)
                return 1


def save_submission(
    form_id: int,
    session_id: str,
    answers: Dict[str, str]
) -> bool:
    """
    Save a submission to the database and increment form counter.
    
    Args:
        form_id: The form ID (1-4)
        session_id: User's session ID
        answers: Dictionary with keys 'q1', 'q2', 'q3', 'q4', 'q5' and their selected names
    
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
                        question_4_answer, question_5_answer
                    ) VALUES (
                        %s, %s, NOW(), %s, %s, %s, %s, %s
                    )
                """, (
                    form_id,
                    session_id,
                    answers['q1'],
                    answers['q2'],
                    answers['q3'],
                    answers['q4'],
                    answers['q5']
                ))
                
                # Increment form counter
                cur.execute("""
                    UPDATE form_counters 
                    SET submission_count = submission_count + 1 
                    WHERE form_id = %s
                """, (form_id,))
                
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
                
                # Get bottom 3
                cur.execute(f"""
                    SELECT {column_name} as name, COUNT(*) as count
                    FROM submissions
                    GROUP BY {column_name}
                    ORDER BY count ASC, {column_name}
                    LIMIT 3
                """)
                bottom_3 = cur.fetchall()
                
                rankings[f"q{question_num}"] = {
                    "top_3": [{"name": row["name"], "count": row["count"]} for row in top_3],
                    "bottom_3": [{"name": row["name"], "count": row["count"]} for row in bottom_3]
                }
            
            return rankings