import socket
import logging
from pathlib import Path
import argparse

from filter import hard_filter_text


# Global Variables that define the server's endpoint where the client will
# try to connect. Change this if your server is on a different machine.
HOST = '127.0.0.1'  # loopback address local server
PORT = 30000  # socket server port number

# Setup the main layout and rules for the logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(Path(__file__).name)


def client_program(msg: str) -> None :
    '''
    Main client function, it receives a string message, calls the filter,
    and  sends the message to the server.
    Parameters:
        - msg (str): Input text to send to the tts server (aka the user's message).
    '''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:  # IPv4 TCP socket
        client_socket.connect((HOST, PORT))  # connect to the server
        try:
            filtered_msg = hard_filter_text(msg)
            if filtered_msg:
                client_socket.sendall(filtered_msg.encode())  # send message
        except KeyboardInterrupt:
            print("Sending interrupted...")
        finally:
            client_socket.close()  # close the connection


if __name__ == '__main__':
    '''
    Program entry piont, calls the client main function.

    Args:
        - m, message(str): The user's tts message.
    '''
    parser = argparse.ArgumentParser(description="TTS client. Receives an incoming message, filters it and sends it to the server to be read.")
    parser.add_argument("-m", "--message", 
                        type=str, 
                        required=True, 
                        help="The input text string to filter.")
    args = parser.parse_args()
    client_program(args.message)
    logger.info(f"Succesfully sent message: {args.message}")