# VibeHack - Hackathon Discovery Platform with AI & OAuth2

VibeHack is a REST API platform for discovering hackathons using AI-powered recommendations and integrating with Google Calendar. It combines local AI (Qwen2) for intelligent search with OAuth2 Google authentication.

## Features

- 🔐 **OAuth2 Google Authentication**: Secure registration and login via Google
- 🤖 **AI-Powered Search**: Semantic search using Qwen2 and embeddings
- 📅 **Google Calendar Integration**: One-click event creation in your calendar
- 🎯 **Smart Filtering**: Only shows hackathons with open registration
- 🏷️ **Technology Tags**: Filter hackathons by tech stack
- 🔄 **No Duplicate Recommendations**: Qwen2 tracks and avoids recommending same hackathons
- 🔍 **Semantic Search**: Natural language queries for better results

## Project Structure

```
VibeHack/
├── backend/
│   ├── routers/
│   │   ├── auth.py                 # OAuth2 and JWT authentication
│   │   ├── hackathons.py           # CRUD and AI search endpoints
│   │   └── calendar.py             # Google Calendar API integration
│   ├── services/
│   │   └── google_calendar.py      # Google Calendar helper functions
│   ├── models.py                   # SQLAlchemy ORM models (User, Hackathon, Technology)
│   ├── schemas.py                  # Pydantic request/response schemas
│   ├── database.py                 # Database configuration
│   ├── ai_recommender.py           # Qwen2 and embeddings engine
│   ├── init_technologies.py        # Initialize default technologies
│   ├── main.py                     # FastAPI application
│   └── hackathon_service.py        # Business logic (reserved for future)
├── requirements.txt                # Python dependencies
└── .env.example                    # Environment variables template
```

## Database Schema

### Users
- id (Primary Key)
- email (Unique)
- name
- google_id (Unique)
- access_token (Google OAuth token)
- refresh_token
- token_expiry
- created_at

### Hackathons
- id (Primary Key)
- title
- description
- start_date (hackathon start)
- end_date (hackathon end)
- registration_deadline ⭐ (cutoff for registration)
- format (online/offline)
- url
- location (city/venue)
- source (devpost, hackerearth, etc.)
- created_at

### Technologies
- id (Primary Key)
- name (unique)
- category (Language, Framework, Database, AI, Cloud, DevOps, Mobile, Technology)
- created_at

### UserHackathon
- id (Primary Key)
- user_id (Foreign Key)
- hackathon_id (Foreign Key)
- calendar_event_id (Google Calendar event ID)
- added_to_calendar
- saved_at

## Setup Instructions

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Ollama (for Qwen2 model)
- Google OAuth2 credentials

### Backend Setup

1. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file** (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

4. **Configure environment variables**:
   ```
   # Database
   DATABASE_URL=postgresql://user:password@localhost/vibehack

   # Google OAuth2
   GOOGLE_CLIENT_ID=your_client_id_from_console.developers.google.com
   GOOGLE_CLIENT_SECRET=your_client_secret
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

   # Ollama
   OLLAMA_BASE_URL=http://localhost:11434

   # JWT
   SECRET_KEY=generate_a_strong_random_key_here
   ALGORITHM=HS256
   ```

5. **Set up PostgreSQL**:
   ```bash
   # Create database
   createdb vibehack
   ```

6. **Install and run Ollama** (for Qwen2):
   ```bash
   # Download from https://ollama.ai
   ollama serve

   # In another terminal, pull Qwen2 model
   ollama pull qwen2
   ```

7. **Start the backend**:
   ```bash
   python -m uvicorn backend.main:app --reload --port 8000
   ```

   API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `GET /auth/login` - Get Google OAuth URL
- `GET /auth/callback?code=code` - OAuth callback handler
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/logout` - Logout

### Hackathons
- `GET /hackathons` - List all hackathons (with pagination)
- `GET /hackathons/{id}` - Get hackathon details
- `GET /hackathons/search/query?q=query` - Text search (basic)
- `GET /hackathons/search/ai?q=query` - AI-powered semantic search ⭐
  - Filters: only shows hackathons with `registration_deadline > now`
  - Uses Qwen2 embeddings for semantic matching
  - Tracks recommendations to avoid duplicates
- `POST /hackathons` - Create hackathon (admin)
- `PUT /hackathons/{id}` - Update hackathon (admin)
- `DELETE /hackathons/{id}` - Delete hackathon (admin)

### Technologies
- `GET /hackathons/technologies` - List all available technologies
- `POST /hackathons/technologies` - Create new technology (admin)
- `DELETE /hackathons/technologies/{id}` - Delete technology (admin)

### Calendar
- `POST /calendar/add-hackathon` - Add hackathon to Google Calendar
  ```json
  {
    "hackathon_id": 1
  }
  ```

## Usage

### Getting Started

1. **Create hackathons** (via admin panel or direct API):
   ```bash
   curl -X POST http://localhost:8000/hackathons \
     -H "Content-Type: application/json" \
     -d '{
       "title": "AI Hackathon 2025",
       "description": "Build AI projects with Qwen2",
       "start_date": "2025-04-01",
       "end_date": "2025-04-03",
       "registration_deadline": "2025-03-25",
       "format": "online",
       "url": "https://example.com/hackathon",
       "location": "Online",
       "technology_ids": [1, 2, 3]
     }'
   ```

2. **Get technologies list**:
   ```bash
   curl http://localhost:8000/hackathons/technologies
   ```

3. **Search with AI**:
   ```bash
   curl "http://localhost:8000/hackathons/search/ai?q=machine+learning+python"
   ```

4. **Add to calendar** (authenticated users):
   ```bash
   curl -X POST http://localhost:8000/calendar/add-hackathon \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"hackathon_id": 1}'
   ```

## Default Technologies

The system initializes with 50+ technologies including:

**Languages**: Python, JavaScript, TypeScript, Java, C++, Rust, Go, Ruby, etc.
**Frameworks**: React, Vue.js, Angular, Django, FastAPI, Flask, Express.js, etc.
**Databases**: PostgreSQL, MongoDB, MySQL, Redis, Firebase, etc.
**AI/ML**: TensorFlow, PyTorch, Scikit-learn, NLP, Computer Vision, Qwen2, LLM
**Cloud**: AWS, Google Cloud, Azure
**DevOps**: Docker, Kubernetes, CI/CD
**Mobile**: React Native, Flutter, iOS, Android

## How It Works

### AI-Powered Search

1. User queries: "I want to learn machine learning with Python"
2. Query is converted to embeddings using `all-MiniLM-L6-v2`
3. Each hackathon (including its technologies) is embedded
4. Semantic similarity is calculated using cosine distance
5. Results are ranked by relevance
6. Qwen2 can provide additional suggestions based on query

### Duplicate Prevention

- The `AIRecommender` class maintains a set of recommended hackathon IDs per session
- When searching, already-recommended hackathons are filtered out
- This ensures users get diverse recommendations

### Registration Deadline Filtering

- AI search only shows hackathons where `registration_deadline > current_datetime`
- Users can still browse all hackathons via basic search
- When adding to calendar, the system validates the hackathon is still open

## Example: Complete Workflow

```bash
# 1. Initialize database (automatic on startup)
# 2. Manually create some hackathons
curl -X POST http://localhost:8000/hackathons \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Web Dev Hackathon",
    "start_date": "2025-04-10",
    "registration_deadline": "2025-04-05",
    "format": "online",
    "technology_ids": [14, 15, 16]
  }'

# 3. Search using AI
curl "http://localhost:8000/hackathons/search/ai?q=web+development&limit=5"

# 4. User logs in with Google OAuth
# 5. Frontend shows search results
# 6. User clicks "Add to Calendar"
# 7. Event appears in their Google Calendar automatically
```

## Technologies Used

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Ollama + Qwen2** - Local LLM for semantic search
- **sentence-transformers** - Embeddings generation
- **google-auth-oauthlib** - Google OAuth2 integration
- **google-api-python-client** - Google Calendar API
- **PyJWT** - JWT token management

## Security Notes

- JWT tokens for API authentication
- Google OAuth2 with PKCE flow for secure third-party auth
- Refresh tokens for token rotation
- HTTPS recommended in production
- Environment variables for sensitive configuration

## Troubleshooting

### "Connection refused" for database
- Check PostgreSQL is running: `pg_isready -h localhost`
- Verify DATABASE_URL connection string

### Ollama connection error
- Ensure Ollama is running: `ollama serve`
- Check OLLAMA_BASE_URL in .env
- Pull model: `ollama pull qwen2`

### OAuth2 fails
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from Google Console
- Check GOOGLE_REDIRECT_URI matches Google Console settings
- Ensure redirect is to `http://localhost:8000/auth/callback`

### No search results
- Check hackathons have registration_deadline in future
- Verify technologies are properly linked to hackathons
- Test with simpler queries first

## Future Enhancements

- [ ] Batch hackathon import from CSV/API
- [ ] Email notifications for matching hackathons
- [ ] User preferences and skill profiles
- [ ] Team matching between users
- [ ] Hackathon past performance tracking
- [ ] Mobile app
- [ ] Real-time scraping of major hackathon sites

## License

MIT

## Support

For issues or feature requests, please report them.
