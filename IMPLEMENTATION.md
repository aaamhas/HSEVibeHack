# VibeHack - Hackathon Discovery Platform

## 📋 What's New

This implementation includes three major additions:

### 1. ✅ Centralized Logging System
- **Location**: `backend/config/logging_config.py`
- **Features**:
  - Console logging (INFO level)
  - File logging with rotation (`logs/vibehack.log`)
  - Separate error log (`logs/vibehack_errors.log`)
  - Structured error tracking with stack traces
  - Integrated into all backend modules

**Usage**:
```python
from backend.config.logging_config import get_logger
logger = get_logger(__name__)
logger.error("Error message", exc_info=True)
```

### 2. 🔄 Hackathon Parsers
- **Source 1**: https://хакатоны.рус - Russian hackathon directory
- **Source 2**: https://hackathons.pro/ - International hackathons
- **Source 3**: https://russianhackers.org/ - Russian hackers community events

**Parser Components**:
- `backend/services/parsers/base_parser.py` - Abstract base class
- `backend/services/parsers/xakatonru_parser.py` - Xakatony.ru parser
- `backend/services/parsers/hackathonspro_parser.py` - Hackathons.pro parser
- `backend/services/parsers/russianhackers_parser.py` - RussianHackers parser
- `backend/hackathon_service.py` - Orchestration service

**Parser API Endpoints**:
```
POST /hackathons/parse/update - Run all parsers
GET /hackathons/parse/sources - Get available parser sources
```

**Error Handling**:
- Network errors (timeouts, connection failures)
- HTML parsing failures
- Duplicate detection
- Comprehensive logging

### 3. 🎨 Minimal Frontend
- **Tech**: Vanilla JavaScript (no build tools required)
- **Location**: `frontend/` directory
- **Files**:
  - `index.html` - Main UI
  - `styles.css` - Dark theme styling
  - `app.js` - Frontend logic

**Features**:
- Browse all hackathons
- Search by title/description (text search)
- AI-powered semantic search (🤖 button)
- Refresh parser data on demand
- Login/logout (dev login for testing)
- Add hackathons to Google Calendar (logged-in users)
- Paginated results (10 per page)
- Mobile responsive design

## 🚀 Getting Started

### Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Start the backend server
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Frontend Setup
```bash
# Start the frontend server
python run_frontend.py
```

The frontend will be available at: `http://localhost:3000`

### Docker Setup
```bash
# Build and start all services
docker-compose up --build
```

## 📊 How the Parsers Work

### Parsing Flow
1. **Trigger**: User clicks "🔄 Refresh Data" on frontend OR calls `POST /hackathons/parse/update`
2. **Execution**: All parsers run sequentially
3. **Processing**:
   - Fetch HTML from each source
   - Parse hackathon elements
   - Extract: title, description, dates, location, URL, technologies
   - Normalize data to Hackathon schema
   - Check for duplicates (title + source)
4. **Storage**: Add new hackathons to PostgreSQL
5. **Logging**: Record results and any errors
6. **Response**: Return summary with counts

### Response Example
```json
{
  "total_found": 45,
  "total_added": 32,
  "duplicates_skipped": 13,
  "errors": [],
  "parser_results": [
    {
      "parser": "xakatony.ru",
      "found": 15,
      "added": 12,
      "duplicates": 3
    },
    ...
  ]
}
```

## 📝 Logging

### Log Files
- `logs/vibehack.log` - All logs (DEBUG and above)
- `logs/vibehack_errors.log` - Errors only
- Console output - INFO and above

### Log Format
```
[2026-03-15 13:20:45] [ERROR] [backend.services.parsers.xakatonru_parser] Error parsing from xakatony.ru: Connection timeout
```

### Key Logged Events
- Application startup/shutdown
- Parser execution start/end
- Successful hackathon parsing and storage
- Duplicate detections
- API request errors
- AI recommendation queries
- User login/logout

## 🔧 Configuration

### Environment Variables (`.env`)
```
FRONTEND_URL=http://localhost:3000
DATABASE_URL=postgresql://vibehack:vibehack_pass@postgres:5432/vibehack
REDIS_URL=redis://redis:6379
OLLAMA_BASE_URL=http://ollama:11434
JWT_SECRET=your-secret-key-here
```

## 🏗️ Architecture Changes

### Database Models
Added two new models:
- **User**: Stores user information (email, name)
- **UserHackathon**: Tracks which hackathons users have added to calendar

### Backend Structure
```
backend/
├── config/
│   └── logging_config.py (NEW)
├── services/
│   └── parsers/ (NEW)
│       ├── base_parser.py
│       ├── xakatonru_parser.py
│       ├── hackathonspro_parser.py
│       └── russianhackers_parser.py
├── routers/
│   └── hackathons.py (UPDATED - new parser endpoints)
├── models.py (UPDATED - new User, UserHackathon models)
├── main.py (UPDATED - logging initialization)
├── ai_recommender.py (UPDATED - use logger instead of print)
└── hackathon_service.py (NEW - parser orchestration)
```

## 🧪 Testing

### Test the Backend
```bash
# Health check
curl http://localhost:8000/health

# List hackathons
curl http://localhost:8000/hackathons

# Trigger parsers
curl -X POST http://localhost:8000/hackathons/parse/update

# Search hackathons
curl "http://localhost:8000/hackathons/search/query?q=python"

# AI search
curl "http://localhost:8000/hackathons/search/ai?q=machine+learning"
```

### Test the Frontend
1. Open `http://localhost:3000`
2. Click "🔄 Refresh Data" to populate database
3. Search for hackathons
4. Try AI search with "machine learning"
5. Login with dev credentials to add to calendar

### Check Logs
```bash
# Watch real-time logs
tail -f logs/vibehack.log

# Check errors
tail -f logs/vibehack_errors.log
```

## 🔍 Error Handling

### Parser Error Handling
- Timeouts: If a site takes >30 seconds, parser logs timeout and continues
- Invalid HTML: Gracefully handles missing elements, logs debug info
- Network errors: Logs and returns empty results for that parser
- Duplicates: Silently skipped with debug log

### API Error Handling
- Validation errors: 400 Bad Request with details
- Not found: 404 Not Found
- Server errors: 500 Internal Server Error with logged stack trace

### Frontend Error Handling
- Network errors: Displayed to user in message box
- Invalid responses: Caught and logged
- Missing data: Gracefully hidden (no description → field hidden)

## 📱 Frontend Usage

### Search Options
1. **Text Search**: Default, case-insensitive, searches title & description
2. **AI Search**: Uses semantic embedding to find related hackathons even if keywords don't match exactly

### User Actions
- **Login**: Use dev-login endpoint for testing (Google OAuth in production)
- **Add to Calendar**: Save hackathon to user's Google Calendar
- **View Details**: Click any card to see full information
- **Pagination**: Navigate through results

## 🚧 Future Improvements

Potential enhancements:
1. Real-time parser scheduling (e.g., daily updates)
2. More parsers for other hackathon platforms
3. Advanced filtering (by date range, location, technologies)
4. User saved hackathons and recommendations
5. Email notifications for new matching hackathons
6. Analytics dashboard

## 🐛 Known Limitations

1. **Parser Accuracy**: Site structure changes may break parsers - needs manual updates
2. **Date Extraction**: Simplified date parsing, may need improvements for complex formats
3. **Rate Limiting**: No rate limiting on parsers - be respectful of target sites
4. **Authentication**: Dev-login only, no real Google OAuth flow implemented

## 📞 Support

For issues or errors:
1. Check logs in `logs/` directory
2. Review error messages in frontend
3. Check API response in browser dev tools
4. Verify database connection
5. Ensure all parsers are accessible

---

**Built with**: FastAPI, PostgreSQL, Redis, Ollama (Qwen2), Sentence Transformers
**Deployment**: Docker, suitable for DigitalOcean/AWS/Azure
