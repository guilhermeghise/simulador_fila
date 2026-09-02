import heapq


# Parametros do Metodo Congruente Linear
A = 1664525
C = 1013904223
M = 2**32
SEMENTE = 123456789
LIMITE_ALEATORIOS = 100000

# Configuracao comum das filas
CAPACIDADE = 5
CHEGADA_MIN = 3.0
CHEGADA_MAX = 5.0
ATENDIMENTO_MIN = 4.0
ATENDIMENTO_MAX = 5.0

# Variaveis da simulacao. Elas sao reiniciadas antes de cada cenario.
anterior = SEMENTE
aleatorios_usados = 0
tempo_global = 0.0
populacao = 0
perdas = 0
tempos_acumulados = []
escalonador = []
ordem_evento = 0
numero_servidores = 1


def NextRandom():
    """Retorna o proximo valor pseudoaleatorio normalizado em [0, 1)."""
    global anterior, aleatorios_usados

    if aleatorios_usados >= LIMITE_ALEATORIOS:
        return None

    anterior = (A * anterior + C) % M
    aleatorios_usados += 1
    return anterior / M


def sortear_intervalo(limite_inferior, limite_superior):
    """Transforma um numero de [0, 1) em um intervalo uniforme [a, b)."""
    u = NextRandom()
    if u is None:
        return None
    return limite_inferior + (limite_superior - limite_inferior) * u


def agendar_evento(tipo, tempo):
    """Insere um evento no escalonador, que e uma fila de prioridade."""
    global ordem_evento

    # Em caso de empate, a saida e tratada antes da chegada.
    prioridade = 0 if tipo == "SAIDA" else 1
    heapq.heappush(escalonador, (tempo, prioridade, ordem_evento, tipo))
    ordem_evento += 1


def NextEvent():
    """Retira do escalonador o evento com o menor tempo."""
    return heapq.heappop(escalonador)


def CHEGADA():
    """Trata a chegada de um cliente e agenda eventos futuros."""
    global populacao, perdas

    cliente_aceito = populacao < CAPACIDADE

    if cliente_aceito:
        populacao += 1

        # Se ha servidor livre, o atendimento comeca imediatamente.
        if populacao <= numero_servidores:
            intervalo = sortear_intervalo(ATENDIMENTO_MIN, ATENDIMENTO_MAX)
            if intervalo is not None:
                agendar_evento("SAIDA", tempo_global + intervalo)
    else:
        perdas += 1

    # A proxima chegada e agendada mesmo quando o cliente atual e perdido.
    intervalo = sortear_intervalo(CHEGADA_MIN, CHEGADA_MAX)
    if intervalo is not None:
        agendar_evento("CHEGADA", tempo_global + intervalo)


def SAIDA():
    """Trata uma saida e inicia novo atendimento quando ha espera."""
    global populacao

    populacao -= 1

    # Depois da saida, esta condicao indica que ainda existe cliente
    # esperando para ocupar o servidor que acabou de ficar livre.
    if populacao >= numero_servidores:
        intervalo = sortear_intervalo(ATENDIMENTO_MIN, ATENDIMENTO_MAX)
        if intervalo is not None:
            agendar_evento("SAIDA", tempo_global + intervalo)


def inicializar_simulacao(servidores):
    """Reinicia as variaveis e agenda a primeira chegada no tempo 3,0."""
    global anterior, aleatorios_usados, tempo_global, populacao, perdas
    global tempos_acumulados, escalonador, ordem_evento, numero_servidores

    anterior = SEMENTE
    aleatorios_usados = 0
    tempo_global = 0.0
    populacao = 0
    perdas = 0
    tempos_acumulados = [0.0] * (CAPACIDADE + 1)
    escalonador = []
    ordem_evento = 0
    numero_servidores = servidores

    agendar_evento("CHEGADA", 3.0)


def simular(servidores):
    """Executa um cenario ate o uso do aleatorio de numero 100.000."""
    global tempo_global

    inicializar_simulacao(servidores)

    while aleatorios_usados < LIMITE_ALEATORIOS and escalonador:
        tempo_evento, _, _, tipo = NextEvent()

        # O tempo desde o evento anterior pertence ao estado atual da fila.
        tempos_acumulados[populacao] += tempo_evento - tempo_global
        tempo_global = tempo_evento

        if tipo == "CHEGADA":
            CHEGADA()
        else:
            SAIDA()

    probabilidades = [tempo / tempo_global for tempo in tempos_acumulados]

    return {
        "servidores": servidores,
        "tempos": tempos_acumulados.copy(),
        "probabilidades": probabilidades,
        "perdas": perdas,
        "tempo_global": tempo_global,
        "aleatorios": aleatorios_usados,
    }


def imprimir_resultado(resultado):
    servidores = resultado["servidores"]
    print(f"Fila G/G/{servidores}/{CAPACIDADE}")
    print(f"Aleatorios utilizados: {resultado['aleatorios']}")
    print(f"Tempo global: {resultado['tempo_global']:.6f}")
    print(f"Clientes perdidos: {resultado['perdas']}")
    print("Estado | Tempo acumulado | Probabilidade")

    for estado in range(CAPACIDADE + 1):
        tempo = resultado["tempos"][estado]
        probabilidade = resultado["probabilidades"][estado]
        print(f"{estado:>6} | {tempo:>15.6f} | {probabilidade:>11.6%}")

    print(f"Soma das probabilidades: {sum(resultado['probabilidades']):.6%}")


def main():
    print("Parametros do gerador congruente linear")
    print(f"a = {A}; c = {C}; M = {M}; semente = {SEMENTE}")
    print(f"Chegadas: [{CHEGADA_MIN}, {CHEGADA_MAX})")
    print(f"Atendimentos: [{ATENDIMENTO_MIN}, {ATENDIMENTO_MAX})")
    print()

    resultado_um_servidor = simular(1)
    imprimir_resultado(resultado_um_servidor)
    print()

    resultado_dois_servidores = simular(2)
    imprimir_resultado(resultado_dois_servidores)


if __name__ == "__main__":
    main()
