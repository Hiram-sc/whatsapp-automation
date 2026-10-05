STATUS = {
    "mensagens_enviadas": 0
}

def zerar_contagem():
    STATUS["mensagens_enviadas"] = 0

def registrar_envio():
    STATUS["mensagens_enviadas"] += 1

def obter_contagem():
    return STATUS["mensagens_enviadas"]