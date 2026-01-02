import os
from flask import Flask, render_template_string, request, jsonify
import yt_dlp

app = Flask(__name__)

# Wygląd aplikacji inspirowany nowoczesnym stylem X (Twittera)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Video Downloader - Bez Reklam</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; margin-bottom: 1rem; }
        p { color: #8899a6; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; font-size: 16px; box-sizing: border-box; outline: none; }
        input:focus { border-color: #1d9bf0; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; font-size: 16px; width: 100%; transition: background 0.2s; }
        button:hover { background: #1a8cd8; }
        button:disabled { background: #0e4e78; cursor: not-allowed; }
        #result { margin-top: 30px; padding-top: 20px; border-top: 1px solid #38444d; }
        .video-info { text-align: left; background: #22303c; padding: 15px; border-radius: 10px; }
        .download-link { display: block; background: #00ba7c; color: white; text-decoration: none; padding: 12px; border-radius: 10px; font-weight: bold; text-align: center; margin-top: 15px; }
        .download-link:hover { background: #009664; }
        .loader { border: 3px solid #f3f3f3; border-top: 3px solid #1d9bf0; border-radius: 50%; width: 20px; height: 20px; animation: spin 1s linear infinite; display: inline-block; vertical-align: middle; margin-right: 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Video Downloader</h1>
        <p>Pobieraj wideo z X (Twittera) bez reklam i trackerów.</p>
        
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link do posta (np. https://x.com/...)" required>
            <button type="submit" id="btn">Wygeneruj link do pobrania</button>
        </form>

        <div id="result" class="hidden"></div>
    </div>

    <script>
        const form = document.getElementById('dlForm');
        const btn = document.getElementById('btn');
        const result = document.getElementById('result');

        form.onsubmit = async (e) => {
            e.preventDefault();
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> Analizuję wideo...';
            result.classList.add('hidden');
            
            const url = document.getElementById('urlInput').value;

            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(url)}`
                });
                const data = await response.json();

                if (data.success) {
                    result.innerHTML = `
                        <div class="video-info">
                            <p style="color:white; margin-top:0;"><strong>Tytuł:</strong> ${data.title}</p>
                            <a href="${data.url}" target="_blank" class="download-link">POBIERZ PLIK MP4</a>
                            <p style="font-size: 12px; margin-bottom:0;">Tip: Jeśli wideo otworzy się w nowym oknie, kliknij prawym przyciskiem i wybierz "Zapisz wideo jako...".</p>
                        </div>
                    `;
                    result.classList.remove('hidden');
                } else {
                    alert("Błąd: " + data.error);
                }
            } catch (err) {
                alert("Wystąpił błąd podczas połączenia z serwerem.");
            } finally {
                btn.disabled = false;
                btn.innerText = "Wygeneruj link do pobrania";
            }
        };
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract', methods=['POST'])
def extract():
    target_url = request.form.get('url')
    
    # Konfiguracja yt-dlp do wyciągnięcia najlepszego dostępnego linku mp4
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            # Wybieramy bezpośredni URL do pliku
            video_url = info.get('url')
            title = info.get('title', 'Video_z_X')
            
            return jsonify({
                'success': True,
                'url': video_url,
                'title': title
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)