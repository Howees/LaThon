import json
from pathlib import Path


class ConfigManager:
    """
    Classe central responsável por gerenciar toda a leitura
    e escrita do arquivo único de configuração (config.json) do LaThon.
    """

    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        # 1. Definimos a pasta de configuração
        self.config_dir = self.base_dir / "config"
        self.config_file = self.config_dir / "config.json"

        # 2. Criamos a pasta caso ela não exista (parents=True evita erros)
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)

        # 3. Cria o arquivo padrão se ele não existir
        if not self.config_file.exists():
            self._save_all(self._get_default_structure())

    def _get_default_structure(self):
        """Retorna a estrutura base com comentários simulados para organizar o JSON."""
        return {
            "_comment_recents": "Lista dos ultimos projetos abertos (maximo 5)",
            "recents": [],

            "_comment_layout": "Configuracoes de proporcao dos paineis (%) e fonte do editor",
            "layout": {
                "left": 15,
                "center": 50,
                "pdf": 35,
                "font_family": "Consolas",
                "font_size": 12
            },

            "_comment_spell": "Preferencias de idiomas do corretor e dicionario de palavras personalizadas",
            "spell": {
                "is_configured": False,
                "enabled_languages": ["pt"],
                "custom_words": []
            }
        }

    def _load_all(self):
        """Lê o arquivo de configuração inteiro."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return self._get_default_structure()

    def _save_all(self, data):
        """Salva a estrutura completa no arquivo JSON formatado."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    # ==========================================
    # PROJETOS RECENTES
    # ==========================================
    def get_recents(self):
        data = self._load_all()
        return data.get("recents", [])

    def add_recent(self, project_path):
        data = self._load_all()
        recents = data.get("recents", [])
        str_path = str(project_path)

        if str_path in recents:
            recents.remove(str_path)

        recents.insert(0, str_path)
        data["recents"] = recents[:5]  # Mantém apenas os 5 mais recentes
        self._save_all(data)

    # ==========================================
    # LAYOUT DA TELA E FONTES
    # ==========================================
    def get_layout(self):
        data = self._load_all()
        layout_data = data.get("layout", {})

        # Fallbacks garantidos caso algo seja apagado do JSON manualmente
        if "center" not in layout_data:
            layout_data["center"] = 100 - layout_data.get("left", 15) - layout_data.get("pdf", 35)
        if "font_family" not in layout_data:
            layout_data["font_family"] = "Consolas"
        if "font_size" not in layout_data:
            layout_data["font_size"] = 12

        return layout_data

    def update_layout(self, **kwargs):
        """Exemplo de uso: update_layout(left=20, pdf=30) ou update_layout(font_size=14)"""
        data = self._load_all()
        if "layout" not in data:
            data["layout"] = {}

        data["layout"].update(kwargs)
        self._save_all(data)

    # ==========================================
    # CORRETOR ORTOGRÁFICO
    # ==========================================
    def get_spell(self):
        data = self._load_all()
        spell_data = data.get("spell", {})

        # Fallbacks
        if "is_configured" not in spell_data: spell_data["is_configured"] = False
        if "enabled_languages" not in spell_data: spell_data["enabled_languages"] = ["pt"]
        if "custom_words" not in spell_data: spell_data["custom_words"] = []

        return spell_data

    def update_spell(self, **kwargs):
        data = self._load_all()
        if "spell" not in data:
            data["spell"] = {}

        data["spell"].update(kwargs)
        self._save_all(data)

    # ==========================================
    # REPOSITÓRIOS (WORKSPACES)
    # ==========================================
    def get_last_workspace(self):
        """Retorna o último repositório acessado ou None."""
        data = self._load_all()
        return data.get("last_workspace", None)

    def get_recent_workspaces(self):
        """Retorna a lista de repositórios recentes."""
        data = self._load_all()
        return data.get("recent_workspaces", [])

    def add_workspace_to_history(self, path: str):
        """Adiciona um repositório ao histórico e define como o atual."""
        data = self._load_all()
        recents = data.get("recent_workspaces", [])

        if path in recents:
            recents.remove(path)
        recents.insert(0, path)  # Coloca no topo da lista

        # Mantém no máximo os 5 repositórios mais recentes para não poluir
        data["recent_workspaces"] = recents[:5]
        data["last_workspace"] = path
        self._save_all(data)

    def remove_workspace_from_history(self, path: str):
        """Remove um repositório do histórico (útil se o usuário quiser limpar)."""
        data = self._load_all()
        recents = data.get("recent_workspaces", [])

        if path in recents:
            recents.remove(path)

        # Se apagou o atual, reseta o último
        if data.get("last_workspace") == path:
            data["last_workspace"] = None

        data["recent_workspaces"] = recents
        self._save_all(data)

    def clear_last_workspace(self):
        """Limpa a memória do último repositório para forçar a tela inicial."""
        data = self._load_all()
        data["last_workspace"] = None
        self._save_all(data)

    def get_root_path(self):
        """Retorna a pasta principal (Cofre) onde ficam todos os repositórios."""
        data = self._load_all()
        return data.get("root_path", None)

    def set_root_path(self, path: str):
        """Salva a pasta principal (Cofre) no JSON."""
        data = self._load_all()
        data["root_path"] = path
        self._save_all(data)

    # ==========================================
    # MARCAÇÕES DO EDITOR (MARKERS)
    # ==========================================
    def get_file_markers(self, file_path: str):
        """Retorna a lista de marcações salvas de um arquivo específico."""
        data = self._load_all()
        markers_dict = data.get("markers", {})
        return markers_dict.get(file_path, [])

    def save_file_markers(self, file_path: str, markers_list: list):
        """Salva a lista de marcações de um arquivo."""
        data = self._load_all()
        if "markers" not in data:
            data["markers"] = {}
        data["markers"][file_path] = markers_list
        self._save_all(data)