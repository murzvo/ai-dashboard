# AI Dashboard Integration Guide

This guide explains how to integrate your 3rd party app with the AI Dashboard.

## Overview

The AI Dashboard allows 3rd party apps to register and display widgets. The dashboard uses AI to generate HTML/CSS widgets based on your data and rendering instructions.

**Integration requires 2 steps:**
1. Register your app to get an integration token
2. Share data and rendering instructions to generate widgets

## Step 1: Register Your App

**Endpoint:** `POST /register`

**Request:**
```json
{
  "registration_token": "YOUR_REGISTRATION_TOKEN",
  "app_name": "My App Name"
}
```

**Response:**
```json
{
  "integration_token": "unique_token_here",
  "app_id": "app_id_here"
}
```

**Parameters:**
- `registration_token`: Provided by dashboard administrator
- `app_name`: Display name for your app

**Save the `integration_token`** - you'll need it for all future requests.

## Step 2: Share Data

**Endpoint:** `POST /share-data`

**Request:**
```json
{
  "integration_token": "your_integration_token",
  "data": {
    "key1": "value1",
    "key2": "value2"
  },
  "render_prompt": "Create a weather widget showing current temperature and condition. Display temperature prominently with an icon."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Data shared and widget generated successfully"
}
```

**Parameters:**
- `integration_token`: Token received from registration
- `data`: Your app's data (any JSON structure)
- `render_prompt`: Instructions for how the AI should render the widget

**Note:** Each time you call `/share-data`, the widget is regenerated with the latest data.

## Example: Python Integration

```python
import requests
import json

# Configuration
DASHBOARD_URL = "https://your-dashboard-url.com"
REGISTRATION_TOKEN = "your_registration_token"  # Get from admin

# Step 1: Register your app (do this once)
def register_app(app_name):
    url = f"{DASHBOARD_URL}/register"
    payload = {
        "registration_token": REGISTRATION_TOKEN,
        "app_name": app_name
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Registered! Integration token: {data['integration_token']}")
        return data['integration_token']
    else:
        print(f"Registration failed: {response.text}")
        return None

# Step 2: Share data (call this whenever your data updates)
def share_data(integration_token, data, render_prompt):
    url = f"{DASHBOARD_URL}/share-data"
    payload = {
        "integration_token": integration_token,
        "data": data,
        "render_prompt": render_prompt
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Data shared successfully!")
        return True
    else:
        print(f"Failed to share data: {response.text}")
        return False

# Example usage
if __name__ == "__main__":
    # Register once
    token = register_app("Weather App")
    
    if token:
        # Share data whenever it updates
        weather_data = {
            "city": "San Francisco",
            "temperature": 72,
            "condition": "Sunny",
            "humidity": 65
        }
        
        prompt = """
        Create a weather widget displaying:
        - City name at the top
        - Large temperature display
        - Weather condition with icon
        - Humidity percentage
        Use a clean, modern design with weather-appropriate colors.
        """
        
        share_data(token, weather_data, prompt)
```

## Example: JavaScript/Node.js Integration

```javascript
const axios = require('axios');

const DASHBOARD_URL = 'https://your-dashboard-url.com';
const REGISTRATION_TOKEN = 'your_registration_token';

// Step 1: Register your app
async function registerApp(appName) {
  try {
    const response = await axios.post(`${DASHBOARD_URL}/register`, {
      registration_token: REGISTRATION_TOKEN,
      app_name: appName
    });
    
    console.log('Registered! Integration token:', response.data.integration_token);
    return response.data.integration_token;
  } catch (error) {
    console.error('Registration failed:', error.response?.data || error.message);
    return null;
  }
}

// Step 2: Share data
async function shareData(integrationToken, data, renderPrompt) {
  try {
    const response = await axios.post(`${DASHBOARD_URL}/share-data`, {
      integration_token: integrationToken,
      data: data,
      render_prompt: renderPrompt
    });
    
    console.log('Data shared successfully!');
    return true;
  } catch (error) {
    console.error('Failed to share data:', error.response?.data || error.message);
    return false;
  }
}

// Example usage
(async () => {
  const token = await registerApp('Task Tracker');
  
  if (token) {
    await shareData(token, {
      tasks: [
        { id: 1, title: 'Complete project', status: 'in-progress' },
        { id: 2, title: 'Review code', status: 'pending' }
      ]
    }, 'Create a task list widget showing all tasks with their status. Use color coding for different statuses.');
  }
})();
```

## Tips for Writing Render Prompts

- **Be specific**: Describe the layout, colors, and data to display
- **Include examples**: Mention similar widgets or design styles
- **Specify data usage**: Explain which data fields to display and how
- **Request styling**: Ask for specific colors, fonts, or layouts if needed

**Good prompt example:**
```
Create a sales dashboard widget showing:
- Total revenue in large, bold text at the top
- Revenue breakdown by product category as a horizontal bar chart
- Use green colors for positive values, red for negative
- Include icons for each category
- Make it responsive and modern
```

## Widget Layout

- Widgets automatically size based on their content
- The dashboard uses a flexible layout that adapts to widget sizes
- Widgets wrap to new rows automatically as needed

## Error Handling

- **401 Unauthorized**: Invalid `integration_token` or `registration_token`
- **400 Bad Request**: Missing or invalid request parameters
- **500 Internal Server Error**: Server-side error (check dashboard logs)

## Best Practices

1. **Register once**: Store your `integration_token` securely
2. **Update regularly**: Call `/share-data` whenever your data changes
3. **Clear prompts**: Write detailed render prompts for better widget quality
4. **Handle errors**: Implement retry logic for network failures
5. **Test first**: Test with sample data before production deployment

## Support

For issues or questions, contact the dashboard administrator or check the dashboard documentation.

