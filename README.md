# AI Dashboard

A dashboard that aggregates 3rd party apps into a grid layout, using AI to generate widget HTML/CSS.

## Features

- **12-column responsive grid** - Auto-places widgets by registration date
- **App Registration API** - Apps register with registration token, receive integration token
- **Data Sharing API** - Apps share data + render prompts, dashboard generates widgets
- **Server-Side Rendering** - AI generates widget HTML/CSS server-side
- **Auto-refresh** - Widgets refresh on timer without regenerating AI
- **MongoDB Storage** - Stores apps, widgets, and cached HTML

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file (or use defaults):
```bash
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=ai_dashboard
REGISTRATION_TOKEN=demo_registration_token_123
ANTHROPIC_API_KEY=your_anthropic_api_key_here
WIDGET_REFRESH_INTERVAL=30000
```

**Important**: Get your Anthropic API key from [console.anthropic.com](https://console.anthropic.com).

3. Make sure MongoDB is running

4. Start the server:
```bash
uvicorn main:app --reload
```

## Heroku Deployment

Quick deploy:
```bash
heroku create your-app-name
heroku config:set MONGODB_URI="your_mongodb_atlas_uri"
heroku config:set ANTHROPIC_API_KEY="your_api_key"
git push heroku main
```

## Testing with Mock App

Run the mock 3rd party app to see how integration works:

```bash
python mock_app.py
```

This will:
1. Register a "Weather Widget" app with the dashboard
2. Share sample weather data with a render prompt
3. The dashboard will generate (placeholder) widget HTML

Then visit `http://localhost:8000` to see the dashboard.

## API Endpoints

- `POST /register` - Register a new app (requires registration token)
  - Body: `{registration_token, app_name}`
  - Returns: `{integration_token, app_id}`
  
- `POST /share-data` - Share data and prompt from 3rd party app (requires integration token)
  - Body: `{integration_token, data, render_prompt}`
  - Triggers AI generation and caches HTML
  
- `GET /` - Main dashboard page (SSR with all widgets)
  
- `GET /widget/{app_id}/refresh` - Refresh widget HTML (returns cached, no AI regeneration)

## Project Structure

- `main.py` - FastAPI app with all endpoints
- `models.py` - Pydantic models for requests/responses
- `database.py` - MongoDB connection and collections
- `config.py` - Configuration from environment variables
- `ai_generator.py` - AI widget generation using Claude 3.5 Sonnet
- `mock_app.py` - Example 3rd party app integration
- `templates/dashboard.html` - Dashboard template with grid layout


