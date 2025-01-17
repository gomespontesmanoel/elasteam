import pika
import os
import json
import logging
from pathlib import Path
import time
from datetime import datetime

# Configuração do RabbitMQ
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq.steam.svc.cluster.local')
RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'steam')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'user')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', '123456789')

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminho do arquivo JSON e tamanho do lote
OUTPUT_FILE = "result.json"
BATCH_SIZE = 60

def connect_to_rabbitmq():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection_params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials
    )
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    return connection, channel

def salvar_mensagens_em_json(dados_agrupados, lote_id):
    # Lê os dados existentes, se houver
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, "r") as f:
            resultados = json.load(f)
    else:
        resultados = {}

    # Adiciona o novo lote ao arquivo existente
    lote_key = f"lote_{lote_id}"
    resultados[lote_key] = {}

    for sensor, data in dados_agrupados.items():
        temperaturas = data["temperaturas"][:BATCH_SIZE]
        media = round(sum(temperaturas) / len(temperaturas), 2) if temperaturas else 0
        temp_min = min(temperaturas) if temperaturas else None
        temp_max = max(temperaturas) if temperaturas else None

        resultados[lote_key][sensor] = {
            "media": media,
            "minima": temp_min,
            "maxima": temp_max,
            "temperaturas": temperaturas
        }

    # Salva os dados atualizados
    with open(OUTPUT_FILE, "w") as f:
        json.dump(resultados, f, indent=4)

def processar_lote(channel):
    mensagens = []
    for _ in range(BATCH_SIZE):
        method_frame, properties, body = channel.basic_get(queue=RABBITMQ_QUEUE, auto_ack=False)
        if method_frame:
            message = json.loads(body.decode())
            mensagens.append(message)
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        else:
            break

    if mensagens:
        # Agrupa mensagens por sensor
        dados_agrupados = {}
        for mensagem in mensagens:
            for sensor_temperaturas, temperaturas_str in mensagem.items():
                sensores = sensor_temperaturas.split(';')
                temperaturas = temperaturas_str.split(';')

                for sensor, temp_str in zip(sensores, temperaturas):
                    if sensor not in dados_agrupados:
                        dados_agrupados[sensor] = {"temperaturas": []}
                    try:
                        temperatura = float(temp_str)
                        dados_agrupados[sensor]["temperaturas"].append(temperatura)
                    except ValueError:
                        continue

        # Define o ID do lote como o timestamp formatado
        lote_id = datetime.now().strftime("%Y-%m-%d_%H-%M")
        salvar_mensagens_em_json(dados_agrupados, lote_id)

connection, channel = connect_to_rabbitmq()

try:
    while True:
        processar_lote(channel)
        time.sleep(2)
except KeyboardInterrupt:
    logger.info("Interrompido pelo usuário.")
finally:
    connection.close()