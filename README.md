# Star Companion

Uma estrela animada que segue o cursor do mouse e reage a cliques e digitação.

## Instalação Rápida

1. Execute `instalar.bat` como administrador
2. Aguarde a conclusão da instalação
3. O programa será iniciado automaticamente

## Estrutura de Arquivos

```
StarCompanion/
├── assets/
│   └── config/           # Arquivos de configuração
│       └── star_config.json
├── bin/                  # Executáveis e scripts de execução
│   ├── executar.py
│   └── StarCompanion.exe
├── docs/                 # Documentação
│   ├── README.md
│   └── como_usar.md
├── modules/              # Módulos de instalação
│   ├── setup.py
│   └── requirements.txt
├── src/                  # Código-fonte
│   └── main.py
├── dist/                 # Pasta gerada durante a instalação
├── instalar.bat          # Script de instalação
├── desinstalar.bat       # Script de desinstalação
├── executar.bat          # Script para execução
└── README.md             # Este arquivo
```

## Instalação

Para instalar o programa como um executável que inicia automaticamente com o Windows:

1. Execute o arquivo `instalar.bat` como administrador
   Este processo irá:
   - Instalar as dependências necessárias
   - Criar um arquivo executável usando PyInstaller
   - Configurar o programa para iniciar automaticamente com o Windows
   - Colocar o executável na pasta "bin" e "dist"

## Uso

Após a instalação, o programa será iniciado automaticamente sempre que você ligar o computador.

Para executar manualmente:
- Execute o arquivo `executar.bat` na raiz do projeto

Para sair do programa:
- Pressione a tecla **ESC**

## Configuração

As configurações podem ser personalizadas editando o arquivo `assets/config/star_config.json`.

## Desinstalação

Para desinstalar o programa, execute o arquivo `desinstalar.bat` como administrador.

O script irá:
- Remover o programa da inicialização automática do Windows
- Encerrar o programa se estiver em execução
- Excluir os executáveis das pastas bin e dist

## Características

- Estrela que segue o cursor do mouse com movimento suave
- Efeitos de brilho e partículas
- Mudança de cor ao clicar (azul para violeta)
- Sistema de aceleração quando o cursor se move rapidamente
- Efeitos de partículas e rastros personalizáveis
- Configuração flexível através de arquivo JSON

## Requisitos

- Python 3.8 ou superior
- Windows (usa win32api para rastreamento do mouse)
- Tkinter (geralmente já vem com Python)

- `src/main.py`: Código principal da aplicação
- `star_config.json`: Arquivo de configuração
- `requirements.txt`: Lista de dependências

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 
