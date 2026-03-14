# LaThon - LaTeX Editor

O **LaThon** é um editor LaTeX de desktop moderno, leve e construído inteiramente em Python.

## 📦 Apenas quer usar o editor?
Vá até a aba **Releases** e baixe o arquivo `.zip` mais recente. Dentro do pacote, você encontrará o executável e um arquivo `ReadMe.txt` com todas as instruções de uso.

## 🛠️ Para Desenvolvedores (Rodando do código-fonte)
**Pré-requisitos:** 
1. Python 3.9+ e compilador 
2. MiKTeX Portable (extraído na pasta `miktex/` na raiz do projeto).

**Como rodar:**
1. Instale as dependências: `pip install -r requirements.txt`
2. Execute o editor: `python run.py`

## 🏗️ Como Compilar e Gerar o Release (.exe e .zip)
1. Certifique-se de ter o `pyinstaller` instalado no seu ambiente.
2. No Windows, execute o script de build: `lathon.bat`
3. O script fará a limpeza, usará o `lathon.spec` para gerar o `lathon.exe`, copiará o `ReadMe.txt` e compactará tudo. O arquivo final `.zip` ficará na pasta `release/`.