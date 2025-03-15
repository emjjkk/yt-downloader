from flask import Flask, render_template, request, redirect, url_for, send_file, Response
from youtubesearchpython import VideosSearch
import yt_dlp
import os
import json

app = Flask(__name__)

def download_with_yt_dlp(url, download_type, progress_callback=None):
    """
    Downloads a YouTube video or audio using yt-dlp.
    download_type: 'video' or 'audio'
    progress_callback: A callback function to report progress.
    Returns the downloaded filename.
    """
    if download_type == 'video':
        ydl_opts = {
            'cookiefile': 'cookies.txt',
            'format': 'best[ext=mp4][vcodec!=none][acodec!=none]',
            'outtmpl': '%(id)s.%(ext)s',
            'progress_hooks': [progress_callback] if progress_callback else []
        }
    elif download_type == 'audio':
        ydl_opts = {
            'cookiefile': 'cookies.txt',
            'format': 'bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'progress_hooks': [progress_callback] if progress_callback else []
        }
    else:
        raise ValueError("Invalid download type specified.")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
    return filename

def get_video_info(url):
    """
    Extracts video information without downloading using yt-dlp.
    """
    ydl_opts = {
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'skip_download': True,
        'no_warnings': True
    }
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
