import http.server
import socketserver
import json
import os
import logging
import threading
from pathlib import Path

# GLOBAL VARIABLE: Change this variable while the server is running 
# to immediately switch the track playing in OBS!
CURRENT_AUDIO_FILE = "startup_jingle.wav"
FRONTEND_DIR = os.path.join(Path(__file__).parents[1], "frontend")
TTS_AUDIO_DIR = os.path.join(Path(__file__).parents[2], "temp_logs")
LOGGER = logging.getLogger(Path(__file__).name)


class AudioHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    '''
    Handles HTTP Requests coming from a browser.
    '''
    def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def end_headers(self):
            '''
            Redefined to add a header send to fix issues.
            '''
            self.send_header('Access-Control-Allow-Origin', '*') # Prevent CORS issues
            self.end_headers()

    def do_GET(self) -> None :
        '''
        Redefined to catch specific requests sent by the frontend.
        '''
        # Catch the specific API request from JavaScript (sent periodically by checkForNewAudio)
        if self.path == '/current-track':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            
            # Send the filename back as clean JSON data
            data = {"filename": CURRENT_AUDIO_FILE}
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        # 2. Handle requests for the temp tts folder (sent by html audioPLayer)
        if self.path.startswith('/external-audio/'):
            # Extract the actual filename from the URL
            filename = self.path.replace('/external-audio/', '', 1)
            full_path = os.path.join(TTS_AUDIO_DIR, filename)
            
            # Verify the file exists before trying to serve it
            if os.path.exists(full_path) and os.path.isfile(full_path):
                self.send_response(200)
                self.send_header('Content-Type', 'audio/wav')
                self.end_headers()
                
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())   
            else:
                self.send_error(404, "File Not Found")
            return
            
        # For all other requests, act normally
        super().do_GET()

    def end_headers(self) -> None :
        '''
        Redefined to add header sends.
        '''
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

class AudioWebServer():
    '''
    Server for the web client.
    '''
    def __init__(self, host: str = "127.0.0.1", port: int = 30001):
        '''
        Parameters:
            - host(str): web server address
            - port(int): web server port 
        '''
        self._host = host
        self._port = port
        self._server_running = False

        socketserver.TCPServer.allow_reuse_address = True
        self._httpd = socketserver.TCPServer((self._host, self._port), AudioHTTPRequestHandler)
        self._web_server_thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def run(self) -> None :
        '''
        Starts the web server thread.
        '''
        LOGGER.info(f"Web server running at http://{self._host}:{self._port}")
        self._server_running = True
        self._web_server_thread.start()


    def stop(self) -> None :
        '''
        Stops the web server, releases the port and joins the thread.
        '''
        LOGGER.info("Stopping web server...")
        if self._server_running:
            self._server_running = False
            self._httpd.shutdown()  # This stops the serve_forever loop safely
            LOGGER.info("Set shutdown flag")
            self._httpd.server_close()  # This releases the server port immediately  
            LOGGER.info("Released server port")
            self._web_server_thread.join()
            LOGGER.info("Web server stopped.")
        else:
            LOGGER.warning("Web server already stopped, can't stop again.")


    def update_external_filepath(self, new_filename: str) -> None :
        '''
        Updates the filepath variable to the new generated tts message audio file.
        '''
        global CURRENT_AUDIO_FILE
        CURRENT_AUDIO_FILE = "external-audio/" + new_filename