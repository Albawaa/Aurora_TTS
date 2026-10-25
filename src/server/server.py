import socket
import sys
import signal
from concurrent.futures import ThreadPoolExecutor
import queue
import threading
import logging
from pathlib import Path

from tts_handler import KokoroTTSHandler
from audio_web_server import AudioWebServer


HOST = '127.0.0.1'  # TTS Server address
PORT = 30000  # TTS server port (initiate port no above 1024 to avoid conflicts)
AUDIO_HOST = '127.0.0.1' # Audio Web Server address (for message playback through a web page)
AUDIO_PORT = 30001  # Audio Web Server port
MAX_TTS_QUEUE = 100 # Max TTS queue lenght
MAX_CLIENT_QUEUE = 5 # Max client connecting queueueueueue 
MAX_TWITCH_MSG_LENGTH = 500
CHAR_SIZE = 4
MAX_MSG_LENGTH = MAX_TWITCH_MSG_LENGTH*CHAR_SIZE

class AuroraServer():
    '''
    Backbone of the TTS server, handles the processor thread, thread pool executor for the client connections
    audio web server and the web server thread.
    '''
    def __init__(self):
        self._tts_input_queue = queue.Queue(MAX_TTS_QUEUE)
        self._shutdown_event = threading.Event()
        self._processor_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._executor = ThreadPoolExecutor()
        self._web_server = AudioWebServer(host=AUDIO_HOST, port=AUDIO_PORT)
        self._web_server_thread = threading.Thread(target=self._web_server.run, daemon=True)

        signal.signal(signal.SIGINT, self._handle_shutdown)

        # Setup the main layout and logging rules
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
        self._logger = logging.getLogger(Path(__file__).name)


    def _unqueues_your_queue(self) -> str | None:
        '''
        Dispenses the tts queue elements (tts text) 
        Returns:
            - (str or None): Returns the tts text if there is, or None if the queue 
                             is empty or if the tts is shutdown.
        '''
        try:
            if not self._shutdown_event.is_set():
                item = self._tts_input_queue.get(block=True, timeout=1)  # 1 second timeout
                data = item.decode('utf-8')
            else:
                data = None
        except UnicodeDecodeError:
            self._logger.error(f"Received non-UTF-8 data, skipping message")
            data = "TTS failed to decode the message, ggwp, get gud"
        except queue.Empty:
            data = None
        finally:
            return data


    def _process_queue(self) -> None:
        '''
        Generates an audio file and updates the web server file name.
        '''
        self._logger
        tts_handler = KokoroTTSHandler()
        while not self._shutdown_event.is_set():
            tts_message = self._unqueues_your_queue() # Unqueueuees at 1Hz 
            if tts_message:
                audio_filename = tts_handler.generate_audio_file(tts_message)
                self._web_server.update_external_filepath(audio_filename)
        self._logger.info("TTS server stopped.")


    def _handle_client(self, client_socket: socket) -> None:
        '''
        Receives client meesage and puts it into the tts queue.
        Parameters:
            - client_socket(socket): The socket to receive the message and 
                                     close the connection once done. 
        '''
        raw = client_socket.recv(MAX_MSG_LENGTH)
        self._tts_input_queue.put(raw)
        client_socket.close()  # close the connection


    def _handle_shutdown(self, signum, frame):
        '''Handles shutdown of the server'''
        self._logger.info("Oki, stopping the tts server... :P")
        self._shutdown_event.set()
        self._logger.info("Shutdown event set")
        self._web_server.stop()
        self._logger.info("Web server told to stop")
        self._executor.shutdown(wait=False)
        self._logger.info("Stopped filling queue")
        self._processor_thread.join()
        self._logger.info("Stopped processing queue")
        self._web_server_thread.join()
        self._logger.info("Stopped web server")
        sys.exit(0)
        

    def start_server(self) -> None:
        '''
        Starts the TTS Server and sets up the network socket.
        '''
        self._logger.info("Starting server...")
        self._processor_thread.start()
        self._web_server_thread.start()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:  # IPv4 TCP socket
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allow port reuse immediately after server shutdown
            server_socket.bind((HOST, PORT))  # bind host address and port together
            server_socket.listen(MAX_CLIENT_QUEUE)  # queue up to MAX_CLIENT_QUEUE connection requests
            server_socket.settimeout(1.0) # Break accept() blocks to process signals
            while True:
                    try:
                        conn, _ = server_socket.accept()  # accept new connection
                        self._executor.submit(self._handle_client, conn)
                    except TimeoutError:
                        continue



if __name__ == '__main__':
    tts_server = AuroraServer()
    tts_server.start_server()