# Market Research Survey App

A Streamlit-based market research survey application that collects user preferences on different brand names. The app uses PostgreSQL for data persistence and is designed to be deployed on Fly.io.

## Features

- **4 Survey Forms**: Each form presents 4 unique brand names (16 names total)
- **5 Questions per Form**: Consistent questions across all forms asking about preferences
- **Smart Form Distribution**: Automatically serves the form with the least submissions to balance data collection
- **Session Tracking**: Tracks users via session IDs to identify repeat submissions
- **Round-Robin Balancing**: Ensures equal distribution of responses across all forms
- **Responsive UI**: Clean, modern interface built with Streamlit
- **Statistics Dashboard**: View submission counts for each form

## Architecture

```
User → Streamlit App → PostgreSQL Database
                ↓
        Session Management
        Form Selection Logic
        Response Recording
```

### Database Schema

**form_counters table:**
- `form_id` (INTEGER, PRIMARY KEY): Form identifier (1-4)
- `submission_count` (INTEGER): Number of submissions for this form
- `last_assigned` (TIMESTAMP): Last time this form was assigned

**submissions table:**
- `id` (SERIAL, PRIMARY KEY): Unique submission ID
- `form_id` (INTEGER): Which form was submitted
- `session_id` (VARCHAR): User's session identifier
- `submission_datetime` (TIMESTAMP): When the submission occurred
- `question_1_answer` through `question_5_answer` (VARCHAR): User's selected names

## Local Development

### Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- pip (Python package manager)

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd market-research
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL**
   
   Create a local PostgreSQL database:
   ```bash
   createdb market_research
   ```

4. **Configure environment variables**
   
   Create a `.env` file:
   ```bash
   cp .env.template .env
   ```
   
   Edit `.env` and set your database URL:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/market_research
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```
   
   The app will be available at `http://localhost:8501`

## Deployment to Fly.io

### Prerequisites

- [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) installed
- Fly.io account (sign up at https://fly.io)

### Step-by-Step Deployment

1. **Login to Fly.io**
   ```bash
   fly auth login
   ```

2. **Create a PostgreSQL cluster**
   ```bash
   fly postgres create
   ```
   
   Follow the prompts:
   - Choose a name (e.g., `market-research-db`)
   - Select a region close to your users
   - Choose configuration (Development is fine for testing)

3. **Launch the application**
   ```bash
   fly launch
   ```
   
   This will:
   - Detect the Dockerfile
   - Create `fly.toml` configuration (already provided)
   - Ask for an app name (e.g., `market-research-survey`)
   - Deploy the application

4. **Attach the PostgreSQL database**
   ```bash
   fly postgres attach <your-postgres-app-name>
   ```
   
   This automatically sets the `DATABASE_URL` environment variable.

5. **Deploy the application**
   ```bash
   fly deploy
   ```

6. **Open your application**
   ```bash
   fly open
   ```

### Updating the Application

After making changes to your code:

```bash
fly deploy
```

### Viewing Logs

```bash
fly logs
```

### Checking Application Status

```bash
fly status
```

### Accessing the Database

To connect to your production database:

```bash
fly postgres connect -a <your-postgres-app-name>
```

## Configuration

### Customizing Form Names

Edit `forms_config.py` to change the brand names for each form:

```python
FORMS = {
    1: {
        "names": ["YourName1", "YourName2", "YourName3", "YourName4"],
        "title": "Survey Form A"
    },
    # ... more forms
}
```

### Customizing Questions

Edit the `QUESTIONS` list in `forms_config.py`:

```python
QUESTIONS = [
    {
        "id": "q1",
        "text": "Your custom question here?"
    },
    # ... more questions
]
```

## File Structure

```
market-research/
├── app.py                  # Main Streamlit application
├── database.py             # Database operations and connection management
├── forms_config.py         # Survey forms and questions configuration
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── fly.toml               # Fly.io deployment configuration
├── .env.template          # Environment variables template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## How It Works

1. **User visits the site**: A unique session ID is generated
2. **Get New Form**: User clicks button to receive a survey
3. **Form Selection**: App queries database for form with least submissions
4. **Survey Display**: User answers 5 questions selecting from 4 names
5. **Submission**: Answers are saved to database, form counter increments
6. **Repeat**: User can request another form, which will be balanced based on submission counts

## Database Maintenance

### View Submission Statistics

The app displays statistics on the main page, but you can also query directly:

```sql
-- Connect to your database
SELECT * FROM form_counters ORDER BY form_id;

-- View all submissions
SELECT * FROM submissions ORDER BY submission_datetime DESC;

-- Count submissions by form
SELECT form_id, COUNT(*) as count 
FROM submissions 
GROUP BY form_id;
```

### Reset Counters

If you need to reset the submission counters:

```sql
UPDATE form_counters SET submission_count = 0, last_assigned = NULL;
```

## Troubleshooting

### "DATABASE_URL environment variable is not set"

Make sure you've either:
- Created a `.env` file with `DATABASE_URL` for local development
- Attached a Postgres database using `fly postgres attach` for Fly.io

### Connection Pool Errors

If you see connection pool errors, the database might be overwhelmed. Consider:
- Increasing the connection pool size in `database.py`
- Upgrading your Fly.io Postgres plan

### Application Won't Start on Fly.io

Check logs:
```bash
fly logs
```

Common issues:
- Database not attached: Run `fly postgres attach`
- Port configuration: Ensure Dockerfile exposes 8501
- Build errors: Check Dockerfile syntax

## License

This project is provided as-is for market research purposes.

## Support

For issues or questions, please open an issue in the repository.
