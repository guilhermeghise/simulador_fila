import argparse
import heapq
import json


class Simulador:
    def __init__(self, configuracao):
        validar_configuracao(configuracao)

        gerador = configuracao["gerador"]
        self.a = gerador["a"]
        self.c = gerador["c"]
        self.m = gerador["m"]
        self.anterior = gerador["semente"]
        self.limite_aleatorios = configuracao["limite_aleatorios"]
        self.aleatorios_usados = 0

        self.filas = configuracao["filas"]
        self.populacoes = [0] * len(self.filas)
        self.perdas = [0] * len(self.filas)
        self.tempos = [
            [0.0] * (fila["capacidade"] + 1)
            for fila in self.filas
        ]

        self.tempo_global = 0.0
        self.eventos = []
        self.ordem_evento = 0

    def proximo_aleatorio(self):
        if self.aleatorios_usados >= self.limite_aleatorios:
            return None

        self.anterior = (self.a * self.anterior + self.c) % self.m
        self.aleatorios_usados += 1
        return self.anterior / self.m

    def sortear_intervalo(self, intervalo):
        aleatorio = self.proximo_aleatorio()
        if aleatorio is None:
            return None
        return intervalo[0] + (intervalo[1] - intervalo[0]) * aleatorio

    def agendar(self, tipo, fila, tempo):
        prioridade = 0 if tipo == "SAIDA" else 1
        heapq.heappush(
            self.eventos,
            (tempo, prioridade, self.ordem_evento, tipo, fila),
        )
        self.ordem_evento += 1

    def iniciar_atendimento(self, fila):
        intervalo = self.sortear_intervalo(
            self.filas[fila]["atendimento"]
        )
        if intervalo is not None:
            self.agendar("SAIDA", fila, self.tempo_global + intervalo)

    def entrar(self, fila):
        configuracao = self.filas[fila]
        if self.populacoes[fila] >= configuracao["capacidade"]:
            self.perdas[fila] += 1
            return

        self.populacoes[fila] += 1
        if self.populacoes[fila] <= configuracao["servidores"]:
            self.iniciar_atendimento(fila)

    def chegada_externa(self, fila):
        self.entrar(fila)

        intervalo = self.sortear_intervalo(
            self.filas[fila]["chegada_externa"]["intervalo"]
        )
        if intervalo is not None:
            self.agendar("CHEGADA", fila, self.tempo_global + intervalo)

    def escolher_destino(self, fila):
        rotas = self.filas[fila].get("roteamento", [])
        if not rotas:
            return None

        if len(rotas) == 1 and rotas[0]["probabilidade"] == 1:
            return rotas[0]["destino"]

        aleatorio = self.proximo_aleatorio()
        if aleatorio is None:
            return None

        acumulada = 0.0
        for rota in rotas:
            acumulada += rota["probabilidade"]
            if aleatorio < acumulada:
                return rota["destino"]
        return None

    def saida(self, fila):
        self.populacoes[fila] -= 1
        if self.populacoes[fila] >= self.filas[fila]["servidores"]:
            self.iniciar_atendimento(fila)

        destino = self.escolher_destino(fila)
        if destino is not None:
            self.entrar(destino)

    def acumular_tempo(self, novo_tempo):
        intervalo = novo_tempo - self.tempo_global
        for fila, populacao in enumerate(self.populacoes):
            self.tempos[fila][populacao] += intervalo
        self.tempo_global = novo_tempo

    def simular(self):
        for indice, fila in enumerate(self.filas):
            chegada = fila.get("chegada_externa")
            if chegada:
                self.agendar(
                    "CHEGADA",
                    indice,
                    chegada["primeira_chegada"],
                )

        while (
            self.aleatorios_usados < self.limite_aleatorios
            and self.eventos
        ):
            tempo, _, _, tipo, fila = heapq.heappop(self.eventos)
            self.acumular_tempo(tempo)

            if tipo == "CHEGADA":
                self.chegada_externa(fila)
            else:
                self.saida(fila)


def validar_intervalo(intervalo, nome):
    if (
        not isinstance(intervalo, list)
        or len(intervalo) != 2
        or intervalo[0] < 0
        or intervalo[0] > intervalo[1]
    ):
        raise ValueError(f"{nome} deve ser [minimo, maximo]")


def validar_configuracao(configuracao):
    filas = configuracao.get("filas", [])
    gerador = configuracao.get("gerador", {})

    if not filas:
        raise ValueError("a configuracao deve possuir ao menos uma fila")
    if configuracao.get("limite_aleatorios", 0) <= 0:
        raise ValueError("limite_aleatorios deve ser positivo")
    if not all(gerador.get(chave, 0) > 0 for chave in ("a", "c", "m")):
        raise ValueError("gerador deve informar a, c e m positivos")
    if "semente" not in gerador:
        raise ValueError("gerador deve informar a semente")

    for indice, fila in enumerate(filas):
        servidores = fila.get("servidores", 0)
        capacidade = fila.get("capacidade", 0)
        if servidores <= 0 or capacidade < servidores:
            raise ValueError(
                f"fila {indice}: capacidade deve ser >= servidores > 0"
            )

        validar_intervalo(fila.get("atendimento"), f"fila {indice}.atendimento")

        chegada = fila.get("chegada_externa")
        if chegada:
            validar_intervalo(
                chegada.get("intervalo"),
                f"fila {indice}.chegada_externa.intervalo",
            )
            if chegada.get("primeira_chegada", -1) < 0:
                raise ValueError(
                    f"fila {indice}: primeira_chegada deve ser >= 0"
                )

        soma = 0.0
        for rota in fila.get("roteamento", []):
            destino = rota.get("destino")
            probabilidade = rota.get("probabilidade", -1)
            if not isinstance(destino, int) or not 0 <= destino < len(filas):
                raise ValueError(f"fila {indice}: destino de rota invalido")
            if not 0 <= probabilidade <= 1:
                raise ValueError(f"fila {indice}: probabilidade invalida")
            soma += probabilidade

        if soma > 1.0 + 1e-12:
            raise ValueError(
                f"fila {indice}: probabilidades de roteamento excedem 1"
            )


def imprimir_resultados(simulador):
    print(f"Aleatorios utilizados: {simulador.aleatorios_usados}")
    print(f"Tempo global: {simulador.tempo_global:.6f}\n")

    for indice, fila in enumerate(simulador.filas):
        print(
            f"{fila['nome']} - G/G/{fila['servidores']}/"
            f"{fila['capacidade']}"
        )
        print(f"Clientes perdidos: {simulador.perdas[indice]}")
        print("Estado | Tempo acumulado | Probabilidade")

        for estado, tempo in enumerate(simulador.tempos[indice]):
            probabilidade = tempo / simulador.tempo_global
            print(
                f"{estado:>6} | {tempo:>15.6f} | "
                f"{probabilidade:>11.6%}"
            )
        print()


def verificar():
    configuracao = {
        "gerador": {"a": 1, "c": 1, "m": 16, "semente": 1},
        "limite_aleatorios": 20,
        "filas": [
            {
                "nome": "Origem",
                "servidores": 1,
                "capacidade": 2,
                "atendimento": [1, 1],
                "chegada_externa": {
                    "intervalo": [2, 2],
                    "primeira_chegada": 0,
                },
                "roteamento": [{"destino": 1, "probabilidade": 1}],
            },
            {
                "nome": "Destino",
                "servidores": 1,
                "capacidade": 2,
                "atendimento": [1, 1],
                "roteamento": [],
            },
        ],
    }
    simulador = Simulador(configuracao)
    simulador.simular()
    assert simulador.aleatorios_usados == 20
    assert simulador.perdas == [0, 0]
    assert all(
        abs(sum(tempos) - simulador.tempo_global) < 1e-9
        for tempos in simulador.tempos
    )
    print("Verificacao concluida com sucesso.")


def main():
    parser = argparse.ArgumentParser(
        description="Simulador de uma rede de filas G/G/c/K"
    )
    parser.add_argument(
        "configuracao",
        nargs="?",
        default="config.json",
        help="arquivo JSON da rede (padrao: config.json)",
    )
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="executa a verificacao interna",
    )
    argumentos = parser.parse_args()

    if argumentos.verificar:
        verificar()
        return

    with open(argumentos.configuracao, encoding="utf-8") as arquivo:
        configuracao = json.load(arquivo)

    simulador = Simulador(configuracao)
    simulador.simular()
    imprimir_resultados(simulador)


if __name__ == "__main__":
    main()
