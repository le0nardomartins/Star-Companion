# Como Usar o StarCompanion

## Instalação

1. Clique duas vezes no arquivo `instalar.bat` para iniciar o processo de instalação
2. O script irá:
   - Instalar as dependências necessárias
   - Criar um arquivo executável (.exe)
   - Configurar o programa para iniciar automaticamente com o Windows
   - Iniciar o programa imediatamente

## Após a Instalação

Após a instalação, o StarCompanion:

- Será iniciado automaticamente sempre que você ligar o computador
- Ficará ativo indefinidamente até que você o encerre
- Mostrará apenas uma mensagem de inicialização no terminal (se aberto a partir do executável)

## Como Encerrar o Programa

Para encerrar o programa, execute o `encerrar.bat`. 
Atenção: todos os precessos python serão encerrados. 

## Desinstalação

Se desejar remover o programa:

1. Clique duas vezes no arquivo `desinstalar.bat`
2. O script irá:
   - Remover o programa da inicialização automática do Windows
   - Encerrar o programa se estiver em execução
   - Excluir o arquivo executável

## Solução de Problemas

Se a estrela não aparecer:

1. Verifique se o processo `StarCompanion.exe` está em execução no Gerenciador de Tarefas
2. Se não estiver, execute manualmente o arquivo `dist\StarCompanion.exe`
3. Se ainda houver problemas, reinstale usando o arquivo `instalar.bat`

## Personalização

Para personalizar a aparência e comportamento da estrela:

1. Edite o arquivo `star_config.json` com um editor de texto
2. Reinstale o programa usando `instalar.bat` para aplicar as alterações 