<div align="center">

# ⌁ Núcleo Link | Server / Servidor

### Messaging between Cardputer V1, Cardputer ADV and web browsers
### Mensagens entre Cardputer V1, Cardputer ADV e navegadores

**Lightweight Python server · Approval-based pairing · Web interface · LAN P2P directory**  
**Servidor Python leve · Pareamento com aprovação · Interface web · Diretório P2P LAN**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Mint%20%7C%20Ubuntu-87CF3E?logo=linux&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-596579)
![Access](https://img.shields.io/badge/Access-local%20by%20default-11785c)

</div>

---

**EN:** **Núcleo Link** lets Cardputer V1, Cardputer ADV and browser users join messaging rooms. This repository contains **the server only**. It does not install Arduino or PlatformIO and **does not compile firmware**.

**PT-BR:** O **Núcleo Link** permite que usuários do Cardputer V1, Cardputer ADV ou de um navegador participem de salas de mensagens. Este repositório contém **somente o servidor**. Não instala Arduino, não baixa PlatformIO e **não compila o firmware**.

> 🔐 **Security notice / Aviso de segurança**  
> **EN:** Server v3 uses per-device authentication and can use HTTPS when a tunnel is enabled. **Messages sent through the relay are NOT end-to-end encrypted.** The server can read them in the SQLite database. UDP P2P is a firmware-dependent LAN feature, not universal P2P across external networks. Do not use it for sensitive information.  
> **PT-BR:** O servidor v3 usa autenticação por dispositivo e pode usar HTTPS quando um túnel for ativado. **As mensagens enviadas pelo relay NÃO têm criptografia ponta a ponta.** O servidor pode lê-las no banco SQLite. O P2P UDP é um modo LAN dependente do firmware, não um P2P universal entre redes externas. Não use para conteúdo sigiloso.

## 🚀 One-command installation / Instalação em um comando

**EN:** On Linux Mint or Ubuntu, download or clone this folder and run the following command inside it.  
**PT-BR:** No Linux Mint ou Ubuntu, baixe ou clone esta pasta e execute dentro dela:

```bash
bash instalar_servidor.sh
```

**EN:** The installer only requires Python 3.9+ (standard library), does not require `sudo`, backs up existing files and installs the server in:  
**PT-BR:** O instalador usa apenas Python 3.9+ (biblioteca padrão), não exige `sudo`, faz backup dos arquivos existentes e instala o servidor em:

```text
~/NucleoLink/
```

**EN:** **Ready:** open [http://127.0.0.1:18781](http://127.0.0.1:18781). The server initially listens only on the local computer. No router port is opened. If another unknown process occupies the port, installation **stops instead of terminating it without permission**, and displays diagnostics.  
**PT-BR:** **Pronto:** abra [http://127.0.0.1:18781](http://127.0.0.1:18781). O servidor inicia restrito ao próprio computador. Nenhuma porta do roteador é aberta. Se a porta já estiver ocupada por um processo desconhecido, a instalação **interrompe em vez de encerrá-lo sem autorização**. O diagnóstico aparece no terminal.

## 🧭 Repository layout / Estrutura do repositório

```text
NucleoLink_Servidor_GitHub/
├── instalar_servidor.sh       # instala e inicia o servidor, sem firmware
├── start.sh                  # inicia local; túnel apenas se solicitado
├── stop.sh                   # encerra processos iniciados pelo projeto
├── status.sh                 # verifica a API
├── criar_sala.sh             # cria convite
├── aprovar.sh                # aprova código mostrado no dispositivo
├── revogar.sh                # lista e revoga credenciais
├── server/app.py             # API Python + SQLite + descoberta LAN
├── web/                      # interface HTML/CSS/JS
├── tests/test_server.py      # teste de integração
├── firmware/builds/          # opcional: arquivos .bin prontos
├── README.md
├── PUBLICAR_NO_GITHUB.md
├── .gitignore
└── LICENSE
```

**EN:** Server data is stored **outside this source-code package**, under `~/NucleoLink/data/` after installation. The `.gitignore` excludes `data/`, `logs/`, `backups/` and tokens.  
**PT-BR:** O servidor guarda os dados **fora deste pacote de código-fonte**, na instalação em `~/NucleoLink/data/`; `data/`, `logs/`, `backups/` e tokens estão protegidos pelo `.gitignore`.

## 💬 Usage / Operação

**EN:** Use the commands below to check status, create rooms, approve or revoke devices, and stop or restart the server.  
**PT-BR:** Use os comandos abaixo para verificar o estado, criar salas, aprovar ou revogar dispositivos e parar ou reiniciar o servidor.

```bash
bash ~/NucleoLink/status.sh          # estado
bash ~/NucleoLink/criar_sala.sh      # criar sala e convite
bash ~/NucleoLink/aprovar.sh CODIGO  # aprovar um Cardputer/navegador
bash ~/NucleoLink/revogar.sh         # listar dispositivos
bash ~/NucleoLink/revogar.sh ID      # revogar um dispositivo
bash ~/NucleoLink/stop.sh           # parar o servidor
bash ~/NucleoLink/start.sh          # iniciar novamente (inclusive apos reiniciar o PC)
```

**EN:** When a device joins with an invitation, it displays a temporary **10-digit code**. The server owner compares the code with the one on the device and approves it in the terminal. An invitation without approval does not grant message-reading access. Browsers also need approval. Never approve an unknown request: verify the user and device first.  
**PT-BR:** Ao conectar com um convite, o dispositivo exibe um código temporário de **10 dígitos**. O proprietário do servidor compara o código no aparelho com o informado e aprova no terminal. Um convite sem aprovação não dá acesso à leitura de mensagens. O navegador também pede aprovação. Não aprove códigos enviados por desconhecidos: confirme o dispositivo e o usuário antes de autorizar.

## 🌍 Communication across different networks (optional) / Acesso entre redes diferentes (opcional)

**EN:** By default, the server listens on `127.0.0.1`. Cardputers on different external networks require a public HTTPS route or an approved private network. **Installing the server does not automatically expose it to the internet.**  
**PT-BR:** O servidor foi configurado para escutar apenas em `127.0.0.1`. Para Cardputers em redes externas diferentes, é necessário um caminho público HTTPS ou uma rede privada aprovada. **Instalar o servidor não o coloca na internet automaticamente.**

**EN:** After installing `cloudflared` from its official distribution, or placing its executable at `~/NucleoLink/bin/cloudflared`, run:  
**PT-BR:** Depois de instalar `cloudflared` pela distribuição oficial, ou colocar o executável em `~/NucleoLink/bin/cloudflared`, execute:

```bash
LINK_PUBLIC=1 bash ~/NucleoLink/start.sh
```

**EN:** The temporary `https://....trycloudflare.com` address will appear in the terminal and in `~/NucleoLink/public_url.txt`. To disable it:  
**PT-BR:** O endereço `https://....trycloudflare.com` temporário aparecerá no terminal e em `~/NucleoLink/public_url.txt`. Para desligá-lo:

```bash
bash ~/NucleoLink/stop.sh
bash ~/NucleoLink/start.sh
```

**EN:** With the public tunnel active, anyone who discovers the URL can reach the API, but sending and reading room messages requires authentication. This **does not eliminate** DoS, credential leaks or software vulnerabilities. Do not expose this version for sensitive messages.  
**PT-BR:** Quando o túnel público está ativo, qualquer pessoa que descubra o endereço consegue alcançar a API, mas o envio/leitura das salas requer autenticação. Isso **não elimina** riscos de DoS, vazamento de credenciais ou falhas de software. Não exponha essa versão para mensagens sensíveis.

**EN, LAN P2P:** The server provides peer discovery (`/api/p2p/announce` and `/api/p2p/peers`), while Cardputers exchange UDP packets directly on port 18782. This does not open a UDP port on the server or router. Use the relay between different external networks. Compatible firmware is required.  
**PT-BR, P2P LAN:** O servidor disponibiliza descoberta de pares (`/api/p2p/announce` e `/api/p2p/peers`), mas os próprios Cardputers realizam a troca UDP na porta 18782. A porta UDP não é aberta no servidor nem no roteador. Em redes externas diferentes, use o relay. Sem firmware compatível, as rotas P2P não bastam para estabelecer comunicação.

## 📦 Firmware `.bin` location / Onde adicionar os arquivos `.bin`

**EN:** To publish the two separately compiled firmware images alongside the server, put them **in this repository folder**:  
**PT-BR:** Para publicar junto do servidor dois firmwares compilados separadamente, adicione-os **na pasta deste repositório**:

```text
firmware/builds/cardputer_v1.bin
firmware/builds/cardputer_adv.bin
```

**EN:** Or, on the computer where the server is installed:  
**PT-BR:** Ou, no computador em que o servidor foi instalado:

```text
~/NucleoLink/firmware/builds/cardputer_v1.bin
~/NucleoLink/firmware/builds/cardputer_adv.bin
```

**EN:** The installer **does not produce `.bin` files**. The package ships without firmware. Do not flash an older `.bin` unless it has been validated against the v3 pairing endpoints and the correct hardware variant. See `firmware/builds/README.md`.  
**PT-BR:** O instalador **não produz `.bin`**. A pasta vem sem firmware. Não use `.bin` antigo, que não tenha sido validado com os endpoints de pareamento v3 e a variante do aparelho. Consulte `firmware/builds/README.md`.

## 🔍 Current security and limitations / Segurança e limites atuais

**EN:**

- **Included:** individual credentials, device approval, revocation, basic rate limiting, maximum message sizes, input validation, SQLite, loopback binding, security headers and an interface resource policy.
- **Not included:** relay end-to-end encryption, formal security proof, comprehensive DDoS mitigation, NAT traversal between external networks, guaranteed working `.bin` images or UDP delivery guarantees.
- Room data and invitations are sensitive. **Never run `git add -f data/` or publish `admin.token`, SQLite files, logs, keys or backups.**

**PT-BR:**

- **Incluído:** credenciais individuais, autorização de dispositivo, revogação, controle básico de frequência, tamanho máximo de mensagens, validação de entrada, banco SQLite, bind em loopback, cabeçalhos de segurança e política de recursos da interface.
- **Não incluído:** criptografia ponta a ponta no relay, prova formal de segurança, mitigação abrangente de DDoS, NAT traversal entre redes externas, fornecimento de `.bin` funcional ou garantia de entrega de pacotes UDP.
- Dados e convites são secretos. **Nunca faça `git add -f data/` nem publique `admin.token`, arquivos SQLite, logs, chaves ou backup.**

## 🧪 Tests / Testes

```bash
python3 tests/test_server.py
bash ~/NucleoLink/status.sh
```

**EN:** These tests verify basic server functionality, but do not replace security audits, hardware testing or production monitoring.  
**PT-BR:** Os testes verificam as funções básicas do servidor, mas não substituem auditoria de segurança, testes no hardware e monitoramento de produção.


