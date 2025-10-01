import logging
import time
import string
import threading
import assemblyai as aai
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingEvents,
    StreamingParameters,
    StreamingSessionParameters,
    BeginEvent,
    TurnEvent,
    TerminationEvent,
    StreamingError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_words(s):
    # Lowercase, strip punctuation, split into words
    translator = str.maketrans('', '', string.punctuation)
    return [w.lower().translate(translator) for w in s.strip().split() if w]

def append_new_part(original: str, updated: str) -> str:
    if original is None:
        original = ""
    if updated is None:
        updated = ""

    original_words = normalize_words(original)
    updated_words = normalize_words(updated)

    # Find longest suffix of original that matches prefix of updated (word-wise)
    for i in range(len(original_words)):
        suffix = original_words[i:]
        if updated_words[:len(suffix)] == suffix:
            appended_part_words = updated_words[len(suffix):]
            # To reconstruct appended part in original form, take from 'updated' string:
            # But to keep it simple, just join appended_part_words with spaces
            appended_part = ' '.join(appended_part_words)
            if appended_part:
                # Append with a space if original isn't empty
                return original.rstrip() + ' ' + appended_part
            else:
                return original.rstrip()

    # No overlap found, append whole updated string
    if original.strip():
        return original.rstrip() + ' ' + updated.lstrip()
    else:
        return updated.lstrip()

class ControlledMicrophoneStream:
    """
    Wrapper around AssemblyAI's MicrophoneStream to allow stopping from another thread.
    """
    def __init__(self, sample_rate=16000):
        self.stream = aai.extras.MicrophoneStream(sample_rate=sample_rate)
        self._stopped = False

    def __iter__(self):
        for chunk in self.stream:
            if self._stopped:
                break
            yield chunk

    def close(self):
        self._stopped = True
        self.stream.close()


class SpeechToTextManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.latest_transcript = ""
        self.done = False
        self.client = StreamingClient(
            StreamingClientOptions(api_key=self.api_key)
        )
        # Attach event handlers
        self.client.on(StreamingEvents.Begin, self.on_begin)
        self.client.on(StreamingEvents.Turn, self.on_turn)
        self.client.on(StreamingEvents.Termination, self.on_terminated)
        self.client.on(StreamingEvents.Error, self.on_error)
        self.client.connect(
            StreamingParameters(
                sample_rate=16000,
                format_turns=True,
            )
        )

    def on_begin(self, client: StreamingClient, event: BeginEvent):
        print(f"Session started: {event.id}")

    def on_turn(self, client: StreamingClient, event: TurnEvent):
        self.latest_transcript = append_new_part(self.latest_transcript,event.transcript)
        print(f"Transcript update: {event.transcript} (End of turn: {event.end_of_turn})")

        if event.end_of_turn and not event.turn_is_formatted:
            params = StreamingSessionParameters(format_turns=True)
            client.set_params(params)

    def on_terminated(self, client: StreamingClient, event: TerminationEvent):
        print(f"Session terminated: processed {event.audio_duration_seconds} seconds of audio")
        self.done = True

    def on_error(self, client: StreamingClient, error: StreamingError):
        print(f"Error occurred: {error}")
        self.done = True

    def speechtotext_from_mic(self, max_duration_sec=60, stop_key="stop"):
        self.done = False
        self.latest_transcript = ""
        print("Starting continuous speech recognition (AssemblyAI)...")
        start_time = time.time()
        mic_stream = ControlledMicrophoneStream(sample_rate=16000)

        def stream_audio():
            try:
                self.client.stream(mic_stream)
            except Exception as e:
                print(f"Exception in streaming thread: {e}")
            finally:
                print("[DEBUG] Stream thread ending.")
                self.done = True

        streaming_thread = threading.Thread(target=stream_audio)
        streaming_thread.start()

        #checking for time or stop word
        try:
            while not self.done:
                time.sleep(0.1)

                normalized = self.latest_transcript.lower().translate(
                    str.maketrans('', '', string.punctuation)
                ).strip()

                if stop_key.lower() in normalized.split():
                    print(f"Detected stop keyword '{stop_key}' in transcript, stopping...")
                    mic_stream.close()  # Stops iteration in the stream
                    #self.client.disconnect(terminate=True)
                    break

                if time.time() - start_time > max_duration_sec:
                    print("Max duration reached, stopping...")
                    mic_stream.close()
                    #self.client.disconnect(terminate=True)
                    break

        except KeyboardInterrupt:
            print("KeyboardInterrupt received, stopping recognition.")
            mic_stream.close()
            self.client.disconnect(terminate=True)

        streaming_thread.join(timeout=5)
        if streaming_thread.is_alive():
            print("[WARNING] Stream thread did not shut down cleanly after disconnect.")

        print("\nFinal transcript:")
        print(self.latest_transcript)
        return self.latest_transcript


if __name__ == "__main__":
    API_KEY = os.getenv("ASSEMBLYAI_API_KEY") # Replace with your AssemblyAI API key
    stt_manager = SpeechToTextManager(API_KEY)

    while True:
        result = stt_manager.speechtotext_from_mic(max_duration_sec=30, stop_key="stop")
        if not result.strip():
            print("Did not receive any input from your microphone!")
        else:
            print(f"\nHERE IS THE RESULT:\n{result}")
            print(f"Inputed string:\n{stt_manager.latest_transcript}")
        print("\nWaiting 10 seconds before next listening session...\n")
        time.sleep(10)