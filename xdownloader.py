import os
import yt_dlp
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X Downloader - Fix Unauthorized</title>
    <style>
        body { font-family: -apple-system, sans-serif; background-color: #15202b; color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { background: #192734; padding: 2rem; border-radius: 20px; width: 90%; max-width: 500px; text-align: center; border: 1px solid #38444d; }
        h1 { color: #1d9bf0; }
        input { width: 100%; padding: 15px; margin: 20px 0; border: 1px solid #38444d; border-radius: 9999px; background: #15202b; color: white; box-sizing: border-box; outline: none; }
        button { background: #1d9bf0; color: white; border: none; padding: 15px 40px; border-radius: 9999px; cursor: pointer; font-weight: bold; width: 100%; }
        .result-box { background: #22303c; margin-top: 20px; padding: 15px; border-radius: 15px; text-align: left; border: 1px solid #00ba7c; }
        .dl-link { display: block; background: #00ba7c; color: white; text-decoration: none; padding: 12px; border-radius: 8px; text-align: center; margin-top: 10px; font-weight: bold; }
        .info-text { font-size: 12px; color: #8899a6; margin-top: 10px; line-height: 1.4; }
    </style>
</head>
<body>
    <div class="container">
        <h1>X Downloader PRO</h1>
        <p>Omijanie blokady "Unauthorized"</p>
        <form id="dlForm">
            <input type="url" id="urlInput" placeholder="Wklej link z X..." required>
            <button type="submit" id="btn">Generuj link</button>
        </form>
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('dlForm').onsubmit = async (e) => {
            e.preventDefault();
            const res = document.getElementById('result');
            res.innerHTML = 'Analizuję zabezpieczenia...';
            
            try {
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `url=${encodeURIComponent(document.getElementById('urlInput').value)}`
                });
                const data = await response.json();
                
                if (data.success) {
                    res.innerHTML = `
                        <div class="result-box">
                            <strong>Wideo znalezione!</strong>
                            <a href="${data.url}" rel="noreferrer" target="_blank" class="dl-link">OTWÓRZ I POBIERZ MP4</a>
                            <div class="info-text">
                                <strong>WAŻNE:</strong> Jeśli po kliknięciu zobaczysz film w przeglądarce:<br>
                                1. Kliknij na niego <strong>prawym przyciskiem myszy</strong>.<br>
                                2. Wybierz <strong>"Zapisz wideo jako..."</strong>.<br>
                                To omija blokadę Unauthorized.
                            </div>
                        </div>`;
                } else { res.innerHTML = '<p style="color:#e0245e">Błąd: Twitter zablokował serwer. Spróbuj za 5 minut.</p>'; }
            } catch (err) { res.innerHTML = 'Błąd połączenia.'; }
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
    
    # Ustawiamy yt-dlp tak, aby udawał sesję mobilną (rzadziej blokowaną)
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target_url, download=False)
            video_url = info.get('url')
            
            # Kluczem jest dodanie atrybutu rel="noreferrer" w HTML, 
            # co powstrzymuje przeglądarkę przed wysłaniem informacji, 
            # że link pochodzi z Twojej aplikacji.
            return jsonify({
                'success': True,
                'url': video_url,
                'title': info.get('title', 'video')
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
