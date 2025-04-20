import base64
from openai import OpenAI
import os
import json
import datetime
from pydub import AudioSegment
import math
import concurrent.futures
import shutil
import uuid

from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

# --- Configuration ---
# Load API Key from environment variable for security
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    # For deployment, it's crucial this variable is set.
    print("CRITICAL WARNING: GEMINI_API_KEY environment variable not set. Transcription will fail.")
    # Optionally, raise an error to prevent the app from starting without a key:
    # raise ValueError("GEMINI_API_KEY environment variable not set.")

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
TEMP_FOLDER = "stt_webapp_temp" # Temporary folder for uploads and chunks

# --- Initialize OpenAI Client ---
# Ensure the client is initialized *after* the API_KEY is potentially checked
client = OpenAI(
    api_key=API_KEY, # Use the variable loaded from environment
    base_url=BASE_URL
)

# --- Initialize FastAPI App ---
app = FastAPI()

# --- Setup Templates ---
# The directory should be relative to main.py's location inside the container (/app)
templates = Jinja2Templates(directory="templates")

# --- Ensure Temp Folder Exists ---
os.makedirs(TEMP_FOLDER, exist_ok=True)

# --- Helper Functions (Adapted from your script) ---

def split_audio(file_path, chunk_length_ms=30*60*1000):
    """
    Split an audio file into chunks of specified length.
    Saves chunks to the TEMP_FOLDER.
    """
    print(f"Loading audio file: {file_path}")
    try:
        audio = AudioSegment.from_file(file_path)
    except Exception as e:
        print(f"Error loading audio file {file_path}: {e}")
        raise ValueError(f"Could not process audio file. Ensure it's a valid format. Error: {e}")

    file_ext = os.path.splitext(file_path)[1].lower()
    # Use mp3 for export regardless of input, as Gemini API might prefer it
    export_format = 'mp3'

    duration_ms = len(audio)

    # Generate a unique subfolder for this processing job's chunks
    job_id = str(uuid.uuid4())
    chunk_folder = os.path.join(TEMP_FOLDER, job_id)
    os.makedirs(chunk_folder, exist_ok=True)
    print(f"Created temporary chunk folder: {chunk_folder}")

    chunk_files = []

    if duration_ms <= chunk_length_ms:
        print(f"Audio file is shorter than {chunk_length_ms/60000} minutes, processing as a single chunk")
        chunk_path = os.path.join(chunk_folder, f"chunk_0.{export_format}")
        try:
            audio.export(chunk_path, format=export_format)
            chunk_files.append(chunk_path)
        except Exception as e:
            print(f"Error exporting single chunk: {e}")
            shutil.rmtree(chunk_folder) # Clean up job folder on error
            raise IOError(f"Failed to export audio chunk: {e}")
    else:
        chunks = math.ceil(duration_ms / chunk_length_ms)
        print(f"Splitting {os.path.basename(file_path)} into {chunks} chunks of {chunk_length_ms/60000} minutes each")

        for i in range(chunks):
            start_ms = i * chunk_length_ms
            end_ms = min((i + 1) * chunk_length_ms, duration_ms)
            chunk = audio[start_ms:end_ms]
            chunk_path = os.path.join(chunk_folder, f"chunk_{i}.{export_format}")
            try:
                chunk.export(chunk_path, format=export_format)
                chunk_files.append(chunk_path)
            except Exception as e:
                print(f"Error exporting chunk {i}: {e}")
                # Attempt cleanup even if some exports failed
                shutil.rmtree(chunk_folder) # Clean up job folder on error
                raise IOError(f"Failed to export audio chunk {i}: {e}")

    return chunk_files, chunk_folder # Return folder path for cleanup

def transcribe_chunk(chunk_path):
    """
    Transcribe a single audio chunk using Gemini API.
    """
    print(f"Transcribing chunk: {chunk_path}")
    file_format = os.path.splitext(chunk_path)[1].replace('.', '').lower()

    try:
        with open(chunk_path, "rb") as audio_file:
            base64_audio = base64.b64encode(audio_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error reading chunk file {chunk_path}: {e}")
        return f"# Transcription Error\n\nCould not read audio chunk file: {os.path.basename(chunk_path)}\nError: {e}"

    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model="gemini-1.5-flash", # Using flash model as specified
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """<role>You are a professional transcriber.</role><task>Transcribe this audio recording completely and accurately. Include all spoken content, maintain proper punctuation, and identify different speakers if possible (e.g., Speaker 1:, Speaker 2:). If there are any unclear sections, indicate them with [unclear]. Preserve any technical terms, names, or specialized vocabulary as accurately as possible.</task><output_format>Provide the transcription directly as plain text. Start from the very beginning of the audio and include everything until the end.</output_format>""",
                            },
                            # { # Using file_uri is not supported by the chat completions endpoint via the OpenAI compatibility layer
                            #     "type": "audio_file",
                            #     "file_uri": chunk_path
                            # }
                            { # Use the base64 encoded audio data instead
                                "type": "input_audio",
                                "input_audio": {
                                    "data": base64_audio,
                                    "format": file_format # file_format is determined earlier (likely 'mp3')
                                }
                            }
                        ],
                    }
                ],
            )
            transcription_response = response.choices[0].message.content
            print(f"Successfully transcribed chunk: {os.path.basename(chunk_path)}")
            return transcription_response

        except Exception as e:
            print(f"Attempt {attempt+1} failed for chunk {os.path.basename(chunk_path)}: {str(e)}")
            if attempt < max_attempts - 1:
                print(f"Retrying in 5 seconds...")
                import time
                time.sleep(5)
            else:
                print(f"All attempts failed for chunk {os.path.basename(chunk_path)}")
                return f"# Transcription Failed\n\nFailed to transcribe segment {os.path.basename(chunk_path)} after {max_attempts} attempts.\nError: {str(e)}"

def process_audio_file(audio_path):
    """
    Process an audio file: split, transcribe chunks, combine, and clean up.
    """
    chunk_folder = None # Initialize chunk_folder
    try:
        # Split audio (adjust chunk length if needed, e.g., 10 mins = 10*60*1000)
        # Gemini 1.5 Flash might handle longer audio, test optimal chunk size. Let's keep 30 mins for now.
        chunk_files, chunk_folder = split_audio(audio_path, chunk_length_ms=30*60*1000)

        all_transcriptions = []

        # Sequential processing (safer for API rate limits and debugging)
        for chunk_path in chunk_files:
            transcription = transcribe_chunk(chunk_path)
            all_transcriptions.append(transcription)

        # Combine transcriptions
        if not all_transcriptions:
            return "# Transcription Error\n\nNo segments were transcribed."

        if len(all_transcriptions) > 1:
            combined_text = ""
            for i, transcription in enumerate(all_transcriptions):
                section_header = f"--- Part {i+1} ---\n\n"
                combined_text += section_header + transcription + "\n\n"
        else:
            combined_text = all_transcriptions[0] # Use directly if single chunk

        return combined_text.strip()

    except (ValueError, IOError) as e:
        # Handle errors during splitting/exporting
        print(f"Error during audio processing: {e}")
        return f"# Processing Error\n\n{str(e)}"
    except Exception as e:
        # Catch other unexpected errors
        print(f"Unexpected error during processing: {e}")
        import traceback
        traceback.print_exc()
        return f"# Unexpected Error\n\nAn error occurred during transcription processing: {str(e)}"
    finally:
        # Clean up temporary files and folders
        if chunk_folder and os.path.exists(chunk_folder):
             try:
                 shutil.rmtree(chunk_folder)
                 print(f"Removed temporary chunk folder: {chunk_folder}")
             except Exception as e:
                 print(f"Error removing temporary folder {chunk_folder}: {e}")
        # Clean up the original uploaded file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                print(f"Removed temporary upload file: {audio_path}")
            except Exception as e:
                print(f"Error removing temporary upload file {audio_path}: {e}")


# --- FastAPI Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML upload page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/transcribe/", response_class=PlainTextResponse)
async def transcribe_audio_endpoint(request: Request, audio_file: UploadFile = File(...)):
    """Handles audio file upload, processes it, and returns transcription."""
    if not audio_file:
        return PlainTextResponse("No audio file provided.", status_code=400)

    # Save uploaded file temporarily
    file_id = str(uuid.uuid4())
    original_filename = audio_file.filename or "upload"
    file_ext = os.path.splitext(original_filename)[1] if '.' in original_filename else '.tmp'
    temp_file_path = os.path.join(TEMP_FOLDER, f"{file_id}{file_ext}")

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        print(f"Saved uploaded file temporarily to: {temp_file_path}")
    except Exception as e:
        print(f"Error saving uploaded file: {e}")
        return PlainTextResponse(f"Error saving uploaded file: {e}", status_code=500)
    finally:
        await audio_file.close() # Ensure file handle is closed

    # Process the saved audio file
    print(f"Processing audio file: {temp_file_path}")
    transcription_result = process_audio_file(temp_file_path) # This function now handles cleanup internally

    # Return the transcription as plain text
    return PlainTextResponse(content=transcription_result)

# --- Optional: Add endpoint to clear temp folder (for maintenance) ---
@app.post("/clear_temp/", response_class=JSONResponse)
async def clear_temp_folder():
    """Removes and recreates the temporary folder."""
    try:
        if os.path.exists(TEMP_FOLDER):
            shutil.rmtree(TEMP_FOLDER)
            print(f"Removed temporary folder: {TEMP_FOLDER}")
        os.makedirs(TEMP_FOLDER, exist_ok=True)
        print(f"Recreated temporary folder: {TEMP_FOLDER}")
        return JSONResponse(content={"message": "Temporary folder cleared successfully."})
    except Exception as e:
        print(f"Error clearing temporary folder: {e}")
        return JSONResponse(content={"error": f"Failed to clear temporary folder: {e}"}, status_code=500)


# --- Run Command (for local testing) ---
# You would typically run this using: uvicorn stt_webapp.main:app --reload --port 8000
# The following block allows running directly with `python stt_webapp/main.py` for simple testing
if __name__ == "__main__":
    # Updated messages for running locally vs. deployment context
    print("Starting Uvicorn server for local testing on http://127.0.0.1:8000")
    print("Access the upload interface at http://127.0.0.1:8000/")
    print(f"Temporary files will be stored in: {os.path.abspath(TEMP_FOLDER)}")
    print("IMPORTANT: Ensure ffmpeg is installed and accessible in your system PATH for pydub.")
    if not API_KEY:
         print("WARNING: GEMINI_API_KEY environment variable is not set. Set it before running for transcription to work.")
    # The uvicorn.run() call is primarily for local testing.
    # For deployment, use: gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:$PORT
    uvicorn.run(app, host="127.0.0.1", port=8000)
