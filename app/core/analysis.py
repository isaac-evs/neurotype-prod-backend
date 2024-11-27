import re

# Define keywords for each emotion
EMOTION_KEYWORDS = {
    "happy": ["happy", "joyful", "elated", "refreshing", "shining"],
    "calm": ["calm", "relaxed", "peaceful", "serene"],
    "sad": ["sad", "down", "unhappy", "depressed"],
    "upset": ["upset", "angry", "frustrated", "irritated"]
}

def analyze_text(text: str):
    # Preprocess the text
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)

    # Initialize counts
    emotion_counts = {emotion: 0 for emotion in EMOTION_KEYWORDS}

    # Count occurrences
    for word in words:
        for emotion, keywords in EMOTION_KEYWORDS.items():
            if word in keywords:
                emotion_counts[emotion] += 1

    return emotion_counts
