import streamlit as st
from dotenv import load_dotenv
load_dotenv() ##load all the nevironment variables
import os
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from xml.etree.ElementTree import ParseError

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

prompt="""You are Yotube video summarizer. You will be taking the transcript text
and summarizing the entire video and providing the important summary in points
within 250 words. Please provide the summary of the text given here:  """


def get_video_id(youtube_url):
    """
    Function to extract video id from youtube url
    """
    if "v=" in youtube_url:
        video_id = youtube_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_url:
        video_id = youtube_url.split("youtu.be/")[1].split("?")[0]
    else:
        video_id = None
    return video_id

## getting the transcript data from yt videos
def extract_transcript_details(youtube_video_url):
    try:
        video_id=get_video_id(youtube_video_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Try human-created transcripts first
        try:
            transcript_text = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["en", "en-US", "en-GB"]
            )
        except NoTranscriptFound:
            # Fallback: try generated transcripts
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            try:
                transcript_obj = transcripts.find_transcript(["en", "en-US", "en-GB"])
            except NoTranscriptFound:
                transcript_obj = transcripts.find_generated_transcript(["en"])
            transcript_text = transcript_obj.fetch()

        # Build plain text
        transcript = " ".join([i.get("text", "") for i in transcript_text if i.get("text")])
        return transcript.strip() or None

    except (TranscriptsDisabled, NoTranscriptFound, ParseError):
        st.error("Transcript unavailable for this video. It may be disabled, restricted, or not provided.")
        return None
    except Exception as e:
        st.error(f"Failed to retrieve transcript: {e}")
        return None
    
## getting the summary based on Prompt from Google Gemini Pro
def generate_gemini_content(transcript_text,prompt):

    model=genai.GenerativeModel("gemini-pro")
    response=model.generate_content(prompt+transcript_text)
    return response.text

st.title("YouTube Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    video_id = get_video_id(youtube_link)
    if video_id:
        print(video_id)
        st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

if st.button("Get Detailed Notes"):
    video_id = get_video_id(youtube_link) if youtube_link else None
    if not video_id:
        st.error("Please enter a valid YouTube URL.")
    else:
        with st.spinner("Fetching transcript..."):
            transcript_text=extract_transcript_details(youtube_link)

        if transcript_text:
            with st.spinner("Generating summary..."):
                summary=generate_gemini_content(transcript_text,prompt)
            st.markdown("## Detailed Notes:")
            st.write(summary)
        else:
            st.error("Could not retrieve transcript for this video.")
