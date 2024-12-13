import pygame
import time
import cv2
import numpy as np
import sys
import pyaudio
import os
import wave
import ffmpeg
import threading

REC_FOLDER = "recordings/"

class Recorder():
    def __init__(self, filename):
        self.filename = filename
        self.screen = pygame.display.set_mode((640, 480))  # Pygame screen
        self.game = self.Game()  # Game logic (e.g., for sprite management)
        
        # Initialize VideoRecorder with Pygame screen reference
        self.video_thread = self.VideoRecorder(self, REC_FOLDER + filename)
        self.audio_thread = self.AudioRecorder(self, REC_FOLDER + filename)

    def startRecording(self):
        self.video_thread.start()
        self.audio_thread.start()

    def stopRecording(self):
        self.video_thread.stop()
        self.audio_thread.stop()

    def saveRecording(self):
        print("Saving recording...")
        self.audio_thread.saveAudio()
        self.video_thread.showFramesResume()
        # Merge video and audio files (use ffmpeg or any other method)
        #Merges both streams and writes
        video_stream = ffmpeg.input(self.video_thread.video_filename)
        audio_stream = ffmpeg.input(self.audio_thread.audio_filename)
        while (not os.path.exists(self.audio_thread.audio_filename)):
            print("waiting for audio file to exit...")
        stream = ffmpeg.output(video_stream, audio_stream, REC_FOLDER + self.filename +".mp4")

        try:
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)
        except ffmpeg.Error as e:
            print(e.stdout, file=sys.stderr)
            print(e.stderr, file=sys.stderr)


    class Game:
        def __init__(self):
            self.FPS = 30
            self.clock = pygame.time.Clock()
            self.sprite = pygame.Surface((50, 50))  # Example sprite
            self.sprite.fill((255, 0, 0))  # Red square as a sprite
            self.sprite_pos = (100, 100)
            self.velocity = 0

        def update(self, volume):
            # Game logic: handle sprite actions based on volume detection
            if volume > 0.5:  # Example threshold for triggering action
                print("Loud sound detected! Triggering jump.")
                self.jump()

            # Update game sprite position, etc.
            self.sprite_pos = (self.sprite_pos[0], self.sprite_pos[1] + self.velocity)

        def draw(self, screen):
            # Draw the game elements (e.g., sprite)
            screen.fill((0, 0, 0))  # Clear screen with black
            screen.blit(self.sprite, self.sprite_pos)
            pygame.display.flip()  # Update the display

        def jump(self):
            # Example function to handle sprite jump
            self.velocity = -10  # Jump up (negative velocity)

    class VideoRecorder():
        def __init__(self, recorder, name, fourcc="MJPG", frameSize=(640,480), camindex=0, fps=15):
            self.recorder = recorder
            self.open = True
            self.device_index = camindex
            self.fps = fps
            self.fourcc = fourcc
            self.video_filename = name + ".avi"
            self.video_cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
            self.video_writer = cv2.VideoWriter_fourcc(*fourcc)
            self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, frameSize)
            self.frame_counts = 1
            self.start_time = time.time()
        
        def record(self):
            "Video starts being recorded and displayed in Pygame"
            counter = 1 
            while self.open:
                ret, frame = self.video_cap.read()
                if ret:
                    self.frame_counts += 1
                    counter += 1

                    # Convert the frame to RGB for Pygame
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = np.rot90(frame)  # Rotate to match Pygame coordinates

                    # Get the screen (this can be a Pygame screen object created earlier)
                    screen = self.recorder.screen

                    # Create a Pygame surface from the frame
                    frame_surface = pygame.surfarray.make_surface(frame)

                    # Blit the surface onto the Pygame screen
                    screen.blit(frame_surface, (0, 0))
                    pygame.display.update()

                    # Write the frame to the video output
                    frame_for_video = np.transpose(frame, (1, 0, 2))  # Correct orientation for video
                    frame_for_video = cv2.cvtColor(frame_for_video, cv2.COLOR_RGB2BGR)
                    self.video_out.write(frame_for_video)

                    # Control frame rate (matching the camera's FPS)
                    self.recorder.game.clock.tick(self.fps)
                else:
                    break

        def stop(self):
            "Stops the video recording"
            self.open = False

        def start(self):
            "Launches the video recording function in a thread"
            self.thread = threading.Thread(target=self.record)
            self.thread.start()

        def showFramesResume(self):
            #Only stop of video has all frames
            frame_counts = self.frame_counts
            elapsed_time = time.time() - self.start_time
            recorded_fps = self.frame_counts / elapsed_time
            print("total frames " + str(frame_counts))
            print("elapsed time " + str(elapsed_time))
            print("recorded fps " + str(recorded_fps))

    class AudioRecorder():
        def __init__(self, recorder, filename, rate=44100, fpb=2940, channels=1, audio_index=0):
            self.recorder = recorder
            self.open = True
            self.rate = rate
            self.frames_per_buffer = fpb
            self.channels = channels
            self.audio_filename = filename + ".wav"
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(format=pyaudio.paInt16,
                                          channels=self.channels,
                                          rate=self.rate,
                                          input=True,
                                          input_device_index=audio_index,
                                          frames_per_buffer=self.frames_per_buffer)
            self.audio_frames = []
            self.latest_volume = 0

        def record(self):
            "Audio starts being recorded"
            self.stream.start_stream()
            while self.open:
                try:
                    data = self.stream.read(self.frames_per_buffer)
                    self.audio_frames.append(data)

                    # Calculate the volume of the audio (RMS)
                    rms = np.sqrt(np.mean(np.square(np.frombuffer(data, dtype=np.int16))))
                    self.latest_volume = rms / 32767.0  # Normalize volume to [0, 1]
                    
                except Exception as e:
                    print("Audio recording error:", e)

        def stop(self):
            "Stops the audio recording"
            self.open = False
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()

        def start(self):
            "Launches the audio recording function in a thread"
            self.thread = threading.Thread(target=self.record)
            self.thread.start()

        def saveAudio(self):
            "Save audio to a file"
            waveFile = wave.open(self.audio_filename, 'wb')
            waveFile.setnchannels(self.channels)
            waveFile.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            waveFile.setframerate(self.rate)
            waveFile.writeframes(b''.join(self.audio_frames))
            waveFile.close()

# Main Game Loop
if __name__ == "__main__":
    recorder = Recorder("test1")
    recorder.startRecording()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Get the latest volume level from the audio thread
        volume = recorder.audio_thread.latest_volume

        # Update game logic based on volume
        recorder.game.update(volume)

        # Draw the game scene (including the video feed)
        recorder.game.draw(recorder.screen)

    recorder.stopRecording()
    recorder.saveRecording()
    pygame.quit()
