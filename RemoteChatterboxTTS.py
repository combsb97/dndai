import requests
import base64
import os

class RemoteChatterboxTTS:
    """
    A client for connecting to a secure, self-hosted Chatterbox TTS instance via Caddy.
    """
    def __init__(self, base_url, username, password):
        """
        Args:
            base_url (str): The full URL (e.g., "https://tts.bencombs.art")
            username (str): The Caddy basic auth username
            password (str): The Caddy basic auth password
        """
        self.base_url = base_url.rstrip('/')
        
        # Generate the same secure Basic Auth header as your Ollama client
        credentials = f"{username}:{password}"
        auth_b64 = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        
        self.headers = {
            "Authorization": f"Basic {auth_b64}"
        }

    def speak(self, text, output_file="output.wav"):
        """
        Sends text to the remote server and saves the resulting audio.
        
        Args:
            text (str): The text to convert to speech.
            output_file (str): Path to save the .wav file (default: output.wav)
            voice_id (str): Optional voice ID if your TTS supports multiple voices.
        
        Returns:
            str: The path to the saved audio file.
        """
        url = f"{self.base_url}/chatterbox/tts"
        payload = {
            "text": text,
        }

        print(f"🎤 Sending text to {self.base_url}...")
        
        try:
            response = requests.post(url, data=payload, headers=self.headers)
            
            if response.status_code == 200:
                # Write the binary audio data to a file
                with open(output_file, "wb") as f:
                    f.write(response.content)
                print(f"✅ Audio saved to: {output_file}")
                return output_file
            
            elif response.status_code == 401:
                raise ConnectionError("❌ 401 Unauthorized. Check your Caddy password.")
            else:
                raise ConnectionError(f"❌ Server returned {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Error generating audio: {e}")
            return None


DOMAIN = "https://tts.bencombs.art" 
USER = "admin"
PASS = "011iv3r0329!" # Your real password

tts_client = RemoteChatterboxTTS(DOMAIN, USER, PASS)