import threading
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

class ProxyViewerApp:
    def __init__(self):
        self.proxies = []
        self.drivers = []  # Lista para armazenar as instâncias de drivers
        self.logs = []  # Armazena os logs separadamente

    def log(self, message):
        """Exibe e armazena mensagens no console."""
        log_message = f"[LOG] {message}"
        self.logs.append(log_message)
        print(log_message)

    def show_logs(self):
        """Exibe todos os logs armazenados."""
        print("\n=== Logs do Sistema ===")
        for log_message in self.logs:
            print(log_message)
        print("========================\n")

    def add_proxies(self, proxies):
        """Adiciona e valida os proxies fornecidos."""
        self.proxies = [proxy.strip() for proxy in proxies if proxy.strip()]
        self.log(f"{len(self.proxies)} proxies encontrados. Testando...")

        valid_proxies = []

        for proxy in self.proxies:
            if self.test_proxy(proxy):
                valid_proxies.append(proxy)
                self.log(f"Proxy válido: {proxy}")
            else:
                self.log(f"Proxy inválido: {proxy}")

        self.proxies = valid_proxies
        self.log(f"{len(self.proxies)} proxies válidos adicionados.")

    def test_proxy(self, proxy):
        """Testa se o proxy está funcionando."""
        try:
            proxies = {"http": proxy, "https": proxy}
            response = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def open_windows(self, urls, tabs_count):
        """Abre janelas para gerar visualizações."""
        if not urls:
            self.log("Erro: Nenhuma URL fornecida.")
            return

        if tabs_count <= 0:
            self.log("Erro: Quantidade inválida de janelas.")
            return

        if len(self.proxies) < tabs_count:
            self.log("Erro: Proxies insuficientes para a quantidade de janelas.")
            return

        self.log(f"Iniciando a abertura de {tabs_count} janelas para {len(urls)} URL(s)...")
        threading.Thread(target=self.launch_browsers, args=(urls, tabs_count)).start()

    def launch_browsers(self, urls, tabs_count):
        """Lança as janelas do navegador uma a uma."""
        url_index = 0
        for i in range(tabs_count):
            proxy = self.proxies[i]
            url = urls[url_index]
            url_index = (url_index + 1) % len(urls)  # Alterna entre as URLs fornecidas

            self.log(f"Configurando proxy: {proxy} para URL: {url}")

            try:
                # Configurações do navegador
                options = Options()
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--mute-audio")  # Desativa o áudio
                options.add_argument("--disable-popup-blocking")  # Bloqueia pop-ups

                # Criando perfis de usuário únicos
                user_data_dir = os.path.join(os.getcwd(), f"user_data_{i}")
                if not os.path.exists(user_data_dir):
                    os.makedirs(user_data_dir)
                options.add_argument(f"--user-data-dir={user_data_dir}")

                # Configura proxy com ou sem autenticação
                if "@" in proxy:
                    proxy_parts = proxy.split("@")
                    ip_port = proxy_parts[1]
                    options.add_argument(f"--proxy-server=http://{ip_port}")
                else:
                    options.add_argument(f"--proxy-server={proxy}")

                # Inicia o navegador
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                driver.set_window_position(i * 200, i * 200)  # Ajuste para não sobrepor as janelas
                driver.set_window_size(300, 300)  # Define um tamanho fixo para a janela
                driver.get(url)

                self.log(f"Janela {i + 1} aberta com proxy {proxy} para URL: {url}.")

                # Adiciona o driver à lista de instâncias abertas
                self.drivers.append(driver)

                # Inicia reprodução infinita
                threading.Thread(target=self.keep_video_playing, args=(driver, url)).start()

            except Exception as e:
                self.log(f"Erro ao abrir janela com proxy {proxy}: {str(e)}")

    def keep_video_playing(self, driver, url):
        """Garante que o vídeo está sendo reproduzido continuamente."""
        while True:
            try:
                # Verifica se a página ainda está ativa
                driver.title

                # Reinicia o vídeo se necessário
                video_element = driver.find_element(By.TAG_NAME, "video")
                if video_element:
                    is_paused = driver.execute_script("return arguments[0].paused;", video_element)
                    if is_paused:
                        driver.execute_script("arguments[0].play();", video_element)
                time.sleep(5)  # Verifica a cada 5 segundos
            except Exception as e:
                self.log(f"Erro ao manter vídeo em execução: {str(e)}")
                break

    def close_all_windows(self):
        """Fecha todas as janelas abertas."""
        self.log("Fechando todas as janelas abertas...")
        for driver in self.drivers:
            try:
                driver.quit()
                self.log("Janela fechada com sucesso.")
            except Exception as e:
                self.log(f"Erro ao fechar janela: {str(e)}")
        self.drivers = []

if __name__ == "__main__":
    app = ProxyViewerApp()

    while True:
        print("\n=== Painel de Controle ===")
        print("1. Adicionar Proxies")
        print("2. Abrir Janelas")
        print("3. Fechar Todas as Janelas")
        print("4. Exibir Logs")
        print("5. Sair")
        choice = input("Escolha uma opção: ")

        if choice == "1":
            proxies = input("Insira a lista de proxies (separados por vírgula): ").split(",")
            app.add_proxies(proxies)
        elif choice == "2":
            urls = input("Insira as URLs dos vídeos (separadas por vírgula): ").split(",")
            tabs_count = int(input("Quantidade de janelas para abrir: "))
            app.open_windows(urls, tabs_count)
        elif choice == "3":
            app.close_all_windows()
        elif choice == "4":
            app.show_logs()
        elif choice == "5":
            app.close_all_windows()
            break
        else:
            print("Opção inválida. Tente novamente.")
