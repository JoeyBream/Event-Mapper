from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Import your event functions
from event_recommender import get_upcoming_events, format_events_for_llm, generate_recommendations

load_dotenv()

app = Flask(__name__)

# Your existing constants
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Store user contexts (in production, use a database)
user_contexts = {}


def get_user_context(session_id):
    """Get or create user context"""
    if session_id not in user_contexts:
        user_contexts[session_id] = {
            'conversation_history': [],
            'preferred_genres': [],
            'first_interaction': True,
            'last_active': datetime.now()
        }
    return user_contexts[session_id]


def extract_genres_from_message(message):
    """Extract music genres mentioned in the message"""
    genres = []
    genre_keywords = {
        'techno': ['techno', 'tech'],
        'house': ['house', 'deep house', 'tech house'],
        'drum and bass': ['dnb', 'drum and bass', 'jungle'],
        'dubstep': ['dubstep', 'bass'],
        'trance': ['trance', 'progressive'],
        'ambient': ['ambient', 'chill'],
        'breakbeat': ['breaks', 'breakbeat']
    }

    message_lower = message.lower()
    for genre, keywords in genre_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            genres.append(genre)

    return genres


@app.route('/')
def index():
    """Serve the chat interface"""
    # You would save the HTML as a separate file, but for demo purposes:
    print("Current directory:", os.getcwd())
    print("HTML file exists:", os.path.exists('music_friend_chat.html'))
    with open('music_friend_chat.html', 'r') as f:
        return f.read()

@app.route('/test')
def test():
    return "Flask is working!"


@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])

        session_id = request.remote_addr
        context = get_user_context(session_id)
        context['conversation_history'] = conversation_history
        context['last_active'] = datetime.now()

        mentioned_genres = extract_genres_from_message(user_message)
        for genre in mentioned_genres:
            if genre not in context['preferred_genres']:
                context['preferred_genres'].append(genre)

        # Use your actual event functions
        try:
            events = get_upcoming_events()
            events_text = format_events_for_llm(events)

            if not events_text or events_text == "No events found.":
                response_text = "No events coming up right now"
            else:
                response_text = generate_recommendations(user_message, events_text, context)

        except Exception as e:
            print(f"Error fetching events: {e}")
            response_text = "Having trouble getting events right now"

        context['first_interaction'] = False

        return jsonify({
            'response': response_text,
            'success': True
        })

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'response': "Something went wrong",
            'success': False
        }), 500

if __name__ == '__main__':
    print("🎵 Starting Music Friend Web Server...")
    print("📱 Open http://localhost:5000 to chat!")
    app.run(host='0.0.0.0', port=5000, debug=True)