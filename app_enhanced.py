import os
import whisper
from moviepy.editor import VideoFileClip, concatenate_videoclips
import requests
import json
import ast
import sys
from datetime import datetime

# ============================================================================
# ZERO-SECRETS ARCHITECTURE
# ============================================================================
# This enhanced version includes:
# - Safe stubbing of external integrations
# - Cost monitoring hooks
# - Maintenance mode detection
# - Graceful fallbacks when APIs are unavailable
# ============================================================================

class Config:
    """Configuration with zero-secrets defaults"""
    
    # Core settings
    PORT = int(os.environ.get('PORT', 8080))
    DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    # Video processing
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')
    VIDEO_INPUT_PATH = os.environ.get('VIDEO_INPUT_PATH', 'input_video.mp4')
    VIDEO_OUTPUT_PATH = os.environ.get('VIDEO_OUTPUT_PATH', 'edited_output.mp4')
    
    # API integration (safe defaults)
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', 'groq-key')
    GROQ_API_URL = os.environ.get('GROQ_API_URL', 'https://api.groq.com/openai/v1/chat/completions')
    
    # Cost protection
    ENABLE_COST_MONITORING = os.environ.get('ENABLE_COST_MONITORING', 'true').lower() == 'true'
    FREE_TIER_LIMIT_MB = int(os.environ.get('FREE_TIER_LIMIT_MB', 500))
    AUTO_SHUTDOWN_ON_LIMIT = os.environ.get('AUTO_SHUTDOWN_ON_LIMIT', 'true').lower() == 'true'
    MAINTENANCE_MODE_ENABLED = os.environ.get('MAINTENANCE_MODE_ENABLED', 'false').lower() == 'true'
    
    # Deployment metadata
    DEPLOYMENT_TARGET = os.environ.get('DEPLOYMENT_TARGET', 'railway')
    DEPLOYMENT_MODE = os.environ.get('DEPLOYMENT_MODE', 'zero-secrets')

    @staticmethod
    def is_api_configured():
        """Check if real API key is configured (not placeholder)"""
        return Config.GROQ_API_KEY and Config.GROQ_API_KEY != 'groq-key' and not Config.GROQ_API_KEY.startswith('placeholder')


class CostMonitor:
    """Monitor resource usage and trigger maintenance mode if needed"""
    
    @staticmethod
    def check_resource_usage():
        """Check if we're approaching resource limits"""
        if not Config.ENABLE_COST_MONITORING:
            return True, "Monitoring disabled"
        
        try:
            # In production, this would query actual Railway/platform metrics
            # For now, we'll implement a simple file-based check
            import psutil
            
            # Get current memory usage
            memory_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            
            if memory_mb > Config.FREE_TIER_LIMIT_MB:
                return False, f"Memory usage {memory_mb:.0f}MB exceeds limit {Config.FREE_TIER_LIMIT_MB}MB"
            
            return True, f"Resource usage OK ({memory_mb:.0f}MB / {Config.FREE_TIER_LIMIT_MB}MB)"
        
        except Exception as e:
            # If monitoring fails, assume OK
            return True, f"Monitoring error (assuming OK): {str(e)}"
    
    @staticmethod
    def trigger_maintenance_mode():
        """Activate maintenance mode and prepare for migration"""
        print("\n" + "="*70)
        print("⚠️  MAINTENANCE MODE TRIGGERED")
        print("="*70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Reason: Free tier limit exceeded")
        print(f"Action: Deploying maintenance page")
        print(f"Next: Migration to Coolify recommended")
        print("="*70 + "\n")
        
        # Log to file for monitoring
        with open('maintenance_mode.log', 'a') as f:
            f.write(f"{datetime.now().isoformat()} - Maintenance mode triggered\n")
        
        # In production, this would:
        # 1. Deploy maintenance.html to Railway
        # 2. Shutdown main service
        # 3. Trigger migration process
        # 4. Send notifications
        
        print("📄 Maintenance page: maintenance.html")
        print("📋 Migration guide: COOLIFY_MIGRATION.md")
        print("🔧 Support docs: COOLIFY_SUPPORT.md")


def transcribe_video(video_path, model_name="base"):
    """Transcribe video using Whisper"""
    print(f"🎙️  Transcribing video with Whisper model: {model_name}")
    
    model = whisper.load_model(model_name)
    audio_path = "temp_audio.wav"
    
    # Extract audio using ffmpeg
    os.system(f"ffmpeg -i {video_path} -ar 16000 -ac 1 -b:a 64k -f mp3 {audio_path} -y 2>/dev/null")
    
    result = model.transcribe(audio_path)
    transcription = []
    
    for segment in result['segments']:
        transcription.append({
            'start': segment['start'],
            'end': segment['end'],
            'text': segment['text'].strip()
        })
    
    print(f"✅ Transcription complete: {len(transcription)} segments")
    return transcription


def get_relevant_segments_stubbed(transcript, user_query):
    """
    STUBBED VERSION: Return mock segments without calling external API
    This is used when GROQ_API_KEY is not configured
    """
    print("\n" + "="*70)
    print("⚠️  STUB MODE: Using mock AI responses (GROQ_API_KEY not configured)")
    print("="*70)
    print("To enable real AI processing:")
    print("1. Get API key from: https://console.groq.com/keys")
    print("2. Set environment variable: GROQ_API_KEY=gsk_your_key_here")
    print("3. Redeploy application")
    print("="*70 + "\n")
    
    # Return mock segments based on transcript length
    # In a real stub, we might use simple keyword matching
    mock_conversations = []
    
    if len(transcript) > 0:
        # Take first few segments as a mock "relevant" clip
        total_segments = len(transcript)
        
        if total_segments >= 3:
            mock_conversations.append({
                'start': transcript[0]['start'],
                'end': transcript[2]['end']
            })
        
        if total_segments >= 6:
            mock_conversations.append({
                'start': transcript[3]['start'],
                'end': transcript[5]['end']
            })
    
    print(f"🎭 Mock response generated: {len(mock_conversations)} conversations")
    return mock_conversations


def get_relevant_segments(transcript, user_query):
    """Get relevant segments using Groq API (or stub if not configured)"""
    
    # Check if API is configured
    if not Config.is_api_configured():
        return get_relevant_segments_stubbed(transcript, user_query)
    
    # Real API call
    print(f"🤖 Calling Groq API for AI-powered segment selection")
    
    prompt = f"""You are an expert video editor who can read video transcripts and perform video editing. Given a transcript with segments, your task is to identify all the conversations related to a user query. Follow these guidelines when choosing conversations. A group of continuous segments in the transcript is a conversation.

Guidelines:
1. The conversation should be relevant to the user query. The conversation should include more than one segment to provide context and continuity.
2. Include all the before and after segments needed in a conversation to make it complete.
3. The conversation should not cut off in the middle of a sentence or idea.
4. Choose multiple conversations from the transcript that are relevant to the user query.
5. Match the start and end time of the conversations using the segment timestamps from the transcript.
6. The conversations should be a direct part of the video and should not be out of context.

Output format: {{ "conversations": [{{"start": "s1", "end": "e1"}}, {{"start": "s2", "end": "e2"}}] }}

Transcript:
{transcript}

User query:
{user_query}"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Config.GROQ_API_KEY}"
    }

    data = {
        "messages": [
            {
                "role": "system",
                "content": prompt
            }
        ],
        "model": "llama-3.1-70b-versatile",
        "temperature": 1,
        "max_tokens": 1024,
        "top_p": 1,
        "stream": False,
        "stop": None
    }
    
    try:
        response = requests.post(Config.GROQ_API_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        response_data = response.json()["choices"][0]["message"]["content"]
        conversations = ast.literal_eval(response_data)["conversations"]
        
        print(f"✅ AI processing complete: {len(conversations)} conversations found")
        return conversations
        
    except requests.exceptions.RequestException as e:
        print(f"❌ API call failed: {str(e)}")
        print("Falling back to stub mode...")
        return get_relevant_segments_stubbed(transcript, user_query)
    except Exception as e:
        print(f"❌ Error processing API response: {str(e)}")
        print("Falling back to stub mode...")
        return get_relevant_segments_stubbed(transcript, user_query)


def edit_video(original_video_path, segments, output_video_path, fade_duration=0.5):
    """Edit video by concatenating segments"""
    print(f"✂️  Editing video with {len(segments)} segments")
    
    video = VideoFileClip(original_video_path)
    clips = []
    
    for seg in segments:
        start = seg['start']
        end = seg['end']
        clip = video.subclip(start, end).fadein(fade_duration).fadeout(fade_duration)
        clips.append(clip)
    
    if clips:
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")
        print(f"✅ Edited video saved to {output_video_path}")
    else:
        print("⚠️  No segments to include in the edited video.")


def main():
    """Main function with zero-secrets architecture"""
    
    print("\n" + "="*70)
    print("🎬 AFRO-CLIPZ - AI Video Clipping")
    print("="*70)
    print(f"Deployment: {Config.DEPLOYMENT_TARGET} ({Config.DEPLOYMENT_MODE} mode)")
    print(f"Whisper Model: {Config.WHISPER_MODEL}")
    print(f"API Configured: {'Yes ✅' if Config.is_api_configured() else 'No ⚠️ (using stubs)'}")
    print("="*70 + "\n")
    
    # Check maintenance mode
    if Config.MAINTENANCE_MODE_ENABLED:
        print("⚠️  Maintenance mode is ENABLED - exiting")
        print("📄 Serving: maintenance.html")
        sys.exit(0)
    
    # Check resource usage
    ok, message = CostMonitor.check_resource_usage()
    print(f"💰 Resource Check: {message}")
    
    if not ok and Config.AUTO_SHUTDOWN_ON_LIMIT:
        CostMonitor.trigger_maintenance_mode()
        sys.exit(1)
    
    # Paths
    input_video = Config.VIDEO_INPUT_PATH
    output_video = Config.VIDEO_OUTPUT_PATH
    
    # Check if input video exists
    if not os.path.exists(input_video):
        print(f"❌ Input video not found: {input_video}")
        print("Please provide a video file to process.")
        sys.exit(1)
    
    # User Query
    user_query = os.environ.get('USER_QUERY', "Find all clips where there is discussion around GPT-4 Turbo")
    print(f"🔍 Query: {user_query}\n")
    
    # Step 1: Transcribe
    print("Step 1: Transcribing video...")
    transcription = transcribe_video(input_video, model_name=Config.WHISPER_MODEL)
    
    # Step 2: Get relevant segments
    print("\nStep 2: Finding relevant segments...")
    relevant_segments = get_relevant_segments(transcription, user_query)
    
    # Step 3: Edit Video
    print("\nStep 3: Editing video...")
    edit_video(input_video, relevant_segments, output_video)
    
    print("\n" + "="*70)
    print("✅ Processing complete!")
    print(f"📹 Output: {output_video}")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
