from flask import Flask, render_template, request, redirect, url_for, send_file, Response
from youtubesearchpython import VideosSearch
import yt_dlp
import os
import json
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def extract_youtube_cookies():
    """
    Extracts cookies for youtube.com using Playwright.
    Returns a dictionary of cookies if the user is logged in, otherwise None.
    """
    try:
        with sync_playwright() as p:
            # Launch a browser instance
            browser = p.chromium.launch(headless=False)  # Set headless=False to see the browser
            context = browser.new_context()
            page = context.new_page()

            # Navigate to YouTube
            page.goto('https://www.youtube.com')

            # Wait for the page to load (you can add more sophisticated waiting logic)
            page.wait_for_timeout(5000)  # Wait for 5 seconds

            # Extract cookies for youtube.com
            cookies = context.cookies()
            youtube_cookies = {cookie['name']: cookie['value'] for cookie in cookies if 'youtube.com' in cookie['domain']}

            # Close the browser
            browser.close()

            return youtube_cookies if youtube_cookies else None
    except Exception as e:
        print(f"Error extracting cookies: {e}")
        return None

def download_with_yt_dlp(url, download_type, progress_callback=None):
    """
    Downloads a YouTube video or audio using yt-dlp.
    download_type: 'video' or 'audio'
    progress_callback: A callback function to report progress.
    Returns the downloaded filename.
    """
    # Try to extract cookies dynamically
    cookies = extract_youtube_cookies()

    if download_type == 'video':
        ydl_opts = {
            'format': 'best[ext=mp4][vcodec!=none][acodec!=none]',
            'outtmpl': '%(id)s.%(ext)s',
            'progress_hooks': [progress_callback] if progress_callback else []
        }
    elif download_type == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'progress_hooks': [progress_callback] if progress_callback else []
        }
    else:
        raise ValueError("Invalid download type specified.")

    # Use extracted cookies if available, otherwise fall back to cookies.txt
    if cookies:
        ydl_opts['cookiefile'] = None
        ydl_opts['cookies'] = cookies
    else:
        ydl_opts['cookiefile'] = 'cookies.txt'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename

def get_video_info(url):
    """
    Extracts video information without downloading using yt-dlp.
    """
    # Try to extract cookies dynamically
    cookies = extract_youtube_cookies()

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True
    }

    # Use extracted cookies if available, otherwise fall back to cookies.txt
    if cookies:
        ydl_opts['cookiefile'] = None
        ydl_opts['cookies'] = cookies
    else:
        ydl_opts['cookiefile'] = 'cookies.txt'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info

# -------------------------------------------------------------------
# Route: Home page – a single form for either a URL or a search term.
@app.route('/')
def index():
    return render_template('index.html')

# -------------------------------------------------------------------
# Route: Process the input from the home page.
@app.route('/process', methods=['POST'])
def process():
    user_input = request.form.get('query')
    if not user_input:
        return redirect(url_for('index'))
    
    # If the input starts with "http://" or "https://", treat it as a URL.
    if user_input.startswith("http://") or user_input.startswith("https://"):
        return redirect(url_for('video', url=user_input))
    else:
        # Otherwise, treat the input as a search term.
        videos_search = VideosSearch(user_input, limit=10)
        results = videos_search.result()['result']
        return render_template('results.html', results=results)

# -------------------------------------------------------------------
# Route: Video page that shows details and download links.
@app.route('/video')
def video():
    video_url = request.args.get('url')
    if not video_url:
        return redirect(url_for('index'))
    try:
        info = get_video_info(video_url)
    except Exception as e:
        return f"Error retrieving video info: {e}", 500
    return render_template('video.html', info=info)

# -------------------------------------------------------------------
# Download route: Downloads video or audio.
@app.route('/download/<video_id>/<download_type>')
def download(video_id, download_type):
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    def progress_hook(d):
        if d['status'] == 'downloading':
            progress = d['_percent_str']
            print(f"Download progress: {progress}")

    try:
        filename = download_with_yt_dlp(video_url, download_type, progress_hook)
    except Exception as e:
        return f"Download error: {e}", 500

    if not os.path.exists(filename):
        return "Downloaded file not found.", 404

    return send_file(filename, as_attachment=True, download_name=os.path.basename(filename))

# -------------------------------------------------------------------
# Optional cleanup route to remove downloaded files.
@app.route('/cleanup')
def cleanup():
    for file in os.listdir('.'):
        if file.endswith('.mp4') or file.endswith('.webm') or file.endswith('.m4a'):
            os.remove(file)
    return render_template('done.html')

if __name__ == '__main__':
    app.run(debug=True)
