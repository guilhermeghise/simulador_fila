import heapq


# Parametros do Metodo Congruente Linear
A = 1664525
C = 1013904223
M = 2**32
SEMENTE = 123456789
LIMITE_ALEATORIOS = 100000


# Configuracao da chegada externa
CHEGADA_MIN = 1.0
CHEGADA_MAX = 5.0
PRIMEIRA_CHEGADA = 2.5


# Fila 1 - G/G/2/3
FILA1_SERVIDORES = 2
FILA1_CAPACIDADE = 3
FILA1_ATENDIMENTO_MIN = 4.0
FILA1_ATENDIMENTO_MAX = 5.0


# Fila 2 - G/G/1/5
FILA2_SERVIDORES = 1
FILA2_CAPACIDADE = 5
FILA2_ATENDIMENTO_MIN = 1.0
FILA2_ATENDIMENTO_MAX = 3.0


# Variaveis da simulacao
anterior = SEMENTE
aleatorios_usados = 0
tempo_global = 0.0

populacao_fila1 = 0
populacao_fila2 = 0

perdas_fila1 = 0
perdas_fila2 = 0

tempos_fila1 = [0.0] * (FILA1_CAPACIDADE + 1)
tempos_fila2 = [0.0] * (FILA2_CAPACIDADE + 1)

escalonador = []
ordem_evento = 0


def NextRandom():
    """Retorna o proximo valor pseudoaleatorio normalizado em [0, 1)."""
    global anterior, aleatorios_usados

    if aleatorios_usados >= LIMITE_ALEATORIOS:
        return None

    anterior = (A * anterior + C) % M
    aleatorios_usados += 1

    return anterior / M


def sortear_intervalo(limite_inferior, limite_superior):
    """Transforma um numero de [0, 1) em um intervalo uniforme."""
    u = NextRandom()

    if u is None:
        return None

    return limite_inferior + (
        limite_superior - limite_inferior
    ) * u


def agendar_evento(tipo, tempo):
    """Insere um evento no escalonador."""
    global ordem_evento

    # Em caso de empate:
    # SAIDA antes de PASSAGEM e PASSAGEM antes de CHEGADA
    prioridades = {
        "SAIDA": 0,
        "PASSAGEM": 1,
        "CHEGADA": 2
    }

    heapq.heappush(
        escalonador,
        (
            tempo,
            prioridades[tipo],
            ordem_evento,
            tipo
        )
    )

    ordem_evento += 1


def NextEvent():
    """Retira o evento com menor tempo do escalonador."""
    return heapq.heappop(escalonador)


def CHEGADA():
    """
    Trata a chegada externa de um cliente na Fila 1.
    """
    global populacao_fila1, perdas_fila1

    if populacao_fila1 < FILA1_CAPACIDADE:

        populacao_fila1 += 1

        # Se existe servidor livre, inicia atendimento imediatamente.
        if populacao_fila1 <= FILA1_SERVIDORES:

            intervalo = sortear_intervalo(
                FILA1_ATENDIMENTO_MIN,
                FILA1_ATENDIMENTO_MAX
            )

            if intervalo is not None:
                agendar_evento(
                    "PASSAGEM",
                    tempo_global + intervalo
                )

    else:
        perdas_fila1 += 1

    # Agenda a proxima chegada externa.
    intervalo = sortear_intervalo(
        CHEGADA_MIN,
        CHEGADA_MAX
    )

    if intervalo is not None:
        agendar_evento(
            "CHEGADA",
            tempo_global + intervalo
        )


def PASSAGEM():
    """
    Trata a saida de um cliente da Fila 1 e sua chegada
    na Fila 2.
    """
    global populacao_fila1
    global populacao_fila2
    global perdas_fila2

    # Cliente sai da Fila 1
    populacao_fila1 -= 1

    # Se ainda existe cliente esperando na Fila 1,
    # inicia um novo atendimento.
    if populacao_fila1 >= FILA1_SERVIDORES:

        intervalo = sortear_intervalo(
            FILA1_ATENDIMENTO_MIN,
            FILA1_ATENDIMENTO_MAX
        )

        if intervalo is not None:
            agendar_evento(
                "PASSAGEM",
                tempo_global + intervalo
            )

    # Cliente tenta entrar na Fila 2.
    if populacao_fila2 < FILA2_CAPACIDADE:

        populacao_fila2 += 1

        # Se o servidor da Fila 2 estiver livre,
        # inicia o atendimento.
        if populacao_fila2 <= FILA2_SERVIDORES:

            intervalo = sortear_intervalo(
                FILA2_ATENDIMENTO_MIN,
                FILA2_ATENDIMENTO_MAX
            )

            if intervalo is not None:
                agendar_evento(
                    "SAIDA",
                    tempo_global + intervalo
                )

    else:
        perdas_fila2 += 1


def SAIDA():
    """
    Trata a saida definitiva de um cliente da Fila 2.
    """
    global populacao_fila2

    populacao_fila2 -= 1

    # Se ainda existe cliente esperando,
    # inicia o atendimento do proximo.
    if populacao_fila2 >= FILA2_SERVIDORES:

        intervalo = sortear_intervalo(
            FILA2_ATENDIMENTO_MIN,
            FILA2_ATENDIMENTO_MAX
        )

        if intervalo is not None:
            agendar_evento(
                "SAIDA",
                tempo_global + intervalo
            )


def acumular_tempo(novo_tempo):
    """
    Acumula simultaneamente o tempo do estado atual
    das duas filas.
    """
    global tempo_global

    intervalo = novo_tempo - tempo_global

    tempos_fila1[populacao_fila1] += intervalo
    tempos_fila2[populacao_fila2] += intervalo

    tempo_global = novo_tempo


def simular():
    """
    Executa a simulacao ate utilizar 100.000 numeros
    pseudoaleatorios.
    """

    # Primeira chegada determinada pelo enunciado.
    agendar_evento(
        "CHEGADA",
        PRIMEIRA_CHEGADA
    )

    while aleatorios_usados < LIMITE_ALEATORIOS and escalonador:

        tempo_evento, _, _, tipo = NextEvent()

        # O tempo deve ser acumulado nas DUAS filas.
        acumular_tempo(tempo_evento)

        if tipo == "CHEGADA":
            CHEGADA()

        elif tipo == "PASSAGEM":
            PASSAGEM()

        elif tipo == "SAIDA":
            SAIDA()


def imprimir_fila(
    numero,
    servidores,
    capacidade,
    tempos,
    perdas
):
    print(
        f"Fila {numero} - "
        f"G/G/{servidores}/{capacidade}"
    )

    print(f"Clientes perdidos: {perdas}")
    print("Estado | Tempo acumulado | Probabilidade")

    for estado in range(capacidade + 1):

        tempo = tempos[estado]
        probabilidade = tempo / tempo_global

        print(
            f"{estado:>6} | "
            f"{tempo:>15.6f} | "
            f"{probabilidade:>11.6%}"
        )

    print()


def main():

    print("Parametros do gerador congruente linear")
    print(
        f"a = {A}; c = {C}; M = {M}; "
        f"semente = {SEMENTE}"
    )

    print()

    print(
        f"Chegadas externas: "
        f"[{CHEGADA_MIN}, {CHEGADA_MAX})"
    )

    print(
        f"Fila 1: G/G/{FILA1_SERVIDORES}/"
        f"{FILA1_CAPACIDADE}, atendimento "
        f"[{FILA1_ATENDIMENTO_MIN}, "
        f"{FILA1_ATENDIMENTO_MAX})"
    )

    print(
        f"Fila 2: G/G/{FILA2_SERVIDORES}/"
        f"{FILA2_CAPACIDADE}, atendimento "
        f"[{FILA2_ATENDIMENTO_MIN}, "
        f"{FILA2_ATENDIMENTO_MAX})"
    )

    print()

    simular()

    print(f"Aleatorios utilizados: {aleatorios_usados}")
    print(f"Tempo global: {tempo_global:.6f}")
    print()

    imprimir_fila(
        1,
        FILA1_SERVIDORES,
        FILA1_CAPACIDADE,
        tempos_fila1,
        perdas_fila1
    )

    imprimir_fila(
        2,
        FILA2_SERVIDORES,
        FILA2_CAPACIDADE,
        tempos_fila2,
        perdas_fila2
    )


if __name__ == "__main__":
    main()