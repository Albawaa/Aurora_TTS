# Aurora_TTS
This is a text-to-speech solution that uses the Kokoro-TTS model to generate speech from input text.

## How it works
### Server.py
The server.py script is the heavy lifter. It's this script that you should start once, and before your stream (or other application).

It handles client requests (ex.: a viewer using !tts command), text-to-speech generation, and runs a web server that plays the generated audio file (this is what is put as a browser source in obs).

In the current configuration, everything runs locally, but it would be possible to run as a distributed system by simply modifying the ip addresses.

### Client.py
This is the script that takes the text that needs to be generated as input, filters it, and sends it to the server to be processed.

The text to be sent is passed as a parameter (-m "<text_to_be_spoken>" or --message "<text_to_be_spoken>"). The script then 
filters the text and replaces the filtered word or words with a preset filter word.

## First time setup
1- Add words that should be filtered to the prohibition_list.txt file in the config filer. Write one term per line and that exact term and simple leetspeak of it will be filtered. 

2- Run the init_dev_venv.ps1 to setup the virtual environment and download the required python packages. This step might not work out of the box, as the script currently assumes that your python installation is callable with "py".    

### Stream specific setup
3- In OBS (or other streaming software), add a web source and put the web server address (default: 127.0.0.1:30001)

## How I currently use it
I set up Streamer.bot to run the client.py everytime the !tts command is used in my Twitch chat. (Make sure to do so in a safe way)

Before stream, I start the server.py script in a terminal. I make sure to use the python.exe that is in the virtual enviroment. Once the script confirms it's ready and the kokoro engine is running, I refresh the OBS source and expect to hear the startup jingle.

At this point Aurora_TTS is now ready to go and handle the stream tts commands :3