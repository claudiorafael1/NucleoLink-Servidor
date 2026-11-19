<div align="center">

# ⌁ Núcleo Link | Servidor

### Mensagens entre Cardputer V1, Cardputer ADV e navegadores

**Servidor Python leve · Pareamento com aprovação · Interface web · Diretório P2P LAN**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Mint%20%7C%20Ubuntu-87CF3E?logo=linux&logoColor=white)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-596579)
![Acesso](https://img.shields.io/badge/Acesso-local%20por%20padr%C3%A3o-11785c)

</div>

---

O **Núcleo Link** permite que usuários do Cardputer V1, Cardputer ADV ou de um navegador participem de salas de mensagens. Este repositório contém **somente o servidor**. Não instala Arduino, não baixa PlatformIO e **não compila o firmware**.

> 🔐 **Aviso de segurança:** o servidor v3 usa autenticação por dispositivo e pode usar HTTPS quando um túnel for ativado. **As mensagens enviadas pelo relay NÃO têm criptografia ponta a ponta**. O servidor pode lê-las no banco SQLite. O P2P UDP é um modo LAN dependente do firmware, não um P2P universal entre redes externas. Não use para conteúdo sigiloso.

## 🚀 Instalação em um comando

No Linux Mint ou Ubuntu, baixe ou clone esta pasta e execute dentro dela:

```bash
bash instalar_servidor.sh
```

O instalador usa apenas Python 3.9+ (biblioteca padrão), não exige `sudo`, faz backup dos arquivos existentes e instala o servidor em:

```text
~/NucleoLink/
```

**Pronto:** abra [http://127.0.0.1:18781](http://127.0.0.1:18781). O servidor inicia restrito ao próprio computador. Nenhuma porta do roteador é aberta.

Se a porta já estiver ocupada por um processo desconhecido, a instalação **interrompe em vez de encerrá-lo sem autorização**. O diagnóstico aparece no terminal.

## 🧭 Estrutura do repositório

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

O servidor guarda os dados **fora deste pacote de código-fonte**, na instalação em `~/NucleoLink/data/`; `data/`, `logs/`, `backups/` e tokens estão protegidos pelo `.gitignore`.

## 💬 Operação

```bash
bash ~/NucleoLink/status.sh          # estado
bash ~/NucleoLink/criar_sala.sh      # criar sala e convite
bash ~/NucleoLink/aprovar.sh CODIGO  # aprovar um Cardputer/navegador
bash ~/NucleoLink/revogar.sh         # listar dispositivos
bash ~/NucleoLink/revogar.sh ID      # revogar um dispositivo
bash ~/NucleoLink/stop.sh           # parar o servidor
bash ~/NucleoLink/start.sh          # iniciar novamente (inclusive apos reiniciar o PC)
```

Ao conectar com um convite, o dispositivo exibe um código temporário de **10 dígitos**. O proprietário do servidor compara o código no aparelho com o informado e aprova no terminal. Um convite sem aprovação não dá acesso à leitura de mensagens.

> O navegador também pede aprovação. Não aprove códigos enviados por desconhecidos: confirme o dispositivo e o usuário antes de autorizar.

## 🌍 Acesso entre redes diferentes (opcional)

O servidor foi configurado para escutar apenas em `127.0.0.1`. Para Cardputers em redes externas diferentes, é necessário um caminho público HTTPS ou uma rede privada aprovada. **Instalar o servidor não o coloca na internet automaticamente.**

Depois de instalar `cloudflared` pela distribuição oficial, ou colocar o executável em `~/NucleoLink/bin/cloudflared`, execute:

```bash
LINK_PUBLIC=1 bash ~/NucleoLink/start.sh
```

O endereço `https://....trycloudflare.com` temporário aparecerá no terminal e em `~/NucleoLink/public_url.txt`. Para desligá-lo:

```bash
bash ~/NucleoLink/stop.sh
bash ~/NucleoLink/start.sh
```

Quando o túnel público está ativo, qualquer pessoa que descubra o endereço consegue alcançar a API, mas o envio/leitura das salas requer autenticação. Isso **não elimina** riscos de DoS, vazamento de credenciais ou falhas de software. Não exponha essa versão para mensagens sensíveis.

**P2P LAN:** o servidor disponibiliza descoberta de pares (`/api/p2p/announce` e `/api/p2p/peers`), mas os próprios Cardputers realizam a troca UDP na porta 18782. A porta UDP não é aberta no servidor nem no roteador. Em redes externas diferentes, use o relay. Sem firmware compatível, as rotas P2P não bastam para estabelecer comunicação.

## 📦 Onde adicionar os arquivos `.bin`

Para publicar junto do servidor dois firmwares compilados separadamente, adicione-os **na pasta deste repositório**:

```text
firmware/builds/cardputer_v1.bin
firmware/builds/cardputer_adv.bin
```

Ou, no computador em que o servidor foi instalado:

```text
~/NucleoLink/firmware/builds/cardputer_v1.bin
~/NucleoLink/firmware/builds/cardputer_adv.bin
```

O instalador **não produz `.bin`**. A pasta vem sem firmware. Não use `.bin` antigo, que não tenha sido validado com os endpoints de pareamento v3 e a variante do aparelho. Consulte `firmware/builds/README.md`.

## 🔍 Segurança e limites atuais

- **Incluído:** credenciais individuais, autorização de dispositivo, revogação, controle básico de frequência, tamanho máximo de mensagens, validação de entrada, banco SQLite, bind em loopback, cabeçalhos de segurança e política de recursos da interface.
- **Não incluído:** criptografia ponta a ponta no relay, prova formal de segurança, mitigação abrangente de DDoS, NAT traversal entre redes externas, fornecimento de `.bin` funcional ou garantia de entrega de pacotes UDP.
- Dados e convites são secretos. **Nunca faça `git add -f data/` nem publique `admin.token`, arquivos SQLite, logs, chaves ou backup.**

## 🧪 Testes

```bash
python3 tests/test_server.py
bash ~/NucleoLink/status.sh
```

Os testes verificam as funções básicas do servidor, mas não substituem auditoria de segurança, testes no hardware e monitoramento de produção.

## 📚 Publicação e licença

Consulte [PUBLICAR_NO_GITHUB.md](PUBLICAR_NO_GITHUB.md) para instruções por terminal e pelo navegador, e [LICENSE](LICENSE) para os termos MIT.
