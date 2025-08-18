# Win32 API Scraper

Um programa Python para fazer scraping da documentação Win32 API da Microsoft Learn e extrair informações detalhadas sobre funções.

## Funcionalidades

- **DLL/Biblioteca**: Identifica qual DLL contém a função (ex: kernel32.dll)
- **Calling Convention**: Determina a convenção de chamada (__stdcall)
- **Parâmetros**: Extrai número e detalhes de todos os parâmetros
- **Arquiteturas**: Identifica suporte para x86/x64
- **Signature**: Mostra a assinatura completa da função formatada
- **Explicações**: Descrição detalhada de cada parâmetro e valor de retorno
- **Formatação Rich**: Exibição colorida e bem formatada no terminal

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### Comando básico
```bash
python win32_scraper.py CreateProcessW
```

### Opções de saída
```bash
# Saída formatada com Rich (padrão)
python win32_scraper.py CreateProcessW --output rich

# Saída em JSON
python win32_scraper.py CreateProcessW --output json

# Saída em Markdown  
python win32_scraper.py CreateProcessW --output markdown
```

## Exemplo de saída

O programa extrai e exibe:

- **Informações básicas**: DLL, calling convention, número de parâmetros, arquiteturas, tipo de retorno
- **Assinatura da função**: Código C formatado com syntax highlighting
- **Descrição**: Explicação do que a função faz
- **Parâmetros**: Tabela detalhada com nome, tipo e descrição de cada parâmetro
- **Valor de retorno**: Explicação do que a função retorna e condições de sucesso/erro

## Funções suportadas

Atualmente implementado para:
- ✅ CreateProcessW

Facilmente extensível para outras funções Win32 API.

## Estrutura do projeto

```
manw/
├── win32_scraper.py    # Script principal
├── requirements.txt    # Dependências Python
└── README.md          # Esta documentação
```

## Dependências

- `requests`: Para requisições HTTP
- `beautifulsoup4`: Para parsing HTML
- `rich`: Para formatação rica no terminal
- `lxml`: Parser XML/HTML