import openai
import pyaudio
import wave
import speech_recognition as sr
from gtts import gTTS
import os
from playsound import playsound
import RPi.GPIO as GPIO
import time

# OpenAI API 키 설정 (자신의 키로 바꾸세요)
openai.api_key = 'YOUR_OPENAI_API_KEY'
led = 22
switch = 17
state = 1

# 음성 녹음 함수
def record_audio(filename):
    GPIO.output(led, 1)

    chunk = 1024  # Record in chunks of 1024 samples
    sample_format = pyaudio.paInt16  # 16 bits per sample
    channels = 1
    fs = 44100  # Record at 44100 samples per second
    p = pyaudio.PyAudio()  # Create an interface to PortAudio

    print('Recording...')

    stream = p.open(format=sample_format,
                    channels=channels,
                    rate=fs,
                    frames_per_buffer=chunk,
                    input=True)

    frames = []  # Initialize array to store frames

    # GPIO.input(switch)==1 조건이 유지되는 동안 데이터 저장
    try:
        while GPIO.input(switch) == 1:
            data = stream.read(chunk)
            frames.append(data)
            time.sleep(0.01)  # CPU 사용량을 줄이기 위해 잠시 대기
    except KeyboardInterrupt:
        pass

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    # Terminate the PortAudio interface
    p.terminate()

    print('Finished recording.')

    # Save the recorded data as a WAV file
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(sample_format))
    wf.setframerate(fs)
    wf.writeframes(b''.join(frames))
    wf.close()

    GPIO.output(led, 0)

# 음성을 텍스트로 변환 함수
def speech_to_text(filename):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language='ko-KR')
        print('음성 인식 텍스트:', text)
        return text
    except sr.UnknownValueError:
        print("음성을 인식할 수 없습니다.")
        return ""
    except sr.RequestError as e:
        print("음성 인식 서비스에 접근할 수 없습니다. 에러:", e)
        return ""

# ChatGPT에게 질문하고 응답 받기
def chat_with_gpt(prompt):
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=prompt,
      max_tokens=150
    )
    return response.choices[0].text.strip()

# 텍스트를 음성으로 변환하고 재생하는 함수
def text_to_speech(text):
    tts = gTTS(text=text, lang='ko')
    filename = "response.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# 메인 함수
def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(led, GPIO.OUT)
    GPIO.setup(switch, GPIO.IN, GPIO.PUD_UP)
    print("setup finish")
    try:
        while True:
            if GPIO.input(switch) == 0:
                while True:
                    if GPIO.input(switch) == 1:
                        audio_filename = "input.wav"
                        record_audio(audio_filename)
                        text = speech_to_text(audio_filename)
                        if text:
                            response = chat_with_gpt(text)
                            print('GPT response:', response)
                            text_to_speech(response)
                        time.sleep(0.2)
                        break
    finally:
        print('end')

if __name__ == "__main__":
    main()