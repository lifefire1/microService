import pika
import whisper
import openai
from gtts import gTTS
import os

# Функция для отправки аудиофайла в очередь RabbitMQ
def send_audio_to_queue(audio_file):
    connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.0.4'))
    channel = connection.channel()

    # Чтение содержимого файла в бинарном режиме
    with open(audio_file, 'rb') as file:
        audio_data = file.read()

    # Определение новой очереди (необязательно, если очередь уже определена заранее)
    # channel.queue_declare(queue='audio_output_queue')

    # Отправка аудиофайла в очередь
    channel.basic_publish(exchange='', routing_key='audio_output_queue', body=audio_data)

    connection.close()

model = whisper.load_model("medium")

def callback(ch, method, properties, body):
    # Предполагается, что тело сообщения содержит бинарные данные аудиофайла
    audio_data = body

    # Обработайте полученные данные здесь, например, сохраните их в файл
    with open("received_audio.wav", "wb") as f:
        f.write(audio_data)
    result = model.transcribe("received_audio.wav")
    # print(result["text"])

    openai.api_key = "pl0CaxJxOvShQ22PO8d6IU3l5rhVWAATFCEoWuVWWuQ"
    openai.api_base = "https://chimeragpt.adventblocks.cc/api/v1"
    text = result["text"]
    response = openai.ChatCompletion.create(
        model='gpt-4',
        messages=[
            {'role': 'user', 'content': text},
        ],
        stream=False
    )
    audio = gTTS(text=response['choices'][0]['message']['content'], lang="ru", slow=False)
    audio.save("example.mp3")

    # Отправка аудиофайла "example.mp3" в очередь
    send_audio_to_queue("example.mp3")

    # Удаление временного аудиофайла
    os.remove("example.mp3")

    print("done")
#   после этого нужно положить файл в очередь в rabbitmq

# Подключение к RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.0.4'))
channel = connection.channel()

# Убедитесь, что очередь существует (можно использовать тот же самый параметр, что и в Java-коде)
channel.queue_declare(queue='audio_queue')

# Запуск прослушивания очереди на предмет новых сообщений
channel.basic_consume(queue='audio_queue', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()