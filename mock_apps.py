"""
Multiple mock 3rd party apps to demonstrate integration with the Dashboard.
Creates apps with different layouts and content.
"""

import requests
import json
import time

DASHBOARD_URL = "http://localhost:8000"
REGISTRATION_TOKEN = "demo_registration_token_123"  # Should match config.py default


def register_app(app_name):
    """Register an app with the dashboard."""
    url = f"{DASHBOARD_URL}/register"
    payload = {
        "registration_token": REGISTRATION_TOKEN,
        "app_name": app_name
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Registered: {app_name}")
        return data['integration_token']
    else:
        print(f"✗ Registration failed for {app_name}: {response.text}")
        return None


def share_data(integration_token, data, render_prompt, app_name):
    """Share data with the dashboard."""
    url = f"{DASHBOARD_URL}/share-data"
    payload = {
        "integration_token": integration_token,
        "data": data,
        "render_prompt": render_prompt
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"✓ Data shared: {app_name}")
        return True
    else:
        print(f"✗ Failed to share data for {app_name}: {response.text}")
        return False


def main():
    print("=== Creating Multiple Mock Apps ===\n")
    
    apps = []
    
    # First batch of apps
    print("First Batch Apps:")
    print("-" * 50)
    
    # App 1: System Status
    token1 = register_app("System Status")
    if token1:
        share_data(token1, {
            "status": "Operational",
            "uptime": "99.9%",
            "active_users": 1247,
            "cpu_usage": 23,
            "memory_usage": 67
        }, "Create a compact system status widget showing operational status with a green indicator, uptime percentage prominently displayed, active users count, and CPU/memory usage with a small progress bar. Use a dark theme with green accent colors for good/operational status. Make it clean and minimal.", 
        "System Status")
        apps.append(token1)
    
    # App 2: Stock Price
    token2 = register_app("Stock Tracker")
    if token2:
        share_data(token2, {
            "symbol": "AAPL",
            "price": 178.45,
            "change": 2.34,
            "change_percent": 1.33,
            "volume": 45234567,
            "market_cap": "2.8T"
        }, "Create a stock price widget showing the stock symbol prominently, current price in large bold font, change amount and percentage (green for positive, red for negative), trading volume, and market cap. Use a professional finance app style with good typography hierarchy. Include up/down arrows based on the change direction.", 
        "Stock Tracker")
        apps.append(token2)
    
    # App 3: Calendar Events
    token3 = register_app("Today's Calendar")
    if token3:
        share_data(token3, {
            "date": "2024-12-19",
            "events": [
                {"time": "09:00", "title": "Team Standup", "type": "meeting"},
                {"time": "14:30", "title": "Client Presentation", "type": "meeting"},
                {"time": "16:00", "title": "Code Review", "type": "task"}
            ],
            "total_events": 3
        }, "Create a calendar widget showing today's date and a list of events with times. Each event should show the time in a smaller font and the title prominently. Use different colors or icons to distinguish meeting types (meetings vs tasks). Make it clean and easy to scan. Include a subtle background or border around each event.", 
        "Today's Calendar")
        apps.append(token3)
    
    time.sleep(0.5)  # Small delay between batches
    
    # Second batch
    print("\nSecond Batch App:")
    print("-" * 50)
    
    token4 = register_app("Analytics Dashboard")
    if token4:
        share_data(token4, {
            "period": "Last 30 Days",
            "metrics": {
                "page_views": 125430,
                "unique_visitors": 34210,
                "bounce_rate": 42.3,
                "avg_session": "3m 45s",
                "conversions": 1245,
                "revenue": "$45,230"
            },
            "trend": "up",
            "trend_percent": 12.5
        }, "Create a comprehensive analytics dashboard widget showing multiple metrics in a grid layout. Display page views, unique visitors, bounce rate, average session duration, conversions, and revenue. Use large numbers for key metrics with smaller labels. Include a trend indicator (up/down arrow) and percentage. Use a professional analytics style with good spacing and visual hierarchy. Consider using cards or sections for different metric groups.", 
        "Analytics Dashboard")
        apps.append(token4)
    
    time.sleep(0.5)
    
    # Third batch
    print("\nThird Batch Apps:")
    print("-" * 50)
    
    # App 5: Weather
    token5 = register_app("Weather")
    if token5:
        share_data(token5, {
            "city": "San Francisco",
            "temperature": 72,
            "condition": "Sunny",
            "humidity": 45,
            "wind_speed": 8,
            "forecast": [
                {"day": "Today", "high": 72, "low": 58, "condition": "Sunny"},
                {"day": "Tomorrow", "high": 68, "low": 55, "condition": "Partly Cloudy"}
            ]
        }, "Create a beautiful weather widget showing the temperature prominently in large font, Use the real current wheather in Lviv city. Style the widget to follow the current wather foreacast Make it visually appealing with rounded corners and good spacing.", 
        "Weather")
        apps.append(token5)
    
    # App 6: GitHub Activity
    token6 = register_app("GitHub Activity")
    if token6:
        share_data(token6, {
            "username": "developer123",
            "today_commits": 8,
            "this_week": 32,
            "repositories": 12,
            "pull_requests": 3,
            "streak": 15
        }, "Create a GitHub activity widget showing developer stats. Display commit count for today and this week prominently, number of repositories, open pull requests, and current streak. Use GitHub's signature colors (dark theme with purple/green accents). Include small icons or visual elements that represent GitHub. Make it look modern and developer-friendly.", 
        "GitHub Activity")
        apps.append(token6)
    
    # App 7: Task List
    token7 = register_app("Tasks")
    if token7:
        share_data(token7, {
            "total_tasks": 8,
            "completed": 5,
            "pending": 3,
            "urgent": 1,
            "tasks": [
                {"id": 1, "title": "Review pull request", "status": "pending", "priority": "high"},
                {"id": 2, "title": "Update documentation", "status": "completed", "priority": "medium"},
                {"id": 3, "title": "Fix bug #1234", "status": "pending", "priority": "urgent"}
            ]
        }, "Create a task list widget showing total tasks, completed count, pending count, and urgent tasks. Display a list of tasks with checkboxes (checked for completed, unchecked for pending). Show task titles clearly, and use color coding for priorities (red for urgent, orange for high, blue for medium). Include a progress indicator showing completed vs total. Make it clean and actionable.", 
        "Tasks")
        apps.append(token7)
    
    time.sleep(0.5)
    
    # Additional apps - diverse content
    print("\nAdditional Apps:")
    print("-" * 50)
    
    # App 8: Time Tracker
    token8 = register_app("Time Tracker")
    if token8:
        share_data(token8, {
            "today_hours": 6.5,
            "this_week": 32.5,
            "this_month": 142,
            "projects": [
                {"name": "Dashboard", "hours": 4.5, "color": "#4CAF50"},
                {"name": "API Integration", "hours": 2.0, "color": "#2196F3"}
            ],
            "current_task": "Dashboard Development"
        }, "Create a time tracking widget showing today's hours prominently, weekly and monthly totals, and a list of active projects with hours worked and color-coded bars. Include the current task being tracked. Use a clean, professional design with progress indicators. Show time in hours with one decimal place.", 
        "Time Tracker")
        apps.append(token8)
    
    # App 9: Server Status
    token9 = register_app("Server Status")
    if token9:
        share_data(token9, {
            "servers": [
                {"name": "Web Server", "status": "online", "cpu": 45, "memory": 62, "uptime": "45d"},
                {"name": "DB Server", "status": "online", "cpu": 28, "memory": 51, "uptime": "45d"},
                {"name": "Cache Server", "status": "online", "cpu": 12, "memory": 34, "uptime": "45d"}
            ],
            "total_servers": 3,
            "online": 3
        }, "Create a server monitoring widget showing multiple servers with their status (online/offline), CPU usage, memory usage, and uptime. Use status indicators (green for online, red for offline), progress bars for CPU/memory, and show uptime in days. Use a dark theme with green/red accents. Make it compact and scannable.", 
        "Server Status")
        apps.append(token9)
    
    # App 10: News Feed
    token10 = register_app("News Feed")
    if token10:
        share_data(token10, {
            "articles": [
                {"title": "AI Breakthrough in Language Models", "source": "Tech News", "time": "2h ago", "category": "Technology"},
                {"title": "New Framework Released", "source": "Dev Blog", "time": "5h ago", "category": "Development"},
                {"title": "Security Update Required", "source": "Security", "time": "1d ago", "category": "Security"}
            ],
            "unread": 3
        }, "Create a news feed widget displaying a list of articles with titles, sources, time ago, and category badges. Show unread count. Each article should be clickable-looking with hover effects. Use a clean list design with good spacing. Highlight unread items subtly. Include category color coding.", 
        "News Feed")
        apps.append(token10)
    
    # App 11: Sales Dashboard
    token11 = register_app("Sales Dashboard")
    if token11:
        share_data(token11, {
            "today_revenue": 12450,
            "month_revenue": 245680,
            "target": 300000,
            "growth": 12.5,
            "top_product": "Product A",
            "sales_count": 156
        }, "Create a sales dashboard widget showing today's revenue prominently, monthly revenue, progress toward monthly target, growth percentage (with up/down indicator), top-selling product, and total sales count. Use professional finance styling with large numbers, percentage indicators, and progress bars. Use green for positive growth, professional color scheme.", 
        "Sales Dashboard")
        apps.append(token11)
    
    # App 12: Team Activity
    token12 = register_app("Team Activity")
    if token12:
        share_data(token12, {
            "team_members": [
                {"name": "Alice", "status": "active", "task": "Working on feature"},
                {"name": "Bob", "status": "away", "task": "In meeting"},
                {"name": "Charlie", "status": "active", "task": "Code review"}
            ],
            "active_count": 2,
            "total_count": 3
        }, "Create a team activity widget showing team members with their names, online status (active/away), and current task. Use status indicators (green dot for active, yellow for away). Show active vs total count. Use a compact card design with avatars or initials. Make it feel like a team presence indicator.", 
        "Team Activity")
        apps.append(token12)
    
    print("\n" + "="*50)
    print(f"✓ Successfully created {len(apps)} apps!")
    print(f"Visit {DASHBOARD_URL} to see the dashboard.")
    print("="*50)


if __name__ == "__main__":
    main()

