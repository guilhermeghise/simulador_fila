# Simulador de rede de filas

Simulador de eventos discretos para redes de filas G/G/c/K. A configuração
padrão representa as duas filas em tandem solicitadas no trabalho:

- Fila 1: G/G/2/3, chegadas entre 1 e 5 e atendimento entre 4 e 5;
- Fila 2: G/G/1/5, atendimento entre 1 e 3;
- 100% dos clientes atendidos pela Fila 1 seguem para a Fila 2;
- primeira chegada no tempo 2,5 e encerramento no 100.000º aleatório.

## Como executar

```bash
python3 simulador_fila.py
```

O programa exibe o tempo global, as perdas, os tempos acumulados e as
probabilidades de cada estado das filas.

Para usar outra rede, copie `config.json`, altere as filas e informe o arquivo:

```bash
python3 simulador_fila.py outra_rede.json
```

O modelo do trabalho T1 está em `t1.json`:

```bash
python3 simulador_fila.py t1.json
```

Nesse arquivo, a Fila 1 não possui capacidade máxima. A Fila 2 encaminha
30% dos clientes para a Fila 1, 50% para a Fila 3 e 20% para fora da rede.
A Fila 3 encaminha 70% para a Fila 2 e 30% para fora.

Cada fila aceita `nome`, `servidores`, `capacidade`, intervalo de
`atendimento`, `chegada_externa` opcional e uma lista de `roteamento`. O campo
`destino` é o índice da fila na lista, começando em zero. A soma das
probabilidades pode ser menor que 1; o restante representa a saída da rede.
Omita `capacidade` para uma fila sem limite de clientes.

Exemplo de roteamento com 70% para a segunda fila e 30% para fora da rede:

```json
"roteamento": [
  {"destino": 1, "probabilidade": 0.7}
]
```

## Verificação interna

```bash
python3 simulador_fila.py --verificar
```
