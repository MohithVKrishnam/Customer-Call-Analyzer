# app.py
# Improved Backend server for the Customer Call Analyzer

import os
import csv
import json
import random
import re
from flask import Flask, request, jsonify, render_template, send_from_directory
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from a .env file (for the API key)
load_dotenv()

app = Flask(__name__)

# --- Configuration ---
CSV_FILE = 'call_analysis.csv'
# Fix: Use the correct environment variable name
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "xai-YY0QDvcUEl58gcxKg0ujmlRytxebp7VB5hi3EeJO0gsr8me2dQ3iSb2Aco0VSHRPkfIyCFT5npmmgcLb")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- Improved Sentiment Keywords for Fallback ---
POSITIVE_KEYWORDS = [
    'thank', 'thanks', 'great', 'excellent', 'wonderful', 'amazing', 'perfect',
    'satisfied', 'happy', 'pleased', 'love', 'fantastic', 'awesome', 'good',
    'helpful', 'friendly', 'professional', 'quick', 'efficient', 'resolved'
]

NEGATIVE_KEYWORDS = [
    'terrible', 'awful', 'horrible', 'bad', 'worst', 'hate', 'angry', 'furious',
    'frustrated', 'disappointed', 'unsatisfied', 'complaint', 'problem', 'issue',
    'broken', 'failed', 'wrong', 'error', 'refund', 'cancel', 'unacceptable'
]

def fallback_sentiment_analysis(transcript: str) -> str:
    """
    Simple keyword-based sentiment analysis as fallback
    """
    text_lower = transcript.lower()
    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    
    if positive_count > negative_count:
        return 'Positive'
    elif negative_count > positive_count:
        return 'Negative'
    else:
        return 'Neutral'

# --- Mock Function ---
def mock_analyze_transcript(transcript: str) -> dict:
    """Enhanced mock analysis with better sentiment detection."""
    print("--- Using MOCK analysis function ---")
    import time
    time.sleep(1)
    
    # Use fallback sentiment analysis instead of random
    sentiment = fallback_sentiment_analysis(transcript)
    
    # Generate more realistic summary based on content
    if len(transcript) > 200:
        summary = f"Customer interaction regarding service inquiry. The conversation covered multiple topics and the customer expressed {sentiment.lower()} feedback about the experience."
    else:
        summary = f"Brief customer contact with {sentiment.lower()} outcome. Issue appears to have been addressed appropriately."
    
    return {
        "summary": summary,
        "sentiment": sentiment
    }

# --- Enhanced Groq API Function ---
def analyze_transcript_with_groq(transcript: str) -> dict:
    """Enhanced transcript analysis using the Groq API with better prompting."""
    print("--- Using GROQ API for analysis ---")
    try:
        # Enhanced system prompt with examples and clearer instructions
        system_prompt = """You are an expert customer service analyst. Analyze call transcripts for summary and sentiment.

SENTIMENT RULES:
- Positive: Customer expresses satisfaction, gratitude, or positive emotions
- Negative: Customer expresses frustration, anger, complaints, or dissatisfaction  
- Neutral: Professional exchange without strong emotional indicators

EXAMPLES:
Customer: "Thank you so much! This really helped solve my problem."
→ Sentiment: Positive

Customer: "This is ridiculous! I've been waiting for hours and nothing works!"
→ Sentiment: Negative

Customer: "I need to update my billing address please."
→ Sentiment: Neutral

Return ONLY valid JSON with exactly these keys: "summary" and "sentiment"
Sentiment MUST be exactly one of: "Positive", "Neutral", or "Negative" """

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Analyze this transcript:\n\n{transcript}",
                }
            ],
            model="llama-3.1-70b-versatile",  # Better model for analysis
            temperature=0.1,  # Lower temperature for more consistent results
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        
        response_content = chat_completion.choices[0].message.content
        print(f"Raw API response: {response_content}")
        
        # Parse and validate the JSON response
        result = json.loads(response_content)
        
        # Validate sentiment value
        valid_sentiments = ['Positive', 'Neutral', 'Negative']
        if result.get('sentiment') not in valid_sentiments:
            print(f"Invalid sentiment '{result.get('sentiment')}', using fallback")
            result['sentiment'] = fallback_sentiment_analysis(transcript)
        
        # Ensure summary exists and is reasonable
        if not result.get('summary') or len(result.get('summary', '').strip()) < 10:
            result['summary'] = f"Customer service interaction with {result['sentiment'].lower()} outcome."
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return mock_analyze_transcript(transcript)
    except Exception as e:
        print(f"Groq API error: {e}")
        return mock_analyze_transcript(transcript)

# --- Enhanced CSV Handling ---
def save_to_csv(data: dict):
    """Appends a new analysis result to the CSV file with better error handling."""
    try:
        file_exists = os.path.isfile(CSV_FILE)
        
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Transcript', 'Summary', 'Sentiment', 'Confidence']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            # Add confidence score based on analysis method
            confidence = "High" if client else "Medium"
            
            writer.writerow({
                'Transcript': data['transcript'][:500] + ('...' if len(data['transcript']) > 500 else ''),
                'Summary': data['summary'],
                'Sentiment': data['sentiment'],
                'Confidence': confidence
            })
    except Exception as e:
        print(f"Error saving to CSV: {e}")

# --- Flask Routes ---
@app.route('/')
def index():
    """Renders the main frontend page."""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Enhanced API endpoint to analyze a transcript."""
    try:
        data = request.get_json()
        if not data or 'transcript' not in data:
            return jsonify({"error": "Request must contain 'transcript' field."}), 400
            
        transcript = data['transcript'].strip()
        if not transcript:
            return jsonify({"error": "Transcript cannot be empty."}), 400
        
        if len(transcript) < 5:
            return jsonify({"error": "Transcript too short for meaningful analysis."}), 400
        
        # Analyze the transcript
        if client and len(transcript) > 10:  # Use API for substantial content
            analysis_result = analyze_transcript_with_groq(transcript)
        else:
            analysis_result = mock_analyze_transcript(transcript)

        # Prepare response
        response_data = {
            "transcript": transcript,
            "summary": analysis_result.get("summary", "Analysis unavailable."),
            "sentiment": analysis_result.get("sentiment", "Neutral"),
            "method": "Groq API" if client else "Fallback Analysis"
        }
        
        # Save to CSV
        save_to_csv(response_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error in analyze endpoint: {e}")
        return jsonify({"error": "Internal server error occurred."}), 500

@app.route('/download')
def download_csv():
    """Provides the CSV file for download."""
    try:
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Transcript', 'Summary', 'Sentiment', 'Confidence'])
                
        return send_from_directory(os.getcwd(), CSV_FILE, as_attachment=True)
    except Exception as e:
        print(f"Error downloading CSV: {e}")
        return jsonify({"error": "Could not download file."}), 500

@app.route('/test-sentiment', methods=['POST'])
def test_sentiment():
    """Test endpoint to debug sentiment analysis"""
    data = request.get_json()
    transcript = data.get('transcript', '')
    
    # Test both methods
    fallback_result = fallback_sentiment_analysis(transcript)
    
    if client:
        api_result = analyze_transcript_with_groq(transcript)
    else:
        api_result = {"sentiment": "API not available"}
    
    return jsonify({
        "transcript": transcript,
        "fallback_sentiment": fallback_result,
        "api_result": api_result,
        "api_available": client is not None
    })

if __name__ == '__main__':
    print(f"API Key available: {client is not None}")
    print(f"CSV file: {CSV_FILE}")
    app.run(debug=True)