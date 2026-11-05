import threading


_LOCK = threading.RLock()

_ESTADO_INICIAL = {
    "conexao": "desconectado",
    "automacao": "ociosa",
    "automacao_detalhe": None,
    "total": 0,
    "mensagens_enviadas": 0,
}

_STATUS = dict(_ESTADO_INICIAL)

_AUTOMACOES_ATIVAS = {"iniciando", "em_execucao"}


def obter_status() -> dict:
    with _LOCK:
        return dict(_STATUS)


def resetar_estado() -> None:
    with _LOCK:
        _STATUS.clear()
        _STATUS.update(_ESTADO_INICIAL)


def definir_conexao(estado: str) -> None:
    with _LOCK:
        _STATUS["conexao"] = estado


def reservar_automacao(total: int) -> bool:
    with _LOCK:
        if _STATUS["automacao"] in _AUTOMACOES_ATIVAS:
            return False

        _STATUS.update(
            {
                "automacao": "iniciando",
                "automacao_detalhe": None,
                "total": total,
                "mensagens_enviadas": 0,
            }
        )
        return True


def marcar_em_execucao() -> None:
    with _LOCK:
        _STATUS["automacao"] = "em_execucao"
        _STATUS["automacao_detalhe"] = None


def registrar_envio() -> None:
    with _LOCK:
        _STATUS["mensagens_enviadas"] += 1


def finalizar_automacao() -> None:
    with _LOCK:
        _STATUS["automacao"] = "finalizada"
        _STATUS["automacao_detalhe"] = None


def falhar_automacao(mensagem: str) -> None:
    with _LOCK:
        _STATUS["automacao"] = "erro"
        _STATUS["automacao_detalhe"] = mensagem


def automacao_ativa() -> bool:
    with _LOCK:
        return _STATUS["automacao"] in _AUTOMACOES_ATIVAS
