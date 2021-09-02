# Vibranium
## Solução de monitoramento inteligente de motores elétricos baseado em dados de vibração
<img src="https://github.com/1lucas1gabriel/Vibranium/blob/main/img/Architecture.png" width="60%">

A solução está divida em três partes:
1. Endpoint: Dispositivo de aquisição para coleta de dados de vibração com capacidade de transmissão via Bluetooth Low Energy (BLE).
2. Gateway: Integração entre o dispositivo de coleta e a nuvem, possibilitando a aplicação de transformação dos dados brutos de aceleração.
3. Web-Service: API REST para armazenamento dos dados e treino do modelo de Machine Learning para detectar anomalias
