🚀 Lathon LaTeX Editor v1.0.1 - Guia de Início Rápido
O Lathon é um editor de LaTeX leve e portátil que usa o compilador MikTex. Este pacote já contém tudo o que você precisa para começar a escrever seus documentos científicos de forma produtiva.

📁 Estrutura deste Pacote:
lathon.exe: O editor principal.

miktex/: Pasta destinada ao compilador portátil.

ReadMe.txt: Este guia.

🛠️ Instruções de Uso:
Instalação do MiKTeX:

Este pacote foi testado especificamente com o MiKTeX Portable Edition.

Download MiKTeX: https://miktex.org/download

Após baixar execute o miktex-portable.exe.

Instale o MiKTeX Portable dentro da pasta miktex/ deste pacote.

Caso ja tenha instalado no seu PC arraste miktex-portable.cmd e texmfs para pasta miktex/ deste pacote.

Ao abrir o lathon.exe, ele detectará automaticamente o compilador vizinho.

⚠️ Nota sobre Pacotes Adicionais (MiKTeX)
O LaTeX funciona através de pacotes. Se o seu documento exigir algo que ainda não está na sua pasta miktex/, o gerenciador do MiKTeX abrirá uma janela perguntando se você deseja instalar o pacote.

O que fazer? Apenas clique em "Install".

Como automatizar? Se não quiser que essa janela apareça novamente, marque a opção "Always show this dialog" como desmarcada ou configure o MiKTeX Console para "Always install missing packages on-the-fly".

Internet: Lembre-se que o MiKTeX precisa de conexão com a internet apenas no momento em que baixa um novo pacote pela primeira vez.

--> Primeira Compilação:

Abra ou crie um arquivo .tex.

Pressione Ctrl+S ou clique em ▶ Compile.

Se o MiKTeX solicitar a instalação de pacotes (Missing Packages), clique em Install. O Lathon exibirá um aviso de download no painel inferior.

No primeiro uso a compilação vai demorar um pouco mais. O miktex precisa instalar as bibliotecas novas.

✨ O que há de novo na v1.0.1:
Assistentes de Edição: Corretor ortográfico e autocompletar integrados no menu "Opções".

Marcações Coloridas: Clique com o botão direito no texto selecionado para destacar trechos e adicionar comentários.

Navegação: Use "Ver Lista de Marcações" para gerenciar todas as suas anotações no documento.

🐛 Suporte e Sugestões:
Encontrou um bug ou tem uma ideia fantástica? Entre em contato com o desenvolvedor! Seu feedback é essencial para as próximas versões.

Desenvolvido por Murilo Campos.

