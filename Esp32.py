from flask import Flask
from flask_socketio import SocketIO
import yt_dlp
import subprocess
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Link video YouTube bạn muốn stream
YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

def stream_video():
    # Cấu hình "mặt nạ" để YouTube không chặn server
    ydl_opts = {
        'format': 'best[height<=480]',
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(YOUTUBE_URL, download=False)
        stream_url = info['url']

    # FFmpeg nhận link từ yt-dlp và chuyển thành luồng MJPEG
    command = [
        'ffmpeg', '-i', stream_url,
        '-f', 'mjpeg',
        '-vf', 'scale=320:240',
        '-r', '15',
        '-q:v', '5',
        'pipe:1'
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**6)

    while True:
        # Đọc từng khung hình và gửi qua Socket
        frame = process.stdout.read(8192)
        if not frame: break
        socketio.emit('video_frame', frame)

@socketio.on('connect')
def handle_connect():
    print("Thiết bị đã kết nối!")
    # Chạy luồng stream riêng biệt để không làm treo server
    threading.Thread(target=stream_video, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
