import threading
import time
import random
import math
import tkinter as tk
import heapq
from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)

# Número de filósofos (e garfos)
NUM_FILOSOFOS = 5

# Limite de ciclos de comer para cada filósofo
MAX_CICLOS = 5

# Tempo máximo de espera para evitar starvation (em segundos)
TEMPO_MAX_ESPERA = 10

# Cores associadas aos filósofos para os prints
cores = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA]

# Estados dos filósofos
class Estado:
    PENSANDO = 0
    COM_FOME = 1
    COMENDO = 2
    TERMINADO = 3

# Semáforos para representar os garfos
garfos = [threading.Semaphore(1) for _ in range(NUM_FILOSOFOS)]

# Estado inicial de cada filósofo
estado = [Estado.PENSANDO for _ in range(NUM_FILOSOFOS)]

# Cores associadas aos estados dos filósofos
ESTADO_CORES = {
    "Pensando": "lightblue",
    "Com fome": "orange",
    "Comendo": "green",
    "Terminado": "gray"  
}

# Contador de refeições para cada filósofo
refeicoes = [0 for _ in range(NUM_FILOSOFOS)]

# Criação da interface gráfica
class JantarFilosofos:
    def __init__(self, root):
        self.root = root
        self.root.title("Jantar dos Filósofos")
        self.canvas = tk.Canvas(root, width=500, height=600)
        self.canvas.pack()
        self.estados = ["Pensando" for _ in range(NUM_FILOSOFOS)]
        self.tempos = [{"pensando": 0, "esperando": 0, "comendo": 0} for _ in range(NUM_FILOSOFOS)]
        self.filosofo_pos = self.calcular_posicoes_circulares(250, 250, 150, NUM_FILOSOFOS)
        self.garfo_pos = self.calcular_posicoes_circulares(250, 250, 100, NUM_FILOSOFOS, self.filosofo_pos)
        self.circulos = []
        self.desenha_filosofos()
        self.desenha_garfos()
        self.desenha_legenda()

    def calcular_posicoes_circulares(self, centro_x, centro_y, raio, num_elementos, posicoes_filosofos=None):
        """Calcula posições circulares para os elementos (filósofos ou garfos)."""
        posicoes = []
        if posicoes_filosofos is None:  # Calcula posições dos filósofos
            for i in range(num_elementos):
                angulo = 2 * math.pi * i / num_elementos
                x = centro_x + raio * math.cos(angulo)
                y = centro_y + raio * math.sin(angulo)
                posicoes.append((x, y))
        else:  # Calcula posições dos garfos
            for i in range(num_elementos):
                x1, y1 = posicoes_filosofos[i]
                x2, y2 = posicoes_filosofos[(i + 1) % num_elementos]
                x = (x1 + x2) / 2
                y = (y1 + y2) / 2
                posicoes.append((x, y))
        return posicoes

    def desenha_filosofos(self):
        for i in range(NUM_FILOSOFOS):
            x, y = self.filosofo_pos[i]
            cor = ESTADO_CORES[self.estados[i]]
            circulo = self.canvas.create_oval(x-30, y-30, x+30, y+30, fill=cor, outline="black")
            self.circulos.append(circulo)
            self.canvas.create_text(x, y, text=f"F{i+1}", font=("Arial", 10))

    def desenha_garfos(self):
        self.garfos_canvas = []
        for i in range(NUM_FILOSOFOS):
            x, y = self.garfo_pos[i]
            garfo = self.canvas.create_oval(x-10, y-10, x+10, y+10, fill="brown", outline="black")
            self.garfos_canvas.append(garfo)
            self.canvas.create_text(x, y, text=f"g{i}", font=("Arial", 8))

    def desenha_legenda(self):
        self.canvas.create_text(50, 400, text="Legenda:", font=("Arial", 10, "bold"))

        self.canvas.create_rectangle(40, 420, 90, 440, fill="lightblue")
        self.canvas.create_text(100, 430, text="Pensando", anchor=tk.W)

        self.canvas.create_rectangle(40, 450, 90, 470, fill="orange")
        self.canvas.create_text(100, 460, text="Com Fome", anchor=tk.W)

        self.canvas.create_rectangle(40, 480, 90, 500, fill="green")
        self.canvas.create_text(100, 490, text="Comendo", anchor=tk.W)

        self.canvas.create_rectangle(40, 510, 90, 530, fill="gray")
        self.canvas.create_text(100, 520, text="Terminou", anchor=tk.W)

    def atualizar_estado(self, id, novo_estado):
        self.root.after(0, self._atualizar_estado, id, novo_estado)

    def _atualizar_estado(self, id, novo_estado):
        self.estados[id] = novo_estado
        cor = ESTADO_CORES[novo_estado]
        self.canvas.itemconfig(self.circulos[id], fill=cor)

    def atualizar_garfo(self, id_garfo, estado):
        self.root.after(0, self._atualizar_garfo, id_garfo, estado)

    def _atualizar_garfo(self, id_garfo, estado):
        cor = "green" if estado == "ocupado" else "brown"
        self.canvas.itemconfig(self.garfos_canvas[id_garfo], fill=cor)

    def atualiza_interface(self):
        self.root.update()

# Semáforo para controlar o acesso aos garfos
mutex = threading.Semaphore(1)

# Fila de prioridade para controlar a ordem dos filósofos
fila_prioridade = []

# Funções para gerenciar a fila de prioridade
def adicionar_filosofo_na_fila(id, tempo_espera):
    heapq.heappush(fila_prioridade, (refeicoes[id], tempo_espera, id))

def proximo_filosofo_na_fila():
    return heapq.heappop(fila_prioridade)[2]

# Função para verificar se um filósofo pode pegar os garfos
def pode_comer(id):
    vizinho_direita = (id + 1) % NUM_FILOSOFOS
    vizinho_esquerda = (id - 1) % NUM_FILOSOFOS
    return estado[id] == Estado.COM_FOME and estado[vizinho_direita] != Estado.COMENDO and estado[vizinho_esquerda] != Estado.COMENDO

# Função que simula as ações de um filósofo
def filosofo(id, jantar, max_ciclos, relatorios_finais):
    ciclos = 0

    while ciclos < max_ciclos:
        print(f"=== Início do ciclo {ciclos + 1} para o Filósofo {id + 1} ===")

        # Filósofo pensa
        jantar.atualizar_estado(id, "Pensando")
        print(f"{cores[id]}Filósofo {id+1} está pensando. \n")
        inicio_pensar = time.time()
        time.sleep(random.uniform(1, 3))
        jantar.tempos[id]["pensando"] += time.time() - inicio_pensar
        jantar.atualiza_interface()

        # Filósofo com fome
        estado[id]= Estado.COM_FOME
        jantar.atualizar_estado(id, "Com fome")
        print(f"{cores[id]}Filósofo {id+1} está com fome. \n")
        inicio_espera = time.time()
        tempo_esperando = 0

        # Adiciona o filósofo na fila de prioridade
        adicionar_filosofo_na_fila(id, tempo_esperando)

        while tempo_esperando < TEMPO_MAX_ESPERA:
            with mutex:
                # Verifica se é a vez do filósofo comer
                if id == proximo_filosofo_na_fila() and pode_comer(id):
                    estado[id] = Estado.COMENDO
                    jantar.atualizar_estado(id, "Comendo")
                    # Corrigindo a atualização dos garfos
                    garfo_esquerda = (id - 1) % NUM_FILOSOFOS  # Calcula o ID do garfo à esquerda
                    jantar.atualizar_garfo(garfo_esquerda, "ocupado")  # Atualiza o garfo à esquerda
                    jantar.atualizar_garfo(id, "ocupado")  # Atualiza o garfo à direita

                    print(f"{cores[id]}Filósofo {id+1} está comendo. \n")
                    inicio_comer = time.time()
                    time.sleep(random.uniform(1, 3))
                    jantar.tempos[id]["comendo"] += time.time() - inicio_comer
                    jantar.atualiza_interface()

                    # Libera os garfos após comer
                    garfos[garfo_esquerda].release() 
                    garfos[id].release()

                    # Corrigindo a liberação dos garfos
                    jantar.atualizar_garfo(garfo_esquerda, "livre")  # Libera o garfo à esquerda
                    jantar.atualizar_garfo(id, "livre")  # Libera o garfo à direita

                    estado[id] = Estado.PENSANDO
                    refeicoes[id] += 1  # Incrementa o contador de refeições
                    ciclos += 1
                    break
                else:
                    time.sleep(0.1)
                    tempo_esperando += 0.1
                    jantar.tempos[id]["esperando"] += 0.1
                    jantar.atualiza_interface()
                    # Atualiza o tempo de espera na fila de prioridade
                    adicionar_filosofo_na_fila(id, tempo_esperando)

        if tempo_esperando >= TEMPO_MAX_ESPERA:
            print(f"Filósofo {id+1} desistiu de comer por agora (starvation).\n")
            
    jantar.atualizar_estado(id, "Terminado") 
    # Relatório final do filósofo
    relatorios_finais.append((id, f"{cores[id]}=== Relatório Filósofo {id + 1} ===\n"
                                  f"Tempo pensando: {jantar.tempos[id]['pensando']:.2f} segundos\n"
                                  f"Tempo esperando: {jantar.tempos[id]['esperando']:.2f} segundos\n"
                                  f"Tempo comendo: {jantar.tempos[id]['comendo']:.2f} segundos\n"
                                  "=========================\n"))
    
# Função principal para iniciar o jantar e a interface
def main():
    root = tk.Tk()
    jantar = JantarFilosofos(root)

    threads = []
    relatorios_finais = []
    for i in range(NUM_FILOSOFOS):
        t = threading.Thread(target=filosofo, args=(i, jantar, MAX_CICLOS, relatorios_finais))
        threads.append(t)
        t.start()

    root.mainloop()

    for t in threads:
        t.join()

    for id, relatorio in relatorios_finais:
        print(relatorio)


if __name__ == "__main__":
    main()
