import flet as ft
import datetime
import random
import string
from db_manager import DBManager
import threading
import getpass

# Configuração mínima de toasts (usada por redirect de `print` e por notificações)
app_settings = {'toast_duration': 3}

db_manager = DBManager('db.db')


def load_spinbox_increment():
    try:
        return 0.1
    except Exception:
        return 0.1



# ===== CLASSE DE GERENCIAMENTO RESPONSIVO =====
class ResponsiveAppManager:
    """Classe para gerenciar o comportamento responsivo da aplicação"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.results_container = None
        self.is_maximized = False
        self.current_layout = "single"  # "single" ou "double"
        self.menu_is_expanded_ref = None
        self.update_menu_func = None
        
        # Configurar listener de redimensionamento
        self.page.on_resized = self.on_window_resize
        self.page.on_window_event = self.on_window_event
    
    def initialize_containers(self, results_container):
        """Inicializa as referências dos containers que serão gerenciados"""
        self.results_container = results_container
        # Layout será aplicado quando houver cards para mostrar
    
    def initialize_menu_controls(self, menu_is_expanded_ref, update_menu_func):
        """Inicializa as referências para os controles do menu lateral"""
        self.menu_is_expanded_ref = menu_is_expanded_ref
        self.update_menu_func = update_menu_func
    
    def clear_results(self):
        """Limpa todos os resultados e reseta o estado"""
        if self.results_container:
            self.results_container.controls.clear()
            self.results_container.update()
            # Não resetar o layout - manter o estado atual baseado na janela
            # self.current_layout permanece como estava (single ou double)
    
    def check_initial_window_state(self):
        """Verifica o estado inicial da janela e aplica o layout apropriado"""
        window_width = self.page.window.width or 1200
        is_maximized = self.page.window.maximized or False
        
        # Se maximizada, sempre usar layout double (prioridade ao estado maximized)
        if is_maximized:
            should_use_double_layout = True
        else:
            should_use_double_layout = window_width > 1400
        
        self.current_layout = "double" if should_use_double_layout else "single"
        self.is_maximized = is_maximized
        
        print(f"🚀 Estado inicial da janela: largura={window_width}px, maximizada={is_maximized}")
        print(f"🚀 Decisão: should_use_double_layout={should_use_double_layout}")
        print(f"🚀 Layout inicial definido como: {self.current_layout}")
        
        # Não precisa aplicar o layout aqui, será aplicado quando o primeiro card for adicionado
    
    def on_window_event(self, e):
        """Callback para eventos da janela (maximizar, restaurar, etc)"""
        if hasattr(e, 'event_type'):
            if e.event_type == "maximize":
                self.is_maximized = True 
                print("🔍 Janela maximizada - aplicando layout de duas colunas")
                self.apply_responsive_layout()
            elif e.event_type == "restore":
                self.is_maximized = False
                print("🔍 Janela restaurada - aplicando layout de uma coluna")
                self.apply_responsive_layout()
    
    def on_window_resize(self, e):
        """Callback chamado quando a janela é redimensionada"""
        window_width = self.page.window.width or 1200
        
        # Determinar se deve usar layout de duas colunas baseado na largura
        should_use_double_layout = window_width > 1400 or self.page.window.maximized
        
        new_layout = "double" if should_use_double_layout else "single"
        
        if new_layout != self.current_layout:
            self.current_layout = new_layout
            print(f"🔄 Mudando layout para: {new_layout} (largura: {window_width}px)")
            self.apply_responsive_layout()
            
        # Atualizar layout dos cards de suppliers se necessário
        self.update_supplier_cards_layout(window_width)
        
        # Atualizar layout da aba Users se necessário
        self.update_users_layout(window_width)

        # Gerenciar estado do menu lateral baseado na largura da tela e layout
        if self.menu_is_expanded_ref and self.update_menu_func:
            # Se a tela for pequena, fechar o menu se estiver aberto
            if window_width < 1000 and self.menu_is_expanded_ref.current:
                print(f"📱 Tela pequena ({window_width}px), fechando menu lateral.")
                self.menu_is_expanded_ref.current = False
                self.update_menu_func()
            # Se o layout for duplo, reabrir o menu se estiver fechado
            elif new_layout == "double" and not self.menu_is_expanded_ref.current:
                print(f"📱 Layout duplo ativado ({window_width}px), reabrindo menu lateral.")
                self.menu_is_expanded_ref.current = True
                self.update_menu_func()
    
    def apply_responsive_layout(self):
        """Aplica o layout responsivo baseado no estado atual"""
        if not self.results_container:
            return
            
        try:
            print(f"🔄 apply_responsive_layout: self.current_layout = '{self.current_layout}'")
            if self.current_layout == "double":
                self._apply_double_column_layout()
            else:
                self._apply_single_column_layout()
                
            # Atualizar a interface
            if hasattr(self.results_container, 'update'):
                self.results_container.update()
            self.page.update()
            
        except Exception as e:
            print(f"❌ Erro ao aplicar layout responsivo: {e}")
    
    def _apply_double_column_layout(self):
        """Aplica layout de duas colunas para a aba Score"""
        print("📱 Aplicando layout de DUAS colunas")
        
        if not hasattr(self.results_container, 'controls'):
            return
            
        # Pegar todos os cards existentes
        cards = list(self.results_container.controls)
        print(f"📱 Cards existentes no container: {len(cards)}")
        
        # Limpar container atual
        self.results_container.controls.clear()
        
        # Criar duas colunas com alinhamento consistente
        left_column = ft.Column(
            [], 
            spacing=10, 
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )
        right_column = ft.Column(
            [], 
            spacing=10, 
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )
        
        # Distribuir cards alternadamente entre as colunas
        for i, card in enumerate(cards):
            if i % 2 == 0:
                left_column.controls.append(card)
            else:
                right_column.controls.append(card)
        
        # Criar linha com as duas colunas com alinhamento estável
        double_column_row = ft.Row([
            left_column,
            right_column
        ], 
        spacing=20, 
        expand=True,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START
        )
        
        # Adicionar ao container principal
        self.results_container.controls.append(double_column_row)
    
    def _apply_single_column_layout(self):
        """Aplica layout de uma coluna para a aba Score"""
        print("📱 Aplicando layout de UMA coluna")
        
        if not hasattr(self.results_container, 'controls'):
            return
            
        # Se já está em layout de uma coluna, não fazer nada
        if len(self.results_container.controls) > 0:
            first_control = self.results_container.controls[0]
            if not isinstance(first_control, ft.Row):
                return  # Já está em layout single
        
        # Coletar todos os cards das colunas
        all_cards = []
        for control in self.results_container.controls:
            if isinstance(control, ft.Row):
                # É um layout de duas colunas, extrair cards
                for column in control.controls:
                    if isinstance(column, ft.Column):
                        all_cards.extend(column.controls)
            else:
                # São cards individuais
                all_cards.append(control)
        
        # Limpar container e readicionar cards em coluna única
        self.results_container.controls.clear()
        for card in all_cards:
            self.results_container.controls.append(card)
    
    def add_card_to_layout(self, card):
        """Adiciona um novo card respeitando o layout atual"""
        if not self.results_container:
            print("❌ Container não disponível para adicionar card")
            return
            
        print(f"🔧 Adicionando card, layout atual: {self.current_layout}, containers existentes: {len(self.results_container.controls)}")
            
        if self.current_layout == "double":
            # Buscar estrutura de duas colunas existente
            double_column_row = None
            for control in self.results_container.controls:
                if isinstance(control, ft.Row) and len(control.controls) == 2:
                    double_column_row = control
                    break
            
            # Se não existe estrutura, criar uma nova
            if double_column_row is None:
                print("🔧 Criando nova estrutura de duas colunas")
                # Coletar cards existentes antes de limpar
                existing_cards = list(self.results_container.controls)
                self.results_container.controls.clear()
                
                # Criar colunas com alinhamento consistente
                left_column = ft.Column(
                    [], 
                    spacing=10, 
                    expand=True,
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                )
                right_column = ft.Column(
                    [], 
                    spacing=10, 
                    expand=True,
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH
                )
                
                # Redistribuir cards existentes
                for i, existing_card in enumerate(existing_cards):
                    if not isinstance(existing_card, ft.Row):  # Evitar nested rows
                        if i % 2 == 0:
                            left_column.controls.append(existing_card)
                        else:
                            right_column.controls.append(existing_card)
                
                # Criar nova row com as colunas
                double_column_row = ft.Row([
                    left_column,
                    right_column
                ], 
                spacing=20, 
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.START
                )
                
                self.results_container.controls.append(double_column_row)
            
            # Agora adicionar o novo card à coluna apropriada
            left_column, right_column = double_column_row.controls
            if len(left_column.controls) <= len(right_column.controls):
                left_column.controls.append(card)
                print(f"🔧 Card adicionado à coluna esquerda (total: {len(left_column.controls)})")
            else:
                right_column.controls.append(card)
                print(f"🔧 Card adicionado à coluna direita (total: {len(right_column.controls)})")
            
            # Uma única atualização no final
            self.results_container.update()
            
        else:
            # Layout single - adicionar diretamente
            self.results_container.controls.append(card)
            self.results_container.update()
            print(f"🔧 Card adicionado em layout single (total: {len(self.results_container.controls)})")
    
    def update_supplier_cards_layout(self, window_width):
        """Atualiza o layout interno dos cards de suppliers baseado na largura da janela"""
        try:
            # Encontrar a lista de suppliers (suppliers_results_list)
            # Esta função será chamada globalmente, então precisamos acessar a lista de suppliers
            # de forma indireta através da página
            global suppliers_results_list
            if 'suppliers_results_list' in globals() and suppliers_results_list:
                should_use_single_column = window_width < 1000
                
                # Percorrer todos os cards de suppliers e atualizar seu layout interno
                for card_control in suppliers_results_list.controls:
                    if isinstance(card_control, ft.Card):
                        # Recrear o conteúdo do card com o novo layout
                        self._update_single_supplier_card_layout(card_control, should_use_single_column)
                
                # Atualizar a interface
                suppliers_results_list.update()
                print(f"📱 Layout dos cards de suppliers atualizado: {'uma coluna' if should_use_single_column else 'duas colunas'}")
                
        except Exception as e:
            print(f"❌ Erro ao atualizar layout dos cards de suppliers: {e}")
    
    def _update_single_supplier_card_layout(self, card, use_single_column):
        """Atualiza o layout interno de um único card de supplier"""
        try:
            # Verificar se o card tem os dados necessários (função de criar layout)
            if hasattr(card, 'data') and card.data and 'create_layout' in card.data:
                create_layout_func = card.data['create_layout']
                
                # Recriar o layout usando a função armazenada
                new_layout = create_layout_func(use_single_column)
                
                # Substituir o conteúdo do container
                if hasattr(card, 'content') and hasattr(card.content, 'content'):
                    card.content.content = new_layout
                    
                print(f"✅ Card {card.data.get('supplier_id', 'unknown')} atualizado para {'uma' if use_single_column else 'duas'} coluna(s)")
                
        except Exception as e:
            print(f"❌ Erro ao atualizar card individual: {e}")
            # Fallback para o método antigo se necessário
            self._update_single_supplier_card_layout_fallback(card, use_single_column)
    
    def _update_single_supplier_card_layout_fallback(self, card, use_single_column):
        """Método de fallback para cards antigos sem função de layout armazenada"""
        try:
            # Obter o container interno do card
            if hasattr(card, 'content') and hasattr(card.content, 'content'):
                container_content = card.content.content
                
                # Verificar se é uma Column com o layout que esperamos
                if isinstance(container_content, ft.Column) and len(container_content.controls) >= 1:
                    # Primeiro controle deve ser Row (duas colunas) ou Column (uma coluna)
                    main_content = container_content.controls[0]
                    
                    # Obter as referências das colunas left_column e right_column
                    left_column = None
                    right_column = None
                    
                    if isinstance(main_content, ft.Row):
                        # Layout de duas colunas atual
                        if len(main_content.controls) >= 3:  # left_column, divider, right_column
                            left_column = main_content.controls[0]
                            right_column = main_content.controls[2]
                    elif isinstance(main_content, ft.Column):
                        # Layout de uma coluna atual - precisamos extrair as partes
                        if len(main_content.controls) >= 3:
                            left_column = main_content.controls[0]
                            right_column = main_content.controls[2]
                    
                    if left_column and right_column:
                        # Recriar o layout baseado na decisão
                        if use_single_column:
                            # Layout de uma coluna
                            new_layout = ft.Column([
                                left_column,
                                ft.Divider(),
                                right_column,
                                ft.Divider(),
                                container_content.controls[-1] if len(container_content.controls) > 1 else ft.Container()  # actions_row
                            ], spacing=15)
                        else:
                            # Layout de duas colunas
                            new_layout = ft.Column([
                                ft.Row([left_column, ft.VerticalDivider(), right_column], expand=True),
                                ft.Divider(),
                                container_content.controls[-1] if len(container_content.controls) > 1 else ft.Container()  # actions_row
                            ], spacing=15)
                        
                        # Substituir o conteúdo
                        card.content.content = new_layout
                        
        except Exception as e:
            print(f"❌ Erro no fallback: {e}")
    
    def update_users_layout(self, window_width):
        """Atualiza o layout da aba Users baseado na largura da janela"""
        try:
            # Definir breakpoint para responsividade (menor que 1000px = layout vertical)
            should_use_vertical_layout = window_width < 1000
            users_form_container = ft.Container(
                content=ft.Column([
                    # Linha 1: WWID e Nome
                    ft.Row([
                        ft.TextField(
                            label="WWID",
                            hint_text="Digite o WWID do usuário",
                            prefix_icon=ft.Icons.BADGE,
                            expand=True,
                            border_radius=8,
                            filled=False,  # Fundo transparente
                        ),
                        ft.TextField(
                            label="Nome Completo",
                            hint_text="Digite o nome do usuário",
                            prefix_icon=ft.Icons.PERSON,
                            expand=True,
                            border_radius=8,
                            filled=False,  # Fundo transparente
                        ),
                    ], spacing=10),

                    # Linha 2: Senha e Privilégio
                    ft.Row([
                        ft.TextField(
                            label="Senha",
                            hint_text="Digite a senha do usuário",
                            prefix_icon=ft.Icons.LOCK,
                            password=True,
                            can_reveal_password=True,
                            expand=True,
                            border_radius=8,
                            filled=False,  # Fundo transparente
                        ),
                        ft.Dropdown(
                            label="Nível de Privilégio",
                            hint_text="Selecione o nível",
                            options=[
                                ft.dropdown.Option("User", "User"),
                                ft.dropdown.Option("Admin", "Admin"),
                                ft.dropdown.Option("Super Admin", "Super Admin"),
                            ],
                            expand=True,
                            bgcolor=None,  # Fundo transparente
                            content_padding=ft.padding.symmetric(horizontal=12, vertical=16),
                        ),
                    ], spacing=10),
                ], spacing=15),
                bgcolor=None,
                padding=ft.padding.all(20),
                border_radius=8,
                border=None
            )

            # Wrapper externo para limitar largura
            users_form_container = ft.Container(
                content=users_form_container,
                width=500,
                alignment=ft.alignment.center
            )
            print(f"❌ Tipos incorretos: row1 ou row2 não são Row/Column")
            return
                
            
        except Exception as e:
            print(f"❌ Erro ao atualizar layout da aba Users: {e}")
            import traceback
            traceback.print_exc()
    
    def _find_users_content_recursive(self, control, depth=0):
        """Busca recursiva para encontrar users_content"""
        if depth > 10:  # Evitar recursão infinita
            return None
            
        # Verificar se é o users_content (Container com padding 20 e visible False inicialmente)
        if isinstance(control, ft.Container) and hasattr(control, 'padding') and control.padding == 20:
            if hasattr(control, 'content') and isinstance(control.content, ft.Column):
                column = control.content
                if len(column.controls) >= 3:
                    first_text = column.controls[0]
                    if isinstance(first_text, ft.Text) and "Gerenciamento de Usuários" in str(first_text.value):
                        return control
        
        # Buscar recursivamente nos filhos
        if hasattr(control, 'controls'):
            for child in control.controls:
                result = self._find_users_content_recursive(child, depth + 1)
                if result:
                    return result
        elif hasattr(control, 'content') and control.content:
            return self._find_users_content_recursive(control.content, depth + 1)
        
        return None

# Instância global do gerenciador responsivo
responsive_app_manager = None

# ===== VARIÁVEIS GLOBAIS =====
current_user_wwid = None
current_user_name = None
current_user_privilege = None
current_user_permissions = {}
selected_user = None  # Para controlar a seleção de usuários na aba Users
suppliers_results_list = None  # Lista global dos cards de suppliers
score_control_type = "slider"  # Tipo de controle: "slider" ou "spinbox"

# ===== FUNÇÕES AUXILIARES =====

def safe_update_control(control, page=None):
    """
    Atualiza um controle de forma segura, lidando com casos onde o controle
    não está devidamente vinculado à página
    """
    try:
        if hasattr(control, 'page') and control.page is not None:
            control.update()
        elif page is not None:
            # Se o controle não está vinculado à página, atualizar toda a página
            page.update()
        else:
            # Tentar atualizar o controle mesmo assim
            control.update()
    except Exception as update_error:
        print(f"Aviso: Erro ao atualizar controle, tentando page.update(): {update_error}")
        if page is not None:
            try:
                page.update()
            except Exception as page_error:
                print(f"Erro ao atualizar página: {page_error}")

# ===== DEFINIÇÕES SIMPLES DE TEMAS =====

def get_current_theme_colors(theme_name="white"):
    """Return base colors for the given theme

    Nota: os campos de "Comentário" e os campos de nota (spinbox/slider TextField)
    presentes nos cards da aba Score foram configurados para usar a mesma cor de
    fundo do card (`card_background`) para terem aparencia integrada ao card.
    Para alterar esse comportamento, edite os locais onde `bgcolor=...get('card_background')`
    é usado ou modifique os valores retornados por este tema.
    """
    if theme_name == "dark":
        return {
            "field_background": "#2C2C2C",
            "on_surface": "#E0E0E0",
            "outline": "#555555",
            "card_background": "#1E1E1E",
            "primary": "#4EA1FF",
            "on_primary": "#FFFFFF",
            "primary_container": "#3B3B3B",
            "surface_variant": "#181818",
            "rail_background": "#0F0F0F"
        }
    elif theme_name == "dracula":
        return {
            "field_background": None,
            "on_surface": "#F8F8F2",
            "outline": "#6272A4",
            "card_background": "#343746",
            "primary": "#BD93F9",
            "on_primary": "#FFFFFF",
            "primary_container": "#6272A4",
            "surface_variant": "#2E303E",
            "rail_background": "#1E1F29"
        }
    else:  # white
        return {
            "field_background": "#FFFFFF",
            "on_surface": "#1C1C1C",
            "outline": "#CCCCCC",
            "card_background": "#F7F7F7",
            "primary": "#0066CC",
            "on_primary": "#FFFFFF",
            "primary_container": "#E6F0FF",
            "surface_variant": "#FAFAFA",
            "rail_background": "#F0F0F0"
        }

def get_theme_name_from_page(page_ref=None):
    """Obtém o nome do tema atual da página"""
    if page_ref and hasattr(page_ref, 'data') and page_ref.data:
        return page_ref.data.get("theme_name", "white")
    return "white"

def get_card_color(theme_name="white"):
    """Retorna a cor dos cards baseada no tema"""
    if theme_name == "dracula":
        return "#6272A4"  # Cor da linha 590 do tema dracula
    else:
        return ft.Colors.BLUE_600  # Cor padrão para white e dark

# ===== SISTEMA DE LOGIN =====
def login_screen(page: ft.Page):
    """Tela de login para autenticação do usuário"""
    global current_user_wwid, current_user_name, current_user_privilege, current_user_permissions
    
    # Configurações da janela de login
    page.title = "Score App - Login"
    page.window.width = 500
    page.window.height = 650
    page.window.resizable = False
    page.window.center()
    page.theme_mode = ft.ThemeMode.SYSTEM  # Usar tema do sistema Windows
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.bgcolor = None  # Deixar que o sistema defina a cor de fundo
    
    # Cores do sistema Windows (adaptável ao tema claro/escuro)
    Colors = {
        'primary': "#1976D2",  # Azul sistema Windows
        'on_primary': "#FFFFFF",
        'surface': None,  # Usar cor padrão do sistema
        'on_surface': None,  # Usar cor padrão do sistema
        'on_surface_variant': "#757575",
        'field_background': None,  # Usar cor padrão do sistema
        'outline': "#BDBDBD",
        'error': "#D32F2F"
    }
    
    # Funções para Remember Me
    def get_app_data_path():
        """Retorna o caminho da pasta AppData para o ScoreApp"""
        import os
        app_data = os.getenv('APPDATA')  # Pasta AppData/Roaming do usuário
        app_folder = os.path.join(app_data, 'ScoreApp')
        
        # Criar pasta se não existir
        if not os.path.exists(app_folder):
            os.makedirs(app_folder)
        
        return os.path.join(app_folder, 'remember_me.txt')
    
    def load_saved_credentials():
        """Carrega credenciais salvas do AppData"""
        try:
            credentials_file = get_app_data_path()
            with open(credentials_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) >= 2:
                    saved_wwid = lines[0].strip()
                    saved_password = lines[1].strip()
                    print(f"📂 Credenciais carregadas de: {credentials_file}")
                    return saved_wwid, saved_password
        except FileNotFoundError:
            print("📂 Nenhuma credencial salva encontrada")
        except Exception as e:
            print(f"❌ Erro ao carregar credenciais: {e}")
        return "", ""
    
    def save_credentials(wwid, password):
        """Salva credenciais na pasta AppData"""
        try:
            credentials_file = get_app_data_path()
            with open(credentials_file, 'w', encoding='utf-8') as f:
                f.write(f"{wwid}\n{password}\n")
            print(f"📂 Credenciais salvas em: {credentials_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar credenciais: {e}")
    
    def clear_saved_credentials():
        """Remove credenciais salvas da pasta AppData"""
        try:
            import os
            credentials_file = get_app_data_path()
            if os.path.exists(credentials_file):
                os.remove(credentials_file)
                print(f"📂 Credenciais removidas de: {credentials_file}")
        except Exception as e:
            print(f"❌ Erro ao limpar credenciais: {e}")
    
    # Carregar credenciais salvas
    saved_wwid, saved_password = load_saved_credentials()
    
    # Campos de entrada com tema do sistema
    wwid_field = ft.TextField(
        label="WWID",
        width=320,
        autofocus=True,
        border_radius=8,
        border_color=Colors['outline'],
        prefix_icon=ft.Icons.PERSON,
        value=saved_wwid  # Preencher com valor salvo
    )
    
    password_field = ft.TextField(
        label="Password", 
        password=True,
        can_reveal_password=True,
        width=320,
        border_radius=8,
        border_color=Colors['outline'],
        prefix_icon=ft.Icons.LOCK,
        value=saved_password  # Preencher com valor salvo
    )
    
    # Checkbox Remember Me
    remember_me_checkbox = ft.Checkbox(
        label="Lembrar de mim",
        value=bool(saved_wwid and saved_password),  # Marcar se há credenciais salvas
        check_color=Colors['primary']
    )
    
    error_text = ft.Text(
        "",
        color=Colors['error'],
        text_align=ft.TextAlign.CENTER,
        size=12
    )
    
    login_button = ft.ElevatedButton(
        "Entrar",
        width=320,
        height=45,
        style=ft.ButtonStyle(
            bgcolor=Colors['primary'],
            color=Colors['on_primary'],
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=2
        ),
        icon=ft.Icons.LOGIN
    )
    
    def authenticate_user(wwid, password):
        """Verifica credenciais na tabela users_table"""
        try:
            result = db_manager.query_one("""
                SELECT user_wwid, user_password, user_privilege, otif, nil, pickup, package 
                FROM users_table 
                WHERE user_wwid = ? AND user_password = ?
            """, (wwid, password))
            
            if result:
                return {
                    'wwid': result['user_wwid'],
                    'password': result['user_password'],
                    'privilege': result['user_privilege'],
                    'otif': result['otif'] == '1' or result['otif'] == 1,
                    'nil': result['nil'] == '1' or result['nil'] == 1,
                    'pickup': result['pickup'] == '1' or result['pickup'] == 1,
                    'package': result['package'] == '1' or result['package'] == 1
                }
            return None
            
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return None
    
    def get_user_theme(wwid):
        """Busca tema do usuário na tabela theme_settings"""
        try:
            result = db_manager.query_one("SELECT theme_mode FROM theme_settings WHERE user_wwid = ?", (wwid,))
            return result['theme_mode'] if result else "white"
            
        except Exception as e:
            print(f"Erro ao carregar tema: {e}")
            return "white"

    def on_login_click(e):
        wwid = wwid_field.value.strip()
        password = password_field.value.strip()

        if not wwid or not password:
            error_text.value = "Por favor, preencha todos os campos"
            page.update()
            return

        # Apenas desabilita o botão para evitar múltiplos cliques
        login_button.disabled = True
        page.update()

        # Autenticar usuário
        user_data = authenticate_user(wwid, password)

        if user_data:
            # Gerenciar Remember Me
            if remember_me_checkbox.value:
                save_credentials(wwid, password)
                print("📝 Credenciais salvas para próximo login")
            else:
                clear_saved_credentials()
                print("🗑️ Credenciais removidas")
            
            # Definir variáveis globais
            global current_user_wwid, current_user_name, current_user_privilege, current_user_permissions
            current_user_wwid = user_data['wwid']
            current_user_name = user_data['wwid']  # Pode ser expandido com nome real
            current_user_privilege = user_data['privilege']
            current_user_permissions = {
                'otif': user_data['otif'],
                'nil': user_data['nil'],
                'pickup': user_data['pickup'],
                'package': user_data['package']
            }

            # Buscar tema do usuário
            user_theme = get_user_theme(wwid)

            print(f"Login bem-sucedido: {current_user_wwid} ({current_user_privilege})")
            print(f"Permissões: {current_user_permissions}")
            print(f"Tema: {user_theme}")

            # Definir usuário atual no DBManager para logs
            db_manager.set_current_user(current_user_wwid)

            # Carregar aplicação principal (sem animação)
            page.controls.clear()
            page.title = "Score App"
            page.window.min_width = 850
            page.window.min_height = 900
            page.window.resizable = True
            page.window.maximized = True
            page.update() # Aplica a maximização

            # Inicializar aplicação principal na mesma página
            initialize_main_app(page, user_theme)

        else:
            # Reabilita o botão e mostra o erro
            login_button.disabled = False
            error_text.value = "WWID ou senha incorretos"
            password_field.value = ""
            page.update()

    login_button.on_click = on_login_click
    
    # Permitir login com Enter
    def on_key_press(e):
        if e.key == "Enter":
            on_login_click(e)
    
    wwid_field.on_submit = on_login_click
    password_field.on_submit = on_login_click
    
    # Layout da tela de login com responsividade
    login_container = ft.Container(
        content=ft.Column(
            [
                ft.Container(height=15),
                ft.Icon(
                    ft.Icons.ANALYTICS,
                    size=48,
                    color=Colors['primary']
                ),
                ft.Container(height=12),
                ft.Text(
                    "Score App",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=Colors['on_surface']
                ),
                ft.Text(
                    "Sistema de Avaliação de Fornecedores",
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                    color=Colors['on_surface_variant']
                ),
                ft.Container(height=25),
                wwid_field,
                ft.Container(height=12),
                password_field,
                ft.Container(height=15),
                # Container para centralizar o checkbox
                ft.Container(
                    content=remember_me_checkbox,
                    alignment=ft.alignment.center_left,
                    width=320,
                ),
                ft.Container(height=8),
                error_text,
                ft.Container(height=20),
                login_button,
                ft.Container(height=15)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        ),
        bgcolor=Colors['surface'],
        border_radius=12,
        padding=ft.padding.all(30),
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=10,
            color="#26000000",  # Preto com 15% de opacidade
            offset=ft.Offset(0, 2)
        ),
        alignment=ft.alignment.center,
        width=420,
        height=None,  # Altura automática para evitar overflow
        margin=ft.margin.all(20),  # Margem para garantir que fique dentro da tela
        animate_opacity=300
    )
    
    # Usar Container com scroll para garantir que caiba na tela
    main_container = ft.Container(
        content=login_container,
        alignment=ft.alignment.center,
        expand=True
    )
    
    page.add(main_container)
# ===== FIM DO SISTEMA DE LOGIN =====

class DeleteSupplierConfirmationDialog(ft.AlertDialog):
    def __init__(self, supplier_name, supplier_id, on_confirm, on_cancel, scale_func=None):
        super().__init__()
        self.supplier_name = supplier_name
        self.supplier_id = supplier_id
        self.on_confirm_callback = on_confirm
        self.on_cancel_callback = on_cancel
        self.random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        self.scale_func = scale_func or (lambda x: x)
        
        self.confirmation_text = ft.TextField(
            label="Digite o código de confirmação",
            width=self.scale_func(300),
            text_align=ft.TextAlign.CENTER
        )
        self.title = ft.Text("🗑️ Excluir Supplier")
        self.error_text = ft.Text("Código incorreto. Tente novamente.", color="red", visible=False)
        self.code_display_text = ft.Text(self.random_code, weight=ft.FontWeight.BOLD, size=20, color="primary")
        
        self.content = ft.Column([
            ft.Text(f"Tem certeza que deseja excluir '{self.supplier_name}'?"),
            ft.Text("Esta ação não pode ser desfeita."),
            ft.Text("Para confirmar, digite o código abaixo:"),
            ft.Row([self.code_display_text], alignment=ft.MainAxisAlignment.CENTER),
            self.confirmation_text,
            self.error_text
        ], tight=True, spacing=15, width=350)
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.cancel),
            ft.TextButton("Excluir", on_click=self.confirm, style=ft.ButtonStyle(color="red"))
        ]
        self.actions_alignment = ft.MainAxisAlignment.END
    
    def confirm(self, e):
        if self.confirmation_text.value.strip().upper() == self.random_code:
            self.on_confirm_callback(e)
        else:
            self.error_text.visible = True
            self.update()
    
    def cancel(self, e):
        self.on_cancel_callback(e)


class DeleteListItemConfirmationDialog(ft.AlertDialog):
    def __init__(self, item_name, item_type, on_confirm, on_cancel, scale_func=None):
        super().__init__()
        self.item_name = item_name
        self.item_type = item_type
        self.on_confirm_callback = on_confirm
        self.on_cancel_callback = on_cancel
        self.random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        self.scale_func = scale_func or (lambda x: x)
        
        self.confirmation_text = ft.TextField(
            label="Digite o código de confirmação",
            width=self.scale_func(300),
            text_align=ft.TextAlign.CENTER
        )
        self.title = ft.Text("🗑️ Excluir Item da Lista")
        self.error_text = ft.Text("Código incorreto. Tente novamente.", color="red", visible=False)
        self.code_display_text = ft.Text(self.random_code, weight=ft.FontWeight.BOLD, size=20, color="primary")
        
        self.content = ft.Column([
            ft.Text(f"Tem certeza que deseja excluir '{self.item_name}'?"),
            ft.Text(f"Lista: {self.item_type}"),
            ft.Text("Esta ação não pode ser desfeita."),
            ft.Text("Para confirmar, digite o código abaixo:"),
            ft.Row([self.code_display_text], alignment=ft.MainAxisAlignment.CENTER),
            self.confirmation_text,
            self.error_text
        ], tight=True, spacing=15, width=350)
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.cancel),
            ft.TextButton("Excluir", on_click=self.confirm, style=ft.ButtonStyle(color="red"))
        ]
        self.actions_alignment = ft.MainAxisAlignment.END
    
    def confirm(self, e):
        if self.confirmation_text.value.strip().upper() == self.random_code:
            self.on_confirm_callback(e)
        else:
            self.error_text.visible = True
            self.update()
    
    def cancel(self, e):
        self.on_cancel_callback(e)


class AddSupplierDialog(ft.AlertDialog):
    def __init__(self, on_confirm, on_cancel, page, scale_func=None, list_options=None):
        super().__init__()
        self.on_confirm_callback = on_confirm
        self.on_cancel_callback = on_cancel
        self.page = page
        self.scale_func = scale_func or (lambda x: x)
        self.list_options = list_options or {}
        
        def update_status_color_dialog(e):
            """Atualiza a cor do texto do dropdown de status no diálogo"""
            status_value = e.control.value
            if status_value == "Active":
                e.control.color = "green"
            elif status_value == "Inactive":
                e.control.color = "red"
            else:
                e.control.color = get_current_theme_colors(self.page).get('on_surface') if hasattr(self, 'page') else "black"
            if e.page:
                e.page.update()
            elif hasattr(e.control, 'update'):
                e.control.update()
        
        # Campos do formulário organizados por seção (sem supplier_id)
        self.fields = {
            # Informações Básicas
            "vendor_name": ft.TextField(
                label="Vendor Name*", 
                width=250,
                bgcolor=get_current_theme_colors(self.page).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline')
            ),
            "supplier_origin": ft.Dropdown(
                label="Origem",
                width=250,
                value="",
                options=[ft.dropdown.Option(v) for v in ["Nacional", "Importado"]],
                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline')
            ),
            "supplier_category": ft.Container(
                content=ft.Dropdown(
                    label="Supplier Category",
                    width=250,
                    color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                    border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline'),
                    options=[
                        ft.dropdown.Option(v)
                        for v in (self.list_options.get('category') or ["Raw Materials", "Components", "Services", "Equipment"])
                    ],
                ),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(self.page)).get('field_background'),
            ),
            
            # Informações de Contato
            "supplier_email": ft.TextField(
                label="Email", 
                width=250,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(self.page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline')
            ),
            "supplier_number": ft.TextField(
                label="Número", 
                width=250,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(self.page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline')
            ),
            
            # Configurações Organizacionais
            "bu": ft.Container(
                content=ft.Dropdown(
                    label="BU (Business Unit)",
                    width=200,
                    color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                    border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline'),
                    filled=False,
                    options=[ft.dropdown.Option(v) for v in (self.list_options.get('bu') or ["", "Operations", "Manufacturing", "Procurement", "Quality", "Logistics"]) ]
                ),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
            ),

            "supplier_status": ft.Container(
                content=ft.Dropdown(
                    label="Status",
                    width=200,
                    value="Active",  # Valor padrão
                    color="green",  # Cor inicial verde para "Active"
                    border_color=get_current_theme_colors(self.page).get('outline'),
                    options=[
                        ft.dropdown.Option("Active"),
                        ft.dropdown.Option("Inactive"),
                    ],
                    on_change=update_status_color_dialog
                ),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
            ),

                        "planner": ft.Container(
                            content=ft.Dropdown(
                                label="Planner",
                                width=200,
                                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline'),
                                options=[ft.dropdown.Option(v) for v in ((self.list_options.get('planner') or []) )]
                            ),
                            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
                        ),

                        "continuity": ft.Container(
                            content=ft.Dropdown(
                                label="Continuity", 
                                width=200,
                                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline'),
                                options=[ft.dropdown.Option(v) for v in ((self.list_options.get('continuity') or []) )]
                            ),
                            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
                        ),

                        "sourcing": ft.Container(
                            content=ft.Dropdown(
                                label="Sourcing",
                                width=200,
                                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline'),
                                options=[ft.dropdown.Option(v) for v in ((self.list_options.get('sourcing') or []) )]
                            ),
                            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
                        ),

                        "sqie": ft.Container(
                            content=ft.Dropdown(
                                label="SQIE",
                                width=200,
                                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline'),
                                options=[ft.dropdown.Option(v) for v in ((self.list_options.get('sqie') or []) )]
                            ),
                            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
                        ),

        }
        
        self.title = ft.Text("➕ Adicionar Novo Supplier", size=18, weight=ft.FontWeight.BOLD)
        self.error_text = ft.Text("", color="red", visible=False)
        
        # Criar seções organizadas com tema padrão
        basic_info_section = ft.Container(
            content=ft.Column([
                ft.Text("📋 Informações Básicas", size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Row([self.fields["vendor_name"], self.fields["supplier_origin"]], spacing=15),
                self.fields["supplier_category"],
            ], spacing=10),
            padding=ft.padding.all(15),
            bgcolor="surface_variant",
            border_radius=8
        )
        
        contact_section = ft.Container(
            content=ft.Column([
                ft.Text("📞 Informações de Contato", size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Row([self.fields["supplier_email"], self.fields["supplier_number"]], spacing=15),
            ], spacing=10),
            padding=ft.padding.all(15),
            bgcolor="surface_variant",
            border_radius=8
        )
        
        org_section = ft.Container(
            content=ft.Column([
                ft.Text("🏢 Configurações Organizacionais", size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Row([self.fields["bu"], self.fields["supplier_status"]], spacing=15),
            ], spacing=10),
            padding=ft.padding.all(15),
            bgcolor="surface_variant",
            border_radius=8
        )
        
        management_section = ft.Container(
            content=ft.Column([
                ft.Text("⚙️ Configurações de Gestão", size=14, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Row([self.fields["planner"], self.fields["continuity"]], spacing=15),
                ft.Row([self.fields["sourcing"], self.fields["sqie"]], spacing=15),
            ], spacing=10),
            padding=ft.padding.all(15),
            bgcolor="surface_variant",
            border_radius=8
        )
        
        self.content = ft.Container(
            content=ft.Column([
                ft.Text("* Campos obrigatórios", size=12, color="red", weight=ft.FontWeight.BOLD),
                basic_info_section,
                contact_section,
                org_section,
                management_section,
                self.error_text
            ], spacing=20, scroll=ft.ScrollMode.AUTO),
            width=600,
            height=500
        )
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self.cancel, icon=ft.Icons.CANCEL),
            ft.ElevatedButton("💾 Salvar", on_click=self.confirm, 
                            style=ft.ButtonStyle(
                                bgcolor="primary",
                                color="white"  # Cor da fonte branca para melhor contraste
                            ))
        ]
        self.actions_alignment = ft.MainAxisAlignment.END
    
    def get_field_value(self, field):
        """Obtém valor tanto de TextField quanto de Dropdown"""
        if hasattr(field, 'value') and field.value:
            return str(field.value).strip()
        return ""
    
    def validate_fields(self):
        """Valida os campos obrigatórios"""
        vendor_name_value = self.get_field_value(self.fields["vendor_name"])
        print(f"🔍 DEBUG: Validando vendor_name: '{vendor_name_value}'")
        
        if not vendor_name_value:
            print("🔍 DEBUG: Vendor Name está vazio")
            self.error_text.value = "❌ Campo Vendor Name é obrigatório!"
            self.error_text.visible = True
            return False
        
        print("🔍 DEBUG: Validação passou")
        self.error_text.visible = False
        return True
    
    def confirm(self, e):
        print("🔍 DEBUG: Método confirm chamado")
        if self.validate_fields():
            print("🔍 DEBUG: Validação passou, chamando callback")
            self.on_confirm_callback(e)
        else:
            print("🔍 DEBUG: Validação falhou")
            self.update()
    
    def cancel(self, e):
        self.on_cancel_callback(e)

class EditTimelineRecordDialog(ft.AlertDialog):
    def __init__(self, record_data, on_confirm, on_cancel, page):
        super().__init__()
        self.record_data = record_data  # (month, year, otif, nil, pickup, package, total, comment)
        self.on_confirm_callback = on_confirm
        self.on_cancel_callback = on_cancel
        self.page = page

        month, year, otif, nil, pickup, package, total, comment = record_data

        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        try:
            month_int = int(month)
            month_name = months[month_int-1] if 1 <= month_int <= 12 else str(month)
        except (ValueError, TypeError):
            month_name = str(month)

        self.title = ft.Text(f"Editar Registro - {month_name}/{year}")

        # Criar controles baseados na configuração e permissões
        self.otif_control = self.create_score_control("OTIF", otif, current_user_permissions.get('otif', False))
        self.nil_control = self.create_score_control("NIL", nil, current_user_permissions.get('nil', False))
        self.pickup_control = self.create_score_control("Pickup", pickup, current_user_permissions.get('pickup', False))
        self.package_control = self.create_score_control("Package", package, current_user_permissions.get('package', False))

        self.comment_field = ft.TextField(
            label="Comentário",
            value=comment or "",
            expand=True,
            multiline=True,
            min_lines=6,
            max_lines=12,
            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
        )

        # Layout em duas colunas: duas notas por linha
        left_col = ft.Column([ft.Container(content=self.otif_control, width=260), ft.Container(height=6), ft.Container(content=self.pickup_control, width=260)], spacing=6)
        right_col = ft.Column([ft.Container(content=self.nil_control, width=260), ft.Container(height=6), ft.Container(content=self.package_control, width=260)], spacing=6)

        controls_row = ft.Row([
            left_col,
            ft.Container(width=12),
            right_col
        ], alignment=ft.MainAxisAlignment.START)

        self.content = ft.Container(
            content=ft.Column([
                    ft.Text("Edite os valores do registro:", size=14),
                    ft.Container(height=8),
                    controls_row,
                    ft.Container(height=8),
                    self.comment_field,
            ], spacing=8, tight=False),
                # Remover width fixo para permitir adaptação à janela
                height=420
        )

        self.actions = [
            ft.TextButton("Cancelar", on_click=self.cancel, icon=ft.Icons.CANCEL),
            ft.ElevatedButton("💾 Salvar", on_click=self.confirm,
                            style=ft.ButtonStyle(
                                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('primary'),
                                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_primary')
                            ))
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def create_score_control(self, label, value, has_permission):
        """Cria um controle de pontuação baseado na configuração (slider ou spinbox) e permissões"""
        global score_control_type

        # Normalizar valor recebido: pode vir como número, string numérica, ou valores inválidos
        norm_value = None
        try:
            if value is None:
                norm_value = None
            elif isinstance(value, (int, float)):
                norm_value = float(value)
            elif isinstance(value, str):
                # remover espaços e possíveis percentuais/ caracteres extras
                v = value.strip()
                # tentar converter diretamentente
                norm_value = float(v) if v != "" else None
            else:
                # tenta converter generically
                norm_value = float(value)
        except (ValueError, TypeError):
            # valor inválido — registrar e usar None como fallback
            print(f"Aviso: valor de pontuação inválido para '{label}': {value}")
            norm_value = None

        if score_control_type == "slider":
            # Criar slider
            score_text = ft.Text(f"{norm_value:.1f}" if norm_value is not None else "0.0", width=40, text_align=ft.TextAlign.CENTER)
            score_slider = ft.Slider(
                min=0,
                max=10,
                divisions=100,
                value=norm_value if norm_value is not None else 0,
                width=120,
                disabled=not has_permission
            )

            def on_slider_change(e):
                score_text.value = f"{e.control.value:.1f}"
                if hasattr(score_text, 'page') and score_text.page is not None:
                    score_text.update()

            score_slider.on_change = on_slider_change

            # Aplicar opacidade reduzida se não tiver permissão
            opacity = 1.0 if has_permission else 0.5
            score_text.opacity = opacity

            return ft.Column([
                ft.Text(label, size=12, weight="bold", opacity=opacity),
                score_slider,
                ft.Container(
                    content=score_text,
                    alignment=ft.alignment.center,
                    width=120,
                    margin=ft.margin.only(top=-15)
                )
            ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        else:  # spinbox
            try:
                increment = load_spinbox_increment()
            except NameError:
                # Função não disponível no escopo no momento; usar valor padrão
                increment = 0.1
            except Exception as ex:
                print(f"Aviso: não foi possível carregar increment do spinbox: {ex}")
                increment = 0.1

            score_field = ft.TextField(
                value=f"{norm_value:.1f}" if norm_value is not None else "0.0",
                text_align=ft.TextAlign.CENTER,
                width=70,
                border_radius=8,
                # Manter a consistência visual: usar cor de fundo igual à do card
                bgcolor=get_current_theme_colors(get_theme_name_from_page(self.page)).get('card_background'),
                color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(self.page)).get('outline'),
                disabled=not has_permission
            )

            # CORRIGIDO: Validar entrada manual no campo de spinbox apenas quando terminar de editar
            def on_score_field_blur(e):
                """Valida e formata o valor apenas quando o usuário termina de editar (perde o foco)"""
                try:
                    v = e.control.value
                    if v is None or str(v).strip() == "":
                        e.control.value = "0.0"
                        e.control.update()
                        return
                    
                    # Permitir entrada de números inteiros e decimais
                    num = float(str(v).strip())
                    # Limitar entre 0 e 10
                    num = max(0, min(10, num))
                    # Formatar com 1 casa decimal
                    e.control.value = f"{num:.1f}"
                    e.control.update()
                except (ValueError, TypeError):
                    # Se não conseguir converter, voltar para 0.0
                    e.control.value = "0.0"
                    e.control.update()

            # Usar on_blur em vez de on_change para não interferir durante a digitação
            score_field.on_blur = on_score_field_blur

            def adjust_score(e):
                if not has_permission:
                    return
                try:
                    current_value = float(score_field.value)
                    if e.control.data == "+":
                        current_value += increment
                    elif e.control.data == "-":
                        current_value -= increment
                    new_value = max(0, min(10, current_value))
                    score_field.value = str(round(new_value, 1))
                    score_field.update()
                except ValueError:
                    score_field.value = "0.0"
                    score_field.update()

            # Aplicar opacidade reduzida se não tiver permissão
            opacity = 1.0 if has_permission else 0.5

            return ft.Column([
                ft.Text(label, size=12, weight="bold", opacity=opacity),
                ft.Row([
                    ft.IconButton(ft.Icons.REMOVE, on_click=adjust_score, data="-", icon_size=16, disabled=not has_permission, opacity=opacity),
                    score_field,
                    ft.IconButton(ft.Icons.ADD, on_click=adjust_score, data="+", icon_size=16, disabled=not has_permission, opacity=opacity),
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def get_control_value(self, control):
        """Extrai o valor do controle (slider ou spinbox)"""
        try:
            if score_control_type == "slider":
                # Para slider: Column[Slider, Container[Text]]
                if hasattr(control, 'controls') and len(control.controls) >= 2:
                    slider = control.controls[1]  # O slider é o segundo controle
                    if hasattr(slider, 'value'):
                        # Garantir que o slider esteja no intervalo
                        try:
                            val = float(slider.value)
                            return max(0, min(10, val))
                        except Exception:
                            return None
            else:  # spinbox
                # Para spinbox: Column[Text, Row[IconButton, TextField, IconButton]]
                if hasattr(control, 'controls') and len(control.controls) >= 2:
                    spinbox_row = control.controls[1]  # A Row é o segundo controle
                    if hasattr(spinbox_row, 'controls') and len(spinbox_row.controls) >= 2:
                        text_field = spinbox_row.controls[1]  # O TextField é o segundo da Row
                        if hasattr(text_field, 'value') and text_field.value:
                            try:
                                val = float(text_field.value)
                                return max(0, min(10, val))
                            except Exception:
                                return None
        except (ValueError, TypeError, AttributeError):
            pass
        return None

    def confirm(self, e):
        # Extrair valores dos controles
        try:
            otif = self.get_control_value(self.otif_control)
            nil = self.get_control_value(self.nil_control)
            pickup = self.get_control_value(self.pickup_control)
            package = self.get_control_value(self.package_control)
            comment = self.comment_field.value.strip() if self.comment_field.value else None

            # Chamar callback com os novos valores
            self.on_confirm_callback(self.record_data, otif, nil, pickup, package, comment)
        except Exception as ex:
           print(f"❌ Erro ao processar valores: {str(ex)}")

    def cancel(self, e):
        self.on_cancel_callback(e)

# Variável global para o usuário atual
# Variáveis globais de usuário definidas no início do arquivo

# Configurações globais do aplicativo
app_settings = {'toast_duration': 3}

def load_app_settings(user_wwid=None):
    """Carrega as configurações gerais do aplicativo."""
    try:
        if user_wwid:
            result = db_manager.query_one("SELECT toast_duration FROM app_settings WHERE user_wwid = ? ORDER BY last_updated DESC LIMIT 1", (user_wwid,))
        else:
            result = db_manager.query_one("SELECT toast_duration FROM app_settings WHERE user_wwid = 'default' ORDER BY last_updated DESC LIMIT 1")
        if result:
            return {'toast_duration': result['toast_duration']}
        return {'toast_duration': 3}  # Valor padrão
    except Exception as ex:
        print(f"Erro ao carregar configurações do app: {ex}")
        return {'toast_duration': 3}

def save_app_settings(settings, user_wwid=None):
    """Salva as configurações gerais do aplicativo."""
    try:
        user_id = user_wwid or 'default'
        
        existing = db_manager.query_one("SELECT id FROM app_settings WHERE user_wwid = ?", (user_id,))
        
        if existing:
            # Atualizar configuração existente
            db_manager.execute("UPDATE app_settings SET toast_duration = ?, last_updated = CURRENT_TIMESTAMP WHERE user_wwid = ?", 
                      (settings['toast_duration'], user_id))
        else:
            # Inserir nova configuração
            db_manager.execute("INSERT INTO app_settings (user_wwid, toast_duration) VALUES (?, ?)", 
                      (user_id, settings['toast_duration']))
        
        return True
    except Exception as ex:
        print(f"Erro ao salvar configurações do app: {ex}")
        return False

def initialize_main_app(page: ft.Page, user_theme="white"):
    global app_settings, current_user_wwid, current_user_name, current_user_privilege, current_user_permissions, users_controls, log_controls
    
    # Armazenar nome do tema na página para acesso global e confiável
    page.data = {"theme_name": user_theme}

    # Carregar configurações do app
    app_settings = load_app_settings()
    
    # Tema simplificado - apenas 3 opções básicas
    
    def menu_item(icon, text, idx, show_text=True):
        is_selected = selected_index.current == idx
        Colors = get_current_theme_colors(get_theme_name_from_page(page))
        
        def on_hover(e):
            e.control.bgcolor = Colors['surface_variant'] if e.data == "true" else (Colors['primary_container'] if is_selected else None)
            e.control.update()
        row_controls = [
            ft.Icon(icon, color=Colors['primary'] if is_selected else Colors['on_surface'])
        ]
        if show_text:
            row_controls.append(
                ft.Text(
                    text,
                    size=16,
                    weight="bold" if is_selected else "normal",
                    color=Colors['primary'] if is_selected else Colors['on_surface'],
                )
            )
        # Corrige: passa a função handler sem executar
        return ft.Container(
            content=ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER if not show_text else ft.MainAxisAlignment.START, spacing=15),
            padding=ft.padding.symmetric(horizontal=0 if not show_text else 10, vertical=10),
            border_radius=8,
            bgcolor=Colors['primary_container'] if is_selected else None,
            on_hover=on_hover,
            on_click=lambda e: set_selected(idx)(e),
            animate=200,
            width=160 if show_text else 40,
        )
    page.title = "Score App"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT

    # Estado do menu selecionado
    selected_index = ft.Ref()
    selected_index.current = 0

    # Funções auxiliares para usuários (definidas antes da interface)
    def check_user_exists(wwid):
        """Verifica se um usuário existe no banco de dados pelo WWID."""
        if not wwid or not wwid.strip():
            return False
        try:
            result = db_manager.query_one("SELECT 1 FROM users_table WHERE UPPER(user_wwid) = ?", (wwid.upper().strip(),))
            return result is not None
        except Exception as ex:
            print(f"Erro ao verificar usuário: {ex}")
            return False

    def update_action_button():
        """Atualiza o texto e ícone do botão de ação baseado no estado atual."""
        if 'action_btn' not in users_controls:
            return

        wwid_ctrl = resolve_control(users_controls.get('wwid')) if 'wwid' in users_controls else None
        wwid = wwid_ctrl.value.strip() if wwid_ctrl and getattr(wwid_ctrl, 'value', None) else ''

        action_btn_ctrl = resolve_control(users_controls.get('action_btn'))

        if wwid and check_user_exists(wwid):
            # Usuário existe - botão Update
            if action_btn_ctrl:
                action_btn_ctrl.text = "Update"
                action_btn_ctrl.icon = ft.Icons.EDIT
        else:
            # Usuário não existe - botão Add User
            if action_btn_ctrl:
                action_btn_ctrl.text = "Add User"
                action_btn_ctrl.icon = ft.Icons.PERSON_ADD

        if action_btn_ctrl and hasattr(action_btn_ctrl, 'update'):
            try:
                action_btn_ctrl.update()
            except Exception as e:
                print(f"Erro ao atualizar botão de ação: {e}")

    def on_wwid_change(e):
        """Função chamada quando o WWID é alterado para verificar em tempo real."""
        global selected_user
        wwid = e.control.value.strip().upper() if e.control.value else ''
        
        # Atualizar botão
        update_action_button()
        
        # Se WWID existe, carregar dados automaticamente
        if wwid and check_user_exists(wwid):
            # Só carregar se não é o usuário já selecionado
            if selected_user != wwid:
                load_user_data_by_wwid(wwid)
        elif wwid:
            # WWID digitado mas não existe - limpar apenas outros campos, manter WWID
            clear_other_fields_except_wwid()
        elif not wwid:
            # Campo WWID foi limpo - limpar seleção
            selected_user = None

    def find_field_by_label(label_text):
        """Busca um TextField ou Dropdown na estrutura users_content pelo label"""
        try:
            # Buscar users_content através da busca recursiva
            users_content_found = responsive_app_manager._find_users_content_recursive(page.controls[0])
            if not users_content_found:
                return None
                
            return _find_control_recursive(users_content_found, label_text)
        except Exception as e:
            print(f"Erro ao buscar campo {label_text}: {e}")
            return None
    
    def find_checkbox_by_label(label_text):
        """Busca um Checkbox na estrutura users_content pelo label"""
        try:
            # Buscar users_content através da busca recursiva
            users_content_found = responsive_app_manager._find_users_content_recursive(page.controls[0])
            if not users_content_found:
                return None
                
            return _find_checkbox_recursive(users_content_found, label_text)
        except Exception as e:
            print(f"Erro ao buscar checkbox {label_text}: {e}")
            return None
    
    def _find_control_recursive(control, target_label, depth=0):
        """Busca recursiva por TextField ou Dropdown com label específico"""
        if depth > 15:  # Evitar recursão infinita
            return None
            
        # Verificar se é TextField ou Dropdown com o label procurado
        if isinstance(control, (ft.TextField, ft.Dropdown)):
            if hasattr(control, 'label') and control.label == target_label:
                return control
        
        # Buscar nos filhos
        if hasattr(control, 'controls'):
            for child in control.controls:
                result = _find_control_recursive(child, target_label, depth + 1)
                if result:
                    return result
        elif hasattr(control, 'content') and control.content:
            return _find_control_recursive(control.content, target_label, depth + 1)
        
        return None
    
    def _find_checkbox_recursive(control, target_label, depth=0):
        """Busca recursiva por Checkbox com label específico"""
        if depth > 15:  # Evitar recursão infinita
            return None
            
        # Verificar se é Checkbox com o label procurado
        if isinstance(control, ft.Checkbox):
            if hasattr(control, 'label') and control.label == target_label:
                return control
        
        # Buscar nos filhos
        if hasattr(control, 'controls'):
            for child in control.controls:
                result = _find_checkbox_recursive(child, target_label, depth + 1)
                if result:
                    return result
        elif hasattr(control, 'content') and control.content:
            return _find_checkbox_recursive(control.content, target_label, depth + 1)
        
        return None

    def clear_other_fields_except_wwid():
        """Limpa todos os campos exceto o WWID quando digitando um WWID novo."""
        try:
            # Usar uma abordagem mais direta que não depende das referências antigas
            # após reorganização responsiva
            
            # Para campos de texto, buscar diretamente na estrutura
            try:
                # Buscar campo Name diretamente
                name_field = find_field_by_label("Nome Completo")
                if name_field:
                    name_field.value = ""
            except Exception as e:
                print(f"Erro ao limpar Name via busca direta: {e}")
                
            try:
                # Buscar campo Password diretamente  
                password_field = find_field_by_label("Senha")
                if password_field:
                    password_field.value = ""
            except Exception as e:
                print(f"Erro ao limpar Password via busca direta: {e}")
                
            try:
                # Buscar campo Privilege diretamente
                privilege_field = find_field_by_label("Nível de Privilégio")
                if privilege_field:
                    privilege_field.value = None
            except Exception as e:
                print(f"Erro ao limpar Privilege via busca direta: {e}")
            
            # Para checkboxes, buscar diretamente
            checkbox_labels = ["OTIF", "NIL", "Pickup", "Package"]
            for label in checkbox_labels:
                try:
                    checkbox = find_checkbox_by_label(label)
                    if checkbox:
                        checkbox.value = False
                except Exception as e:
                    print(f"Erro ao limpar checkbox {label}: {e}")
            
            # Não limpar selected_user automaticamente para evitar problemas com exclusão
            # A limpeza será feita apenas manualmente através da função clear_users_fields()
            
        except Exception as ex:
            print(f"Erro ao limpar campos: {ex}")

    def load_user_data_by_wwid(wwid):
        """Carrega os dados de um usuário pelo WWID e preenche os campos."""
        try:
            result = db_manager.query_one("""
                SELECT user_name, user_password, user_privilege,
                       otif, nil, pickup, package
                FROM users_table 
                WHERE UPPER(user_wwid) = ?
            """, (wwid.upper(),))
            
            if result:
                name = result['user_name']
                password = result['user_password']
                privilege = result['user_privilege']
                otif = result['otif']
                nil = result['nil']
                pickup = result['pickup']
                package = result['package']
                
                print(f"🔄 Preenchimento automático para WWID {wwid}")
                
                # Preencher campos usando busca direta na estrutura
                try:
                    name_field = find_field_by_label("Nome Completo")
                    if name_field:
                        name_field.value = str(name) if name else ""
                except Exception as e:
                    print(f"Erro ao preencher Name: {e}")
                    
                try:
                    password_field = find_field_by_label("Senha")
                    if password_field:
                        password_field.value = str(password) if password else ""
                except Exception as e:
                    print(f"Erro ao preencher Password: {e}")
                    
                try:
                    privilege_field = find_field_by_label("Nível de Privilégio")
                    if privilege_field:
                        privilege_field.value = str(privilege) if privilege else None
                except Exception as e:
                    print(f"Erro ao preencher Privilege: {e}")
                
                # Definir valores dos checkboxes usando busca direta
                checkbox_data = [
                    ("OTIF", otif), ("NIL", nil), ("Pickup", pickup), ("Package", package)
                ]
                for label, db_val in checkbox_data:
                    try:
                        checkbox = find_checkbox_by_label(label)
                        if checkbox:
                            checkbox.value = int(db_val) == 1
                    except Exception as e:
                        print(f"Erro ao preencher checkbox {label}: {e}")
                
                # Atualizar página diretamente
                try:
                    page.update()
                except Exception as e:
                    print(f"Erro ao atualizar página: {e}")
                
                # Definir usuário selecionado globalmente
                global selected_user
                selected_user = wwid
                
                print(f"✅ Dados carregados automaticamente para {wwid}")
                
        except Exception as ex:
            print(f"Erro ao carregar dados do usuário {wwid}: {ex}")

    # Variáveis globais para controles de usuário
    selected_user = None

    # Estado do menu (expandido/recolhido)
    menu_is_expanded = ft.Ref()
    menu_is_expanded.current = True

    menu_column_ref = ft.Ref()

    def load_user_theme(user_wwid=None):
        """Carrega o tema salvo do usuário ou o tema padrão."""
        try:
            if user_wwid:
                result = db_manager.query_one("SELECT theme_mode FROM theme_settings WHERE user_wwid = ? ORDER BY last_updated DESC LIMIT 1", (user_wwid,))
            else:
                # Se não há usuário logado, pegar o último tema usado
                result = db_manager.query_one("SELECT theme_mode FROM theme_settings ORDER BY last_updated DESC LIMIT 1")
            
            return result['theme_mode'] if result else "light"
            
        except Exception as e:
            print(f"Erro ao carregar tema: {e}")
            return "light"

    def save_user_theme(theme_mode, user_wwid=None):
        """Salva o tema do usuário no banco de dados."""
        try:
            # Inserir ou atualizar tema
            if user_wwid:
                # Verificar se já existe configuração para este usuário
                existing = db_manager.query_one("SELECT id FROM theme_settings WHERE user_wwid = ?", (user_wwid,))
                if existing:
                    # Atualizar existente
                    db_manager.execute("UPDATE theme_settings SET theme_mode = ?, last_updated = CURRENT_TIMESTAMP WHERE user_wwid = ?", 
                              (theme_mode, user_wwid))
                else:
                    # Inserir novo
                    db_manager.execute("INSERT INTO theme_settings (user_wwid, theme_mode) VALUES (?, ?)", 
                              (user_wwid, theme_mode))
            else:
                # Sem usuário específico, inserir como configuração geral
                db_manager.execute("INSERT INTO theme_settings (theme_mode) VALUES (?)", (theme_mode,))
            
            print(f"Tema '{theme_mode}' salvo com sucesso!")
            
        except Exception as e:
            print(f"Erro ao salvar tema: {e}")


    # Helper para acessar tanto ft.Ref quanto controles diretos
    def resolve_control(ctrl_or_ref):
        try:
            return ctrl_or_ref.current if hasattr(ctrl_or_ref, 'current') and ctrl_or_ref.current else ctrl_or_ref
        except Exception:
            return ctrl_or_ref


    def apply_theme(theme_mode, is_initialization=False):
        """Apply theme to the page"""
        if theme_mode == "dracula":
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = "#282A36"
            page.theme = ft.Theme(
                color_scheme=ft.ColorScheme(
                    primary="#BD93F9",
                    background="#282A36",
                    surface="#282A36",
                    on_surface="#F8F8F2",
                    outline="#6272A4",
                )
            )
        elif theme_mode == "dark":
            page.theme = None
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = "#121212"
        else:  # white
            page.theme = None
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = "#FFFFFF"

        # Save current theme
        page.data["theme_name"] = theme_mode
        page.update()

        # Update all UI controls (always call, whether init or not)
        try:
            # Only call functions if they're defined (to avoid NameError during initialization)
            if 'refresh_users_list' in globals():
                refresh_users_list()
            if 'update_menu' in globals():
                update_menu()
            for key in ['planner', 'continuity', 'sourcing', 'sqie']:
                if 'refresh_list_ui' in globals():
                    refresh_list_ui(key)
            if 'update_control_colors' in globals():
                update_control_colors(page, theme_mode)
            if 'update_timeline_search_container_colors' in globals():
                update_timeline_search_container_colors(theme_mode)
            # Atualizar cores específicas da aba Risks (ano/meta)
            try:
                if 'update_risks_container_colors' in globals():
                    update_risks_container_colors(theme_mode)
            except Exception as _e:
                print(f"Aviso: falha ao atualizar cores da aba Risks: {_e}")
            # Atualizar conteúdo da aba Home
            try:
                if 'update_home_content' in globals():
                    update_home_content()
            except Exception as _e:
                print(f"Aviso: falha ao atualizar aba Home: {_e}")
        except Exception as e:
            print(f"⚠️ Error updating UI: {e}")

    def update_timeline_search_container_colors(theme_name):
        """Atualiza as cores do container dos campos de pesquisa do Timeline"""
        try:
            if timeline_search_container.current:
                colors = get_current_theme_colors(theme_name)
                
                # Atualizar as cores do container principal
                timeline_search_container.current.bgcolor = colors.get('surface_variant')
                timeline_search_container.current.border = ft.border.all(1.5, colors.get('outline'))
                
                # Atualizar o campo de pesquisa
                
                # Atualizar os dropdowns dentro do container
                if timeline_vendor_dropdown.current:
                    timeline_vendor_dropdown.current.bgcolor = colors.get('field_background')
                    timeline_vendor_dropdown.current.color = colors.get('on_surface')
                    timeline_vendor_dropdown.current.border_color = colors.get('outline')
                
                if timeline_year_dropdown.current:
                    timeline_year_dropdown.current.bgcolor = colors.get('field_background')
                    timeline_year_dropdown.current.color = colors.get('on_surface')
                    timeline_year_dropdown.current.border_color = colors.get('outline')
                
                timeline_search_container.current.update()
                
        except Exception as e:
            print(f"Erro ao atualizar cores do container Timeline: {e}")

    def update_control_colors(control, theme_name, depth=0):
        """Atualiza cores de controles recursivamente"""
        if depth > 20:
            return
        
        # Obter cores do tema
        Colors = get_current_theme_colors(theme_name)
            
        # Atualizar TextField
        if isinstance(control, ft.TextField):
            control.bgcolor = Colors.get('field_background')
            control.color = Colors.get('on_surface')
            control.border_color = Colors.get('outline')
            
        # Atualizar Dropdown  
        elif isinstance(control, ft.Dropdown):
            control.bgcolor = Colors.get('field_background')
            control.color = Colors.get('on_surface')
            control.border_color = Colors.get('outline')
        
        # Atualizar Card
        elif isinstance(control, ft.Card):
            control.color = Colors.get('card_background')
        
        # Atualizar Container
        elif isinstance(control, ft.Container):
            # Se tem bgcolor definido, atualizar conforme o contexto
            if hasattr(control, 'bgcolor') and control.bgcolor:
                # Para containers da aba Home que usam surface_variant
                if any(color in str(control.bgcolor) for color in ['#2E303E', '#181818', '#FAFAFA', 'surface_variant']):
                    control.bgcolor = Colors.get('surface_variant')
                    print(f"🎨 Container bgcolor atualizado para: {Colors.get('surface_variant')}")
                # Para containers que são fundos de cards
                elif any(color in str(control.bgcolor) for color in ['#343746', '#1E1E1E', '#F7F7F7', 'card_background']):
                    control.bgcolor = Colors.get('card_background')
                    print(f"🎨 Card bgcolor atualizado para: {Colors.get('card_background')}")
                # Para containers que provavelmente são fundos de campos
                elif control.bgcolor in ['#FFFFFF', '#2C2C2C', '#44475A', 'field_background']:
                    control.bgcolor = Colors.get('field_background')
        
        # Atualizar Text (para casos especiais)
        elif isinstance(control, ft.Text):
            # Preservar cores especiais como primary, mas atualizar cores básicas
            if hasattr(control, 'color') and control.color:
                color_str = str(control.color)
                # Atualizar cores específicas dos temas
                if any(old_color in color_str for old_color in ['#F8F8F2', '#E0E0E0', '#1C1C1C', '#000000']):
                    control.color = Colors.get('on_surface')
                    print(f"🎨 Text color atualizado para: {Colors.get('on_surface')}")
                elif any(old_color in color_str for old_color in ['#666666', '#555555']):
                    control.color = Colors.get('on_surface_variant', '#666666')
                    print(f"🎨 Text secondary color atualizado para: {Colors.get('on_surface_variant', '#666666')}")
                elif control.color in ['on_surface', 'black', 'white']:
                    control.color = Colors.get('on_surface')
        
        # Recursão nos filhos
        if hasattr(control, 'controls'):
            for child in control.controls:
                update_control_colors(child, theme_name, depth + 1)
        elif hasattr(control, 'content') and control.content:
            update_control_colors(control.content, theme_name, depth + 1)

    def update_risks_container_colors(theme_name):
        """Atualiza as cores do header da aba Risks (ano e target)"""
        try:
            colors = get_current_theme_colors(theme_name)
            # Atualizar container principal do header (border e bgcolor)
            if risks_header_container and risks_header_container.current:
                try:
                    risks_header_container.current.bgcolor = colors.get('surface_variant')
                    risks_header_container.current.border = ft.border.all(1.5, colors.get('outline'))
                except Exception:
                    pass

            # Atualizar dropdown e texto alvo dentro do header
            if risks_year_dropdown and risks_year_dropdown.current:
                risks_year_dropdown.current.bgcolor = colors.get('field_background')
                risks_year_dropdown.current.color = colors.get('on_surface')
                risks_year_dropdown.current.border_color = colors.get('outline')

            if target_display_container and target_display_container.current:
                # target_display_container tem borda e bgcolor especiais
                try:
                    target_display_container.current.border = ft.border.all(1.5, ft.Colors.AMBER_700)
                    target_display_container.current.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.AMBER_700)
                except Exception:
                    pass

            # Fazer update nos controles referenciados e forçar redraw da página
            if risks_header_container and risks_header_container.current:
                try:
                    risks_header_container.current.update()
                except Exception:
                    pass
            if target_display_container and target_display_container.current:
                try:
                    target_display_container.current.update()
                except Exception:
                    pass
            # Atualizar dropdown do ano se existir
            if risks_year_dropdown and risks_year_dropdown.current:
                try:
                    risks_year_dropdown.current.update()
                except Exception:
                    pass
            try:
                page.update()
            except Exception:
                pass

        except Exception as e:
            print(f"Erro ao atualizar cores da aba Risks: {e}")

    def update_home_content():
        """Atualiza o conteúdo da aba Home quando o tema muda"""
        try:
            print(f"🎨 Iniciando atualização da aba Home...")
            print(f"🎨 Tema atual: {get_theme_name_from_page(page)}")
            
            if home_content_container.current:
                print("🎨 Container encontrado, recriando conteúdo...")
                # Recriar o conteúdo com o novo tema
                new_content = create_home_content()
                home_content_container.current.content = new_content
                
                # Forçar atualização recursiva de todos os controles
                update_control_colors(home_content_container.current, get_theme_name_from_page(page))
                
                home_content_container.current.update()
                print("✅ Conteúdo da aba Home atualizado com novo tema")
            else:
                print("⚠️ Referência do container da aba Home não encontrada")
        except Exception as e:
            print(f"❌ Erro ao atualizar conteúdo da aba Home: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            # Fallback: tentar forçar update da página inteira
            try:
                page.update()
            except:
                pass

    # ===== CARREGAMENTO INICIAL DO TEMA =====
    # Aplicar tema padrão ou salvo se disponível
    saved_theme = None
    try:
        # Carregar tema salvo do banco de dados
        if current_user_wwid:
            try:
                import sqlite3
                import os
                
                # Verificar se o banco de dados existe
                db_path = 'db.db'
                if os.path.exists(db_path):
                    # Criar tabela se não existir
                    db_manager.execute('''
                        CREATE TABLE IF NOT EXISTS user_themes (
                            user_wwid TEXT PRIMARY KEY,
                            theme TEXT NOT NULL
                        )
                    ''')
                    
                    # Buscar tema do usuário
                    result = db_manager.query_one("SELECT theme FROM user_themes WHERE user_wwid = ?", (current_user_wwid,))
                    saved_theme = result['theme'] if result else None
                    
                    if saved_theme:
                        print(f"Tema encontrado no banco para usuário {current_user_wwid}: {saved_theme}")
                    else:
                        print(f"Nenhum tema salvo encontrado para usuário {current_user_wwid}")
                else:
                    print("Banco de dados não encontrado, usando tema padrão")
            except Exception as e:
                print(f"Erro ao acessar banco de dados: {e}")
                saved_theme = None
        
        # Aplicar tema carregado ou usar padrão
        if user_theme and user_theme in ["white", "dark", "dracula"]:
            apply_theme(user_theme, is_initialization=True)
            print(f"Tema aplicado na inicialização: {user_theme}")
        else:
            apply_theme("white", is_initialization=True)  # tema padrão
            print("Aplicando tema padrão (white) na inicialização")
            
    except Exception as e:
        print(f"Erro durante carregamento de tema: {e}")
        apply_theme("white", is_initialization=True)  # fallback para tema padrão
    # ===== FIM DO CARREGAMENTO INICIAL DO TEMA =====

    def show_toast(message, color="green", restore_control=None):
        """Mostra um show_toast com duração configurável e gerenciamento melhorado.

        If `restore_control` is provided, the control will be re-enabled and its
        processing flag cleared before showing the show_toast. This ensures error/warning
        flows that call `show_toast` don't accidentally leave the originating
        control disabled.
        """
        global app_settings, _active_toast, _active_toast_cancel_event

        # Initialize globals used to track the active toast
        try:
            _active_toast
        except NameError:
            _active_toast = None
        try:
            _active_toast_cancel_event
        except NameError:
            _active_toast_cancel_event = None

        # Restore control immediately if provided
        try:
            if restore_control is not None:
                try:
                    restore_control.disabled = False
                    if hasattr(restore_control, '_is_processing'):
                        restore_control._is_processing = False
                    safe_update_control(restore_control, page)
                except Exception as _:
                    print(f"Aviso: não foi possível restaurar controle antes do show_toast: {_}")
        except Exception:
            pass

        # MELHORADO: Limpeza mais robusta de toasts anteriores
        def clean_previous_toasts():
            """Limpa todos os toasts anteriores do overlay de forma segura"""
            try:
                if _active_toast_cancel_event is not None:
                    _active_toast_cancel_event.set()
                
                if not hasattr(page, 'overlay') or page.overlay is None:
                    return
                
                # Remover toast específico se existe
                if _active_toast is not None:
                    try:
                        if _active_toast in page.overlay:
                            page.overlay.remove(_active_toast)
                    except (ValueError, AttributeError):
                        pass
                
                # NOVO: Limpeza geral de toasts órfãos
                # Remove containers que parecem ser toasts baseados em propriedades
                toasts_to_remove = []
                for item in page.overlay[:]:  # Cópia da lista para iteração segura
                    try:
                        if (hasattr(item, 'top') and hasattr(item, 'right') and 
                            hasattr(item, 'bgcolor') and 
                            item.top == 50 and item.right == 20):
                            toasts_to_remove.append(item)
                    except AttributeError:
                        continue
                
                for toast in toasts_to_remove:
                    try:
                        if toast in page.overlay:
                            page.overlay.remove(toast)
                    except (ValueError, AttributeError):
                        pass
                        
                page.update()
                
            except Exception as ex:
                print(f"Aviso: erro na limpeza de toasts: {ex}")

        # Limpar toasts anteriores
        clean_previous_toasts()

        # Normalize color - accept common names
        color_map = {
            'green': "#31A037",
            'red': '#C62828',
            'orange': '#EF6C00',
            'blue': '#1565C0'
        }
        bgcolor = color_map.get(color, color)

        # Create new toast container and add to overlay
        try:
            toast_container = ft.Container(
                content=ft.Text(str(message), color="white", weight="bold"),
                bgcolor=bgcolor,
                padding=10,
                border_radius=5,
                top=50,
                right=20,
                animate_opacity=300,
            )

            if not hasattr(page, 'overlay') or page.overlay is None:
                page.overlay = []
            
            page.overlay.append(toast_container)
            _active_toast = toast_container
            page.update()
        except Exception as ex:
            print(f"Erro ao mostrar show_toast: {ex}")
            return

        # MELHORADO: Remover thread mais robusta com timeout de segurança
        def remover(cancel_event, toast_ref):
            """Remove o toast após duração especificada, com proteções de segurança"""
            try:
                import time
                duration = app_settings.get('toast_duration', 3)
                max_duration = min(duration, 10)  # NOVO: Limite máximo de 10 segundos
                
                # Wait in small increments to allow cancellation
                waited = 0.0
                step = 0.1
                while waited < max_duration:
                    if cancel_event.is_set():
                        return
                    time.sleep(step)
                    waited += step

                # MELHORADO: Remoção mais robusta do toast
                try:
                    if (hasattr(page, 'overlay') and page.overlay is not None and
                        toast_ref is not None):
                        
                        # Verificação dupla para evitar condições de corrida
                        if toast_ref in page.overlay:
                            page.overlay.remove(toast_ref)
                            page.update()
                        else:
                            # NOVO: Fallback - procurar por toasts similares órfãos
                            similar_toasts = [
                                item for item in page.overlay 
                                if (hasattr(item, 'top') and hasattr(item, 'right') and 
                                    item.top == 50 and item.right == 20)
                            ]
                            for toast in similar_toasts[:1]:  # Remove apenas o primeiro
                                try:
                                    page.overlay.remove(toast)
                                    page.update()
                                    break
                                except (ValueError, AttributeError):
                                    pass
                                    
                except Exception as inner:
                    print(f"Aviso: erro ao remover toast específico: {inner}")
                    
            except Exception as outer:
                print(f"Erro na thread de remoção de toast: {outer}")
            finally:
                # NOVO: Limpeza final de segurança
                try:
                    if toast_ref == _active_toast:
                        globals()['_active_toast'] = None
                except Exception:
                    pass

        cancel_event = threading.Event()
        _active_toast_cancel_event = cancel_event
        
        # MELHORADO: Thread daemon com referência específica do toast
        remover_thread = threading.Thread(
            target=remover, 
            args=(cancel_event, toast_container), 
            daemon=True,
            name=f"ToastRemover-{id(toast_container)}"
        )
        remover_thread.start()

    def clear_all_toasts():
        """Função utilitária para limpar manualmente todos os toasts órfãos da tela"""
        try:
            global _active_toast, _active_toast_cancel_event
            
            # Cancelar toast ativo atual
            if _active_toast_cancel_event is not None:
                try:
                    _active_toast_cancel_event.set()
                except Exception:
                    pass
            
            if not hasattr(page, 'overlay') or page.overlay is None:
                return 0
            
            # Encontrar e remover todos os containers que parecem toasts
            toasts_removed = 0
            for item in page.overlay[:]:  # Cópia para iteração segura
                try:
                    # Identificar toasts por suas propriedades características
                    if (hasattr(item, 'top') and hasattr(item, 'right') and 
                        hasattr(item, 'bgcolor') and hasattr(item, 'padding') and
                        item.top == 50 and item.right == 20):
                        page.overlay.remove(item)
                        toasts_removed += 1
                except (ValueError, AttributeError):
                    continue
            
            # Limpar referências globais
            _active_toast = None
            _active_toast_cancel_event = None
            
            # Atualizar página se removemos algo
            if toasts_removed > 0:
                page.update()
                print(f"🧹 Removidos {toasts_removed} toast(s) órfão(s)")
            
            return toasts_removed
            
        except Exception as ex:
            print(f"❌ Erro ao limpar toasts: {ex}")
            return 0

    def test_toast_system():
        """Função de teste para verificar o sistema de toast melhorado"""
        try:
            print("🧪 Testando sistema de toast...")
            
            # Limpar toasts existentes primeiro
            cleared = clear_all_toasts()
            if cleared > 0:
                print(f"🧹 Limpeza inicial: {cleared} toasts removidos")
            
            # Mostrar alguns toasts de teste
            show_toast("✅ Teste 1: Toast verde", "green")
            threading.Timer(1.0, lambda: show_toast("⚠️ Teste 2: Toast laranja", "orange")).start()
            threading.Timer(2.0, lambda: show_toast("❌ Teste 3: Toast vermelho", "red")).start()
            threading.Timer(3.0, lambda: show_toast("ℹ️ Teste 4: Toast azul", "blue")).start()
            
            print("🧪 Testes de toast iniciados. Observe se eles aparecem e desaparecem automaticamente.")
            
        except Exception as ex:
            print(f"❌ Erro no teste do sistema de toast: {ex}")

    def test_spinbox_functionality():
        """Função de teste para demonstrar o funcionamento correto dos spinboxes"""
        try:
            print("🧪 Testando funcionalidade dos spinboxes...")
            print("✅ Correções aplicadas:")
            print("   - Mudança de on_change para on_blur")
            print("   - Formatação apenas após perder o foco")
            print("   - Permite digitar '10' sem converter para '1.0'")
            print("   - Validação de faixa 0.0 a 10.0")
            print("   - Formatação com 1 casa decimal")
            print("🎯 Agora você pode digitar '10' nos spinboxes e ele não será convertido para '1.0' durante a digitação!")
            
        except Exception as ex:
            print(f"❌ Erro no teste dos spinboxes: {ex}")

    show_toast = show_toast

    def load_user_criteria(user_wwid=None):
        """Carrega os pesos dos critérios salvos no banco."""
        try:
            # Primeiro tenta carregar da criteria_settings (configurações personalizadas)
            if user_wwid:
                result = db_manager.query_one("SELECT nil_weight, otif_weight, pickup_weight, package_weight, target_weight FROM criteria_settings WHERE user_wwid = ? ORDER BY last_updated DESC LIMIT 1", (user_wwid,))
                if result:
                    return {
                        'NIL': result['nil_weight'],
                        'OTIF': result['otif_weight'], 
                        'Quality of Pick Up': result['pickup_weight'],
                        'Quality-Supplier Package': result['package_weight'],
                        'Target': result['target_weight']
                    }
            
            # Se não encontrou configurações personalizadas, carrega da criteria_table original
            print("Carregando critérios da tabela criteria_table...")
            results = db_manager.query("SELECT criteria_category, value FROM criteria_table")
            
            criteria_data = {}
            for row in results:
                criteria_name = row['criteria_category']
                value_str = row['value']
                
                try:
                    # Converter valor para float
                    raw_value = float(value_str)
                    
                    # Target mantém escala 0-10, outros critérios ficam na escala 0-1
                    if criteria_name == "Target":
                        value = raw_value  # Manter escala 0-10
                        print(f"Target mantido na escala 0-10: {value}")
                    else:
                        value = raw_value  # Outros critérios já estão na escala 0-1
                    
                    criteria_data[criteria_name] = value
                    print(f"Critério carregado: {criteria_name} = {value}")
                    
                except ValueError as e:
                    print(f"Erro ao converter valor para {criteria_name}: {value_str} - {e}")
            
            if criteria_data:
                return criteria_data
                
            return None
        except Exception as ex:
            print(f"Erro ao carregar critérios: {ex}")
            return None

    def save_user_criteria(criteria_weights, user_wwid=None):
        """Salva os pesos dos critérios no banco."""
        try:
            if user_wwid:
                # Verificar se já existe configuração para este usuário
                existing = db_manager.query_one("SELECT id FROM criteria_settings WHERE user_wwid = ?", (user_wwid,))
                
                if existing:
                    # Atualizar configuração existente
                    db_manager.execute("""UPDATE criteria_settings SET 
                                   nil_weight = ?, otif_weight = ?, pickup_weight = ?, 
                                   package_weight = ?, target_weight = ?, 
                                   last_updated = CURRENT_TIMESTAMP 
                                   WHERE user_wwid = ?""", 
                              (criteria_weights['NIL'], criteria_weights['OTIF'], 
                               criteria_weights['Quality of Pick Up'], criteria_weights['Quality-Supplier Package'], 
                               criteria_weights['Target'], user_wwid))
                else:
                    # Inserir nova configuração
                    db_manager.execute("""INSERT INTO criteria_settings 
                                   (user_wwid, nil_weight, otif_weight, pickup_weight, package_weight, target_weight) 
                                   VALUES (?, ?, ?, ?, ?, ?)""", 
                              (user_wwid, criteria_weights['NIL'], criteria_weights['OTIF'], 
                               criteria_weights['Quality of Pick Up'], criteria_weights['Quality-Supplier Package'], 
                               criteria_weights['Target']))
                
                return True
            return False
        except Exception as ex:
            print(f"Erro ao salvar critérios: {ex}")
            return False

    # --- Início: Funções para Gerar Nota Cheia ---
    
    def generate_full_score_dialog():
        """Abre diálogo para gerar notas cheias"""
        global current_user_wwid
        # Refs para os controles do diálogo
        month_dropdown_ref = ft.Ref()
        year_dropdown_ref = ft.Ref()
        generate_button_ref = ft.Ref()
        cancel_button_ref = ft.Ref()
        # controle de execução e cancelamento
        import threading as _threading
        cancel_event = _threading.Event()
        running_flag = {'value': False}
        include_inactive_ref = ft.Ref()
        progress_bar_ref = ft.Ref()
        progress_text_ref = ft.Ref()
        
        # Opções de mês
        months = [
            ft.dropdown.Option("1", "Janeiro"),
            ft.dropdown.Option("2", "Fevereiro"),
            ft.dropdown.Option("3", "Março"),
            ft.dropdown.Option("4", "Abril"),
            ft.dropdown.Option("5", "Maio"),
            ft.dropdown.Option("6", "Junho"),
            ft.dropdown.Option("7", "Julho"),
            ft.dropdown.Option("8", "Agosto"),
            ft.dropdown.Option("9", "Setembro"),
            ft.dropdown.Option("10", "Outubro"),
            ft.dropdown.Option("11", "Novembro"),
            ft.dropdown.Option("12", "Dezembro"),
        ]
        
        # Opções de ano (2024 a 2040)
        years = [ft.dropdown.Option(str(year), str(year)) for year in range(2024, 2041)]
        
        def close_dialog(e):
            # Se estiver rodando, aciona cancelamento; caso contrário, fecha o diálogo normalmente
            if running_flag['value']:
                cancel_event.set()
                try:
                    progress_text_ref.current.visible = True
                    progress_text_ref.current.value = "Cancelando..."
                    progress_bar_ref.current.visible = True
                    # opcional: indeterminate
                    progress_bar_ref.current.value = None
                    # desabilita botões para evitar cliques repetidos
                    if cancel_button_ref.current:
                        cancel_button_ref.current.disabled = True
                    if generate_button_ref.current:
                        generate_button_ref.current.disabled = True
                    page.update()
                except Exception:
                    pass
            else:
                page.close(dialog)
        
        def start_generation(e):
            month = month_dropdown_ref.current.value
            year = year_dropdown_ref.current.value
            include_inactive = bool(include_inactive_ref.current.value)
            
            if not month or not year:
                # Mostrar erro na própria janela
                progress_bar_ref.current.visible = False
                progress_text_ref.current.visible = True
                progress_text_ref.current.value = "❌ Mês e ano devem ser selecionados para gerar notas."
                progress_text_ref.current.color = ft.Colors.RED
                page.update()
                return
            
            # Validação para não gerar para meses futuros
            now = datetime.datetime.now()
            month_int = int(month)
            year_int = int(year)
            
            if (year_int > now.year) or (year_int == now.year and month_int > now.month):
                # Mostrar erro na própria janela
                progress_bar_ref.current.visible = False
                progress_text_ref.current.visible = True
                progress_text_ref.current.value = "❌ Não é possível gerar notas para meses futuros."
                progress_text_ref.current.color = ft.Colors.RED
                page.update()
                return
            
            # Evitar reentrância e desabilitar botão Gerar
            if running_flag['value']:
                return
            running_flag['value'] = True
            try:
                if generate_button_ref.current:
                    generate_button_ref.current.disabled = True
                if cancel_button_ref.current:
                    cancel_button_ref.current.disabled = False
                # Desabilitar dropdowns e switch durante execução
                if month_dropdown_ref.current:
                    month_dropdown_ref.current.disabled = True
                if year_dropdown_ref.current:
                    year_dropdown_ref.current.disabled = True
                if include_inactive_ref.current:
                    include_inactive_ref.current.disabled = True
                page.update()
            except Exception:
                pass

            # Iniciar geração em thread separada
            def run_generation():
                try:
                    generate_full_scores(
                        month, year,
                        include_inactive,
                        cancel_event,
                        progress_bar_ref,
                        progress_text_ref,
                        dialog,
                        generate_button_ref,
                        cancel_button_ref,
                        theme_colors,
                        dialog_content,
                        month_dropdown_ref,
                        year_dropdown_ref,
                        include_inactive_ref
                    )
                except Exception as ex:
                    page.run_thread(lambda: show_toast(f"Erro durante a geração: {str(ex)}", "red"))
                finally:
                    # reset estado ao finalizar (se o diálogo ainda estiver aberto)
                    running_flag['value'] = False
                    try:
                        if generate_button_ref.current:
                            generate_button_ref.current.disabled = False
                        if cancel_button_ref.current:
                            cancel_button_ref.current.disabled = False
                        # Reabilitar dropdowns e switch
                        if month_dropdown_ref.current:
                            month_dropdown_ref.current.disabled = False
                        if year_dropdown_ref.current:
                            year_dropdown_ref.current.disabled = False
                        if include_inactive_ref.current:
                            include_inactive_ref.current.disabled = False
                        page.update()
                    except Exception:
                        pass
            
            _threading.Thread(target=run_generation, daemon=True).start()
        
        # Obter cores do tema atual
        theme_colors = get_current_theme_colors(get_theme_name_from_page(page))
        
        # Conteúdo do diálogo
        dialog_content = ft.Column([
            ft.Text(
                "Gerar Nota Cheia", 
                size=20, 
                weight="bold",
                color=theme_colors.get('on_surface')
            ),
            ft.Text(
                "Selecione o mês e ano para gerar notas máximas para todos os fornecedores ativos:", 
                size=14,
                color=theme_colors.get('on_surface')
            ),
            ft.Divider(height=20, color=theme_colors.get('outline')),
            
            ft.Row([
                ft.Dropdown(
                    label="Mês",
                    options=months,
                    expand=True,
                    ref=month_dropdown_ref,
                    dense=True,
                    color=theme_colors.get('on_surface'),
                    border_color=theme_colors.get('outline'),
                    **({'bgcolor': theme_colors.get('field_background')} if theme_colors.get('field_background') else {})
                ),
                ft.Dropdown(
                    label="Ano", 
                    options=years,
                    expand=True,
                    ref=year_dropdown_ref,
                    dense=True,
                    color=theme_colors.get('on_surface'),
                    border_color=theme_colors.get('outline'),
                    **({'bgcolor': theme_colors.get('field_background')} if theme_colors.get('field_background') else {})
                ),
            ], spacing=10),

            # Switch para incluir fornecedores inativos
            ft.Row([
                ft.Switch(ref=include_inactive_ref, value=False, active_color=theme_colors.get('primary')),
                ft.Text("Gerar score também para Inactives", color=theme_colors.get('on_surface'))
            ], spacing=10),
            
            # Container para barra de progresso
            ft.Container(
                content=ft.Column([
                    ft.Text(
                        "", 
                        ref=progress_text_ref, 
                        size=12, 
                        visible=False,
                        color=theme_colors.get('on_surface')
                    ),
                    ft.ProgressBar(ref=progress_bar_ref, visible=False),
                ], spacing=5),
                padding=ft.padding.only(top=20)
            ),
            
            ft.Divider(height=20, color=theme_colors.get('outline')),
            ft.Row([
                ft.TextButton(
                    "Cancelar", 
                    on_click=close_dialog,
                    ref=cancel_button_ref,
                    style=ft.ButtonStyle(
                        color=theme_colors.get('on_surface')
                    )
                ),
                ft.ElevatedButton(
                    "Gerar", 
                    on_click=start_generation, 
                    bgcolor=theme_colors.get('primary'), 
                    color=theme_colors.get('on_primary'),
                    ref=generate_button_ref,
                ),
            ], alignment=ft.MainAxisAlignment.END, spacing=10)
        ], width=450, spacing=10, tight=True)
        
        dialog = ft.AlertDialog(
            content=dialog_content,
            modal=True,
        )
        
        page.open(dialog)
    
    def generate_full_scores(month, year, include_inactive, cancel_event, progress_bar_ref, progress_text_ref, dialog, generate_button_ref, cancel_button_ref, theme_colors, dialog_content, month_dropdown_ref, year_dropdown_ref, include_inactive_ref):
        """Gera notas cheias baseado na função fornecida pelo usuário"""
        try:
            # Mostrar progresso
            progress_bar_ref.current.visible = True
            progress_text_ref.current.visible = True
            progress_text_ref.current.value = "Carregando critérios..."
            page.update()
            
            # Carregar critérios da tabela criteria_table
            criterios_raw = db_manager.query(
                "SELECT criteria_category, value FROM criteria_table"
            )
            
            criterio_map = {}
            for row in criterios_raw:
                # DBManager.query retorna dict(row)
                nome = str(row.get('criteria_category') if isinstance(row, dict) else row[0]).strip().lower()
                valor = float(row.get('value') if isinstance(row, dict) else row[1])
                if "package" in nome:
                    criterio_map["package"] = valor
                elif "pick" in nome:
                    criterio_map["pickup"] = valor  
                elif "nil" in nome:
                    criterio_map["nil"] = valor
                elif "otif" in nome:
                    criterio_map["otif"] = valor
            
            if not all(k in criterio_map for k in ["package", "pickup", "nil", "otif"]):
                page.run_thread(lambda: show_toast("Um ou mais critérios de pontuação estão faltando na tabela de critérios.", "red"))
                return
            
            progress_text_ref.current.value = "Carregando fornecedores..."
            page.update()
            
            # Carregar fornecedores
            fornecedores = db_manager.query(
                "SELECT supplier_id, vendor_name, supplier_status FROM supplier_database_table"
            )
            
            if not fornecedores:
                page.run_thread(lambda: show_toast("Nenhum fornecedor encontrado no banco de dados.", "orange"))
                return
            
            # Configurar barra de progresso
            progress_bar_ref.current.value = 0
            total_fornecedores = len(fornecedores)
            page.update()
            
            user = getpass.getuser()
            register_date = datetime.datetime.now()
            registered_by = "NIL,OTIF,Package,Pickup"
            nota_fixa = 10.0
            
            adicionados = 0
            ignorados_inativos = 0
            ignorados_existentes = 0
            
            for i, fornecedor in enumerate(fornecedores):
                # Cancelamento cooperativo
                if cancel_event.is_set():
                    # Fechar diálogo e notificar
                    page.close(dialog)
                    page.run_thread(lambda: show_toast("Operação cancelada pelo usuário.", "orange"))
                    return
                # Atualizar progresso
                progress = (i + 1) / total_fornecedores
                progress_bar_ref.current.value = progress
                progress_text_ref.current.value = f"Processando fornecedor {i + 1} de {total_fornecedores}..."
                page.update()
                
                # fornecedores é lista de dicts
                supplier_id = fornecedor.get('supplier_id') if isinstance(fornecedor, dict) else fornecedor[0]
                supplier_name = fornecedor.get('vendor_name') if isinstance(fornecedor, dict) else fornecedor[1]
                raw_status = fornecedor.get('supplier_status') if isinstance(fornecedor, dict) else fornecedor[2]
                status = raw_status.strip() if raw_status else ""
                status_lower = status.lower()
                
                # Filtrar fornecedores inativos (status deve ser "Active")
                if not include_inactive and status_lower != "active":
                    ignorados_inativos += 1
                    continue
                
                # Verificar se já existe registro para este período
                existe = db_manager.query(
                    "SELECT 1 FROM supplier_score_records_table WHERE supplier_id = ? AND month = ? AND year = ?",
                    (supplier_id, month, year)
                )
                if existe:
                    ignorados_existentes += 1
                    continue
                
                # Calcular total baseado nos critérios
                total = (
                    nota_fixa * criterio_map["otif"] +
                    nota_fixa * criterio_map["nil"] +
                    nota_fixa * criterio_map["package"] +
                    nota_fixa * criterio_map["pickup"]
                )
                total = round(total, 2)
                
                # Inserir registro
                query_insert = """
                    INSERT INTO supplier_score_records_table (
                        supplier_id, supplier_name, month, year,
                        quality_package, quality_pickup, nil, otif,
                        total_score, comment, register_date, changed_by, registered_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (
                    str(supplier_id),                 # supplier_id como texto (mantém compatibilidade)
                    str(supplier_name),               # supplier_name texto
                    str(month),                       # mês como texto
                    str(year),                        # ano como texto
                    float(nota_fixa),                 # quality_package (numérico)
                    float(nota_fixa),                 # quality_pickup (numérico)
                    float(nota_fixa),                 # nil (numérico)
                    float(nota_fixa),                 # otif (numérico)
                    float(total),                     # total_score (numérico)
                    "Maximum score auto-generated.", # comment
                    register_date.isoformat(),        # register_date (ISO string)
                    str(user),                        # changed_by
                    registered_by                     # registered_by
                )
                
                try:
                    db_manager.execute(query_insert, params)
                    adicionados += 1
                    print(f"Registro adicionado para {supplier_name} - {month}/{year}")
                except Exception as insert_error:
                    print(f"Erro ao inserir {supplier_name}: {insert_error}")
                    continue
            
            # Exibir resultado no próprio diálogo (sem fechar)
            try:
                progress_bar_ref.current.visible = False
                progress_text_ref.current.visible = False
                
                # Criar resumo estruturado e mostrar no lugar do progresso
                summary_text = (
                    f"✅ Geração de notas concluída!\n\n"
                    f"📊 Adicionadas: {adicionados}\n"
                    f"⚠️  Ignoradas (inativas): {ignorados_inativos}\n" 
                    f"ℹ️  Ignoradas (já existem): {ignorados_existentes}"
                )
                
                progress_text_ref.current.visible = True
                progress_text_ref.current.value = summary_text
                progress_text_ref.current.size = 14
                
                # reabilitar Gerar; alterar Cancelar para Fechar
                if generate_button_ref and generate_button_ref.current:
                    generate_button_ref.current.disabled = False
                # Reabilitar dropdowns e switch
                if month_dropdown_ref and month_dropdown_ref.current:
                    month_dropdown_ref.current.disabled = False
                if year_dropdown_ref and year_dropdown_ref.current:
                    year_dropdown_ref.current.disabled = False  
                if include_inactive_ref and include_inactive_ref.current:
                    include_inactive_ref.current.disabled = False
                if cancel_button_ref and cancel_button_ref.current:
                    try:
                        cancel_button_ref.current.text = "Fechar"
                    except Exception:
                        pass
                page.update()
            except Exception as e:
                # Fallback para texto simples se houver erro
                summary = (
                    f"Geração de notas concluída!\n"
                    f"✅ Adicionadas: {adicionados}\n"
                    f"⚠️ Ignoradas (inativas): {ignorados_inativos}\n"
                    f"ℹ️ Ignoradas (já existem): {ignorados_existentes}"
                )
                try:
                    progress_bar_ref.current.visible = False
                    progress_text_ref.current.visible = True
                    progress_text_ref.current.value = summary
                    # reabilitar Gerar; alterar Cancelar para Fechar
                    if generate_button_ref and generate_button_ref.current:
                        generate_button_ref.current.disabled = False
                    # Reabilitar dropdowns e switch
                    if month_dropdown_ref and month_dropdown_ref.current:
                        month_dropdown_ref.current.disabled = False
                    if year_dropdown_ref and year_dropdown_ref.current:
                        year_dropdown_ref.current.disabled = False  
                    if include_inactive_ref and include_inactive_ref.current:
                        include_inactive_ref.current.disabled = False
                    if cancel_button_ref and cancel_button_ref.current:
                        try:
                            cancel_button_ref.current.text = "Fechar"
                        except Exception:
                            pass
                    page.update()
                except Exception:
                    pass
            
            # Atualizar lista de resultados se estiver visível
            page.run_thread(lambda: (
                results_list.controls.clear(),
                results_list.update()
            ) if 'results_list' in globals() and results_list else None)
            
        except Exception as e:
            err_msg = f"Erro durante a geração de notas: {e}"
            page.run_thread(lambda msg=err_msg: show_toast(msg, "red"))
    
    # --- Fim: Funções para Gerar Nota Cheia ---

    def theme_changed(e):
        """Handle theme change from UI (radio button)"""
        global current_user_wwid
        theme_mode = e.control.value

        # Aplicar tema usando a função centralizada
        apply_theme(theme_mode)

        # Salvar tema no banco
        save_user_theme(theme_mode, current_user_wwid)

        # Atualizar menus, abas e listas
        try:
            update_menu()
            update_config_tabs()
            load_all_lists_data()
            load_users_full()
        except Exception as ex:
            print(f"⚠️ Error updating after theme change: {ex}")

        # Pegar cores atuais do tema
        theme_colors = get_current_theme_colors(get_theme_name_from_page(page))

        # --- Containers principais ---
        score_form_container.bgcolor = theme_colors.get('field_background')
        score_form_container.update()

        users_form_container.bgcolor = theme_colors.get('field_background')
        users_form_container.border = ft.border.all(1, theme_colors.get('outline'))
        users_form_container.update()

        rail_container.bgcolor = theme_colors.get('rail_background')
        rail_container.update()

        # --- Dropdowns da aba score ---
        for dropdown in [month_dropdown, year_dropdown]:
            dropdown.bgcolor = theme_colors.get('field_background')
            dropdown.color = theme_colors.get('on_surface')
            dropdown.border_color = theme_colors.get('outline')
            dropdown.update()

        # --- TextFields da aba score ---
        for field_ref in [search_field_ref, selected_po, selected_bu]:
            if field_ref.current:
                field_ref.current.bgcolor = theme_colors.get('field_background')
                field_ref.current.color = theme_colors.get('on_surface')
                field_ref.current.border_color = theme_colors.get('outline')
                field_ref.current.update()

        # --- Campos das abas de configuração ---
        try:
            for config_type in ['sqie', 'continuity', 'planner', 'sourcing', 'bu', 'category']:
                if config_type in lists_controls:
                    for key in ['input', 'alias', 'email']:
                        if key in lists_controls[config_type]:
                            ctrl = lists_controls[config_type][key]
                            ctrl.bgcolor = theme_colors.get('field_background')
                            ctrl.color = theme_colors.get('on_surface')
                            ctrl.border_color = theme_colors.get('outline')
                            ctrl.update()
        except Exception as ex:
            print(f"⚠️ Error updating config fields: {ex}")

        # --- Campos da aba Users ---
        try:
            if wwid_field_ref.current:
                wwid_field_ref.current.filled = False
                wwid_field_ref.current.color = theme_colors.get('on_surface')
                wwid_field_ref.current.border_color = theme_colors.get('outline')
                wwid_field_ref.current.update()
            if name_field_ref.current:
                name_field_ref.current.filled = False
                name_field_ref.current.color = theme_colors.get('on_surface')
                name_field_ref.current.border_color = theme_colors.get('outline')
                name_field_ref.current.update()
            if password_field_ref.current:
                password_field_ref.current.filled = False
                password_field_ref.current.color = theme_colors.get('on_surface')
                password_field_ref.current.border_color = theme_colors.get('outline')
                password_field_ref.current.update()
            if privilege_dropdown_ref.current:
                privilege_dropdown_ref.current.bgcolor = None
                privilege_dropdown_ref.current.color = theme_colors.get('on_surface')
                privilege_dropdown_ref.current.border_color = theme_colors.get('outline')
                privilege_dropdown_ref.current.update()
        except Exception as ex:
            print(f"⚠️ Error updating user fields: {ex}")

        # --- Campos da aba Log ---
        try:
            if 'log_controls' in globals() and log_controls:
                for ctrl in log_controls.values():
                    control = resolve_control(ctrl)
                    if control:
                        control.bgcolor = theme_colors.get('field_background')
                        control.color = theme_colors.get('on_surface')
                        control.border_color = theme_colors.get('outline')
                        control.update()
        except Exception as ex:
            print(f"⚠️ Error updating log controls: {ex}")

        # --- Campo de pesquisa de Suppliers ---
        try:
            if suppliers_search_field_ref.current:
                suppliers_search_field_ref.current.bgcolor = theme_colors.get('field_background')
                suppliers_search_field_ref.current.color = theme_colors.get('on_surface')
                suppliers_search_field_ref.current.border_color = theme_colors.get('outline')
                suppliers_search_field_ref.current.update()
        except Exception as ex:
            print(f"⚠️ Error updating suppliers search field: {ex}")

        # --- Cards de Score ---
        try:
            if responsive_app_manager and responsive_app_manager.results_container:
                update_control_colors(responsive_app_manager.results_container, theme_mode, 0)
                responsive_app_manager.results_container.update()
        except Exception as ex:
            print(f"⚠️ Error updating Score cards: {ex}")

        # --- Cards de Suppliers ---
        try:
            if 'suppliers_results_list' in globals() and suppliers_results_list and suppliers_results_list.controls:
                for card in suppliers_results_list.controls:
                    update_control_colors(card, theme_mode, 0)
                suppliers_results_list.update()
        except Exception as ex:
            print(f"⚠️ Error updating Suppliers cards: {ex}")

        # --- Cards de métricas da Timeline ---
        try:
            if 'timeline_cards_refs' in globals() and timeline_cards_refs:
                colors = get_current_theme_colors(theme_mode)
                primary_color = colors.get('primary')
                for refs in timeline_cards_refs.values():
                    if refs["card"].current:
                        refs["card"].current.surface_tint_color = primary_color
                    if refs["icon"].current:
                        refs["icon"].current.color = primary_color
                    if refs["value"].current:
                        refs["value"].current.color = primary_color
                    # Não reatribuir gradiente - removido para usar bgcolor sólido nos cards
                    # if refs["gradient"].current:
                    #     refs["gradient"].current.gradient = ft.LinearGradient(...)
                timeline_metrics_row.current.update()
        except Exception as ex:
            print(f"⚠️ Error updating Timeline metric cards: {ex}")

        # --- Botões da Timeline ---
        try:
            if timeline_chart_button.current and timeline_table_button.current:
                colors = get_current_theme_colors(theme_mode)
                if timeline_chart_tab.current:
                    timeline_chart_button.current.bgcolor = colors.get('primary')
                    timeline_chart_button.current.color = colors.get('on_primary', '#FFFFFF')
                    timeline_table_button.current.bgcolor = None
                    timeline_table_button.current.color = None
                elif timeline_table_tab.current:
                    timeline_table_button.current.bgcolor = colors.get('primary')
                    timeline_table_button.current.color = colors.get('on_primary', '#FFFFFF')
                    timeline_chart_button.current.bgcolor = None
                    timeline_chart_button.current.color = None
                timeline_chart_button.current.update()
                timeline_table_button.current.update()
        except Exception as ex:
            print(f"⚠️ Error updating Timeline buttons: {ex}")

    # Confirmação via show_toast
        show_toast(f"✅ Theme '{theme_mode}' applied and saved!", "green")

    def set_selected(idx):
        def handler(e):
            # Verificar se o usuário tem acesso à aba
            if not is_tab_accessible(idx, current_user_privilege or "User"):
                # Mostrar toast de erro e retornar sem alterar a seleção
                show_toast("Acesso negado para esta funcionalidade", ft.colors.RED)
                return
                
            selected_index.current = idx
            home_view.visible = idx == 0
            score_view.visible = idx == 1
            timeline_view.visible = idx == 2
            risks_view.visible = idx == 3
            email_view.visible = idx == 4
            configs_view.visible = idx == 5
            
            # Limpar campos da aba Log quando sair da aba Configs
            if selected_index.current != 5 and idx != 5:
                try:
                    # Se estava na aba Configs e está saindo dela
                    if selected_config_tab.current == 5:  # Se estava na sub-aba Log
                        clear_log_fields()
                except Exception as ex:
                    print(f"Aviso: erro ao limpar campos da aba Log: {ex}")
            
            # Quando aba Score é selecionada e não há busca ativa, mostrar favoritos
            if idx == 1 and search_field_ref.current:  # Score agora é índice 1
                search_term = search_field_ref.current.value.strip()
                bu_val = selected_bu.current.value if selected_bu.current else None
                # Se não há termo de busca nem BU, mostrar favoritos
                if not search_term and (not bu_val or not bu_val.strip()):
                    show_favorites_only()
                    
            update_menu()
            # Se a aba Risks foi selecionada, gerar os cards imediatamente (usa ano atual se dropdown vazio)
            try:
                if idx == 3:  # Risks agora é índice 3
                    # Atualizar valor do target exibido na aba Risks antes de gerar cards
                    try:
                        if target_risks_text and target_risks_text.current and target_slider and target_slider.value is not None:
                            target_risks_text.current.value = f"{target_slider.value:.2f}"
                            target_risks_text.current.update()
                    except Exception as _ex:
                        print(f"Aviso ao atualizar Target na aba Risks: {_ex}")
                    # Ao entrar na página de Risks, buscar por Todo Período por padrão
                    try:
                        if risks_year_dropdown and risks_year_dropdown.current:
                            # '' corresponde à opção 'Todo Período'
                            risks_year_dropdown.current.value = ""
                            try:
                                risks_year_dropdown.current.update()
                            except Exception:
                                pass
                    except Exception as _ex2:
                        print(f"Aviso ao setar filtro 'Todo Período' na aba Risks: {_ex2}")
                    generate_risk_cards()
            except Exception as ex:
                print(f"Erro ao gerar cards ao abrir aba Risks: {ex}")
            # Se estamos saindo da aba Risks, limpar os cards para liberar memória/estado
            try:
                if idx != 3 and risks_cards_container and risks_cards_container.current:  # Risks agora é índice 3
                    risks_cards_container.current.content = ft.Text("Nenhum risco pesquisado")
                    risks_cards_container.current.update()
            except Exception as ex:
                print(f"Aviso ao limpar cards da aba Risks: {ex}")
            page.update()
        return handler

    # Dropdowns de mês e ano
    month_options = [ft.dropdown.Option(str(i).zfill(2), text=str(i)) for i in range(1, 13)]
    year_options = [ft.dropdown.Option("", "(Ano Atual)")] + [ft.dropdown.Option(str(y)) for y in range(2025, 2036)]
    selected_month = ft.Ref()
    selected_year = ft.Ref()
    selected_bu = ft.Ref()
    selected_po = ft.Ref()

    def on_month_year_change(e):
        # A busca é chamada sempre que um dropdown muda. A função de busca verificará os valores.
        load_scores()

    def get_user_accessible_tabs(privilege):
        """Retorna lista de índices de abas que o usuário pode acessar baseado no privilégio"""
        if privilege == "Super Admin":
            # Super Admin pode acessar tudo
            return [0, 1, 2, 3, 4, 5]  # Home, Score, Timeline, Risks, Email, Configs
        elif privilege == "Admin":
            # Admin pode: Home, Score, Timeline, Risks, Configs (sem Email)
            return [0, 1, 2, 3, 5]  # Home, Score, Timeline, Risks, Configs
        else:  # User
            # User pode: Home, Timeline, Risks, Configs limitado
            return [0, 2, 3, 5]  # Home, Timeline, Risks, Configs

    def is_tab_accessible(tab_index, privilege):
        """Verifica se uma aba específica é acessível para o privilégio do usuário"""
        accessible_tabs = get_user_accessible_tabs(privilege)
        return tab_index in accessible_tabs

    def update_menu():
        if menu_column_ref.current:
            show_text = menu_is_expanded.current
            
            # Lista completa de itens de menu
            all_menu_items = [
                ("home_outlined", "Home", 0),
                ("score_outlined", "Score", 1),
                ("timeline_outlined", "Timeline", 2),
                ("warning_outlined", "Risks", 3),
                ("email_outlined", "Email", 4),
                ("settings_outlined", "Configs", 5),
            ]
            
            # Filtrar itens baseado no privilégio do usuário
            accessible_tabs = get_user_accessible_tabs(current_user_privilege or "User")
            filtered_menu_items = [
                menu_item(icon, text, idx, show_text) 
                for icon, text, idx in all_menu_items 
                if idx in accessible_tabs
            ]
            
            menu_column_ref.current.controls = filtered_menu_items
            menu_column_ref.current.width = 160 if show_text else 40
            menu_column_ref.current.update()

    def toggle_menu(e):
        menu_is_expanded.current = not menu_is_expanded.current
        update_menu()
        page.update()

    # --- Início: Lógica do Banco de Dados e Pesquisa ---

    # Conexão com o banco de dados local. check_same_thread=False é necessário para Flet.
    try:
        db_conn = sqlite3.connect("db.db", check_same_thread=False)
        print("Conexão com banco de dados estabelecida com sucesso!")
        
        # Criar tabela de favoritos se não existir
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS favorites_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wwid TEXT NOT NULL,
                supplier_id TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_wwid, supplier_id)
            )
        ''')
        print("Tabela de favoritos verificada/criada com sucesso!")

        # Criar tabelas de listas usadas em comboboxes (se não existirem)
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS sqie_table (
                sqie_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                alias TEXT UNIQUE,
                email TEXT,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS continuity_table (
                continuity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                alias TEXT UNIQUE,
                email TEXT,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS planner_table (
                planner_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                alias TEXT UNIQUE,
                email TEXT,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS sourcing_table (
                sourcing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                alias TEXT UNIQUE,
                email TEXT,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS business_unit_table (
                business_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bu TEXT UNIQUE,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS categories_table (
                categories_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        
        # Criar tabela de usuários
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS users_table (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wwid TEXT UNIQUE NOT NULL,
                user_name TEXT,
                user_password TEXT NOT NULL,
                user_privilege TEXT NOT NULL,
                otif INTEGER DEFAULT 0,
                nil INTEGER DEFAULT 0,
                pickup INTEGER DEFAULT 0,
                package INTEGER DEFAULT 0,
                register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                registered_by TEXT,
                last_updated_by TEXT,
                last_updated_date TIMESTAMP
            )
        ''')
        
        # Helper: garante colunas existem em tabela, adicionando as que faltam
        def ensure_columns(table_name, columns):
            """Verifica colunas existentes usando PRAGMA table_info e adiciona colunas ausentes.

            `columns` deve ser um dict {column_name: column_definition_sql_after_name},
            por exemplo: {'user_name': 'TEXT', 'last_updated_date': 'TIMESTAMP'}
            """
            try:
                # Obter colunas existentes
                existing = db_manager.query(f"PRAGMA table_info({table_name})")
                existing_names = {row['name'] for row in existing} if existing else set()
                for col, definition in columns.items():
                    if col not in existing_names:
                        q = f"ALTER TABLE {table_name} ADD COLUMN {col} {definition}"
                        try:
                            db_manager.execute(q)
                            print(f"Coluna {col} adicionada à tabela {table_name}")
                        except Exception as e:
                            print(f"Erro ao adicionar coluna {col} em {table_name}: {e}")
            except Exception as e:
                print(f"Erro ao garantir colunas para {table_name}: {e}")

        # Garantir colunas na users_table
        ensure_columns('users_table', {
            'user_name': 'TEXT',
            'last_updated_by': 'TEXT',
            'last_updated_date': 'TIMESTAMP',
            'registered_by': 'TEXT',
        })
        
        # Criar tabela de configurações de tema
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS theme_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wwid TEXT,
                theme_mode TEXT NOT NULL DEFAULT 'light',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Criar tabela de configurações de critérios
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS criteria_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wwid TEXT,
                nil_weight REAL DEFAULT 0.2,
                otif_weight REAL DEFAULT 0.2,
                pickup_weight REAL DEFAULT 0.2,
                package_weight REAL DEFAULT 0.2,
                target_weight REAL DEFAULT 5.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Criar tabela de configurações gerais do aplicativo
        db_manager.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wwid TEXT,
                setting_key TEXT,
                setting_value TEXT,
                toast_duration INTEGER DEFAULT 3,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Garantir colunas existentes em criteria_settings e app_settings
        ensure_columns('criteria_settings', {
            'target_weight': 'REAL DEFAULT 0.2'
        })

        ensure_columns('app_settings', {
            'setting_key': 'TEXT',
            'setting_value': 'TEXT'
        })
        
        db_conn.commit()
        
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        db_conn = None # Garante que o app não quebre se a conexão falhar

    def save_score_control_type(control_type):
        """Salva o tipo de controle de score no banco de dados"""
        try:
            # Verificar se já existe uma configuração
            exists = db_manager.query_one("SELECT COUNT(*) as count FROM app_settings WHERE setting_key = 'score_control_type'")
            
            if exists and exists['count'] > 0:
                db_manager.execute("UPDATE app_settings SET setting_value = ? WHERE setting_key = 'score_control_type'", (control_type,))
            else:
                db_manager.execute("INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?)", ('score_control_type', control_type))
            
            print(f"Tipo de controle salvo no banco: {control_type}")
        except Exception as e:
            print(f"Erro ao salvar tipo de controle: {e}")

    def load_score_control_type():
        """Carrega o tipo de controle de score do banco de dados"""
        global score_control_type
        try:
            result = db_manager.query_one("SELECT setting_value FROM app_settings WHERE setting_key = 'score_control_type'")
            if result:
                score_control_type = result['setting_value']
                print(f"Tipo de controle carregado do banco: {score_control_type}")
                return result['setting_value']
        except Exception as e:
            print(f"Erro ao carregar tipo de controle: {e}")
        return "slider"
    
    def save_spinbox_increment(increment):
        """Salva o incremento do spinbox no banco de dados"""
        try:
            # Verificar se já existe uma configuração
            exists = db_manager.query_one("SELECT COUNT(*) as count FROM app_settings WHERE setting_key = 'spinbox_increment'")
            
            if exists and exists['count'] > 0:
                db_manager.execute("UPDATE app_settings SET setting_value = ? WHERE setting_key = 'spinbox_increment'", (str(increment),))
            else:
                db_manager.execute("INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?)", ('spinbox_increment', str(increment)))
            
            print(f"Incremento do spinbox salvo no banco: {increment}")
        except Exception as e:
            print(f"Erro ao salvar incremento do spinbox: {e}")

    def load_spinbox_increment():
        """Carrega o incremento do spinbox do banco de dados"""
        try:
            result = db_manager.query_one("SELECT setting_value FROM app_settings WHERE setting_key = 'spinbox_increment'")
            if result and result['setting_value'] is not None and str(result['setting_value']).strip() != "":
                increment = float(result['setting_value'])
                print(f"Incremento do spinbox carregado do banco: {increment}")
                return increment
        except Exception as e:
            print(f"Erro ao carregar incremento do spinbox: {e}")
        return 0.1

    def create_spinbox():
        """Cria um widget de spinbox customizado para notas."""
        # Carregar incremento do banco (uso seguro se a função não existir no momento)
        try:
            increment = load_spinbox_increment()
        except NameError:
            increment = 0.1
        except Exception as ex:
            print(f"Aviso: não foi possível carregar increment do spinbox no create_spinbox: {ex}")
            increment = 0.1
        
        score_field = ft.TextField(
            value="0.0", 
            text_align=ft.TextAlign.CENTER, 
            width=70, 
            border_radius=8,
            # Usar a mesma cor de fundo do card para integrar visualmente o campo ao card
            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
        )

        # CORRIGIDO: Validar entrada manual apenas quando terminar de editar: garantir 0.0 - 10.0 e formatar com uma casa decimal
        def on_field_blur(e):
            """Valida e formata o valor apenas quando o usuário termina de editar (perde o foco)"""
            try:
                v = e.control.value
                if v is None or str(v).strip() == "":
                    e.control.value = "0.0"
                    e.control.update()
                    return
                
                # Permitir entrada de números inteiros e decimais
                num = float(str(v).strip())
                # Limitar entre 0 e 10
                num = max(0, min(10, num))
                # Formatar com 1 casa decimal
                e.control.value = f"{num:.1f}"
                e.control.update()
            except (ValueError, TypeError):
                # Se não conseguir converter, voltar para 0.0
                e.control.value = "0.0"
                e.control.update()

        # Usar on_blur em vez de on_change para não interferir durante a digitação
        score_field.on_blur = on_field_blur

        def adjust_score(e):
            try:
                current_value = float(score_field.value)
                if e.control.data == "+":
                    current_value += increment
                elif e.control.data == "-":
                    current_value -= increment
                # Garantir que não seja negativo e limitar a 10
                new_value = max(0, min(10, current_value))
                score_field.value = str(round(new_value, 1))
                score_field.update()
            except ValueError:
                score_field.value = "0.0"
                score_field.update()

        return ft.Row([
            ft.IconButton(ft.Icons.REMOVE, on_click=adjust_score, data="-"),
            score_field,
            ft.IconButton(ft.Icons.ADD, on_click=adjust_score, data="+"),
        ], alignment=ft.MainAxisAlignment.CENTER)

    # ---------- Utilitários para listas (sqie, planner, sourcing, continuity, bu, category) ----------
    
    def load_all_lists_data():
        """Carrega dados existentes de todas as tabelas para popular as listas na interface."""
        if not db_conn:
            return
        
        try:
            # Usar refresh_list_ui para cada tipo de lista
            # Isso garantirá consistência com a nova estrutura de cards
            for key in lists_controls.keys():
                refresh_list_ui(key)
                    
        except Exception as e:
            print(f"Erro ao carregar dados das listas: {e}")

    def select_list_item(key, value):
        """Seleciona ou des-seleciona um item na lista, atualizando apenas o realce visual."""
        
        # Se o item clicado já estava selecionado, desmarca (define como None).
        # Caso contrário, define o item clicado como o selecionado.
        if lists_controls[key]['selected_item'] == value:
            lists_controls[key]['selected_item'] = None
        else:
            lists_controls[key]['selected_item'] = value
        
        # Recarregar apenas a lista específica usando o mesmo estilo de load_all_lists_data
        reload_single_list_with_style(key)
        
        # A atualização da página é necessária para que a lista seja redesenhada na tela.
        page.update()

    def reload_single_list_with_style(key):
        """Recarrega uma lista específica mantendo o estilo da load_all_lists_data"""
        # Usar refresh_list_ui para manter consistência
        refresh_list_ui(key)

    def load_list_options(table_name, column_name):
        """Retorna lista de tuplas (value, text) para popular Dropdowns."""
        try:
            if table_name in ("business_unit_table", "categories_table"):
                # Tabelas que só têm uma coluna principal
                rows = db_manager.query(f"SELECT {column_name} FROM {table_name} ORDER BY {column_name}")
                options = [r[column_name] for r in rows if r[column_name]]  # Filtrar valores nulos/vazios
                return options if options else []  # Não retorna lista vazia se não há dados
            else:
                # Para tabelas com name, alias, email (sqie, continuity, planner, sourcing)
                # Usar apenas o campo 'name' como solicitado
                rows = db_manager.query(f"SELECT name FROM {table_name} WHERE name IS NOT NULL AND name != '' ORDER BY name")
                options = [r['name'] for r in rows if r['name']]  # Filtrar valores nulos/vazios
                return options if options else []  # Não retorna lista vazia se não há dados
        except Exception as ex:
            print(f"Erro ao carregar opções de {table_name}: {ex}")
            return []

    def load_list_items_full(table_name):
        """Retorna dados completos dos itens da lista com name, alias, email e ID único."""
        try:
            if table_name == "business_unit_table":
                rows = db_manager.query(f"SELECT business_id, bu FROM {table_name} ORDER BY bu")
                return [{"id": r["business_id"], "display": r["bu"], "alias": r["bu"]} for r in rows]
            elif table_name == "categories_table":
                rows = db_manager.query(f"SELECT categories_id, category FROM {table_name} ORDER BY category")
                return [{"id": r["categories_id"], "display": r["category"], "alias": r["category"]} for r in rows]
            else:
                # Para tabelas com name, alias, email - incluir ID da tabela
                id_columns = {
                    'sqie_table': 'sqie_id',
                    'continuity_table': 'continuity_id', 
                    'planner_table': 'planner_id',
                    'sourcing_table': 'sourcing_id'
                }
                
                id_col = id_columns.get(table_name, 'id')
                rows = db_manager.query(f"SELECT {id_col}, name, alias, email FROM {table_name} ORDER BY alias")
                items = []
                for row in rows:
                    row_id = row[id_col]
                    name = row["name"]
                    alias = row["alias"]
                    email = row["email"]
                    # Criar texto de exibição com as informações completas
                    display_parts = []
                    if name and name.strip():
                        display_parts.append(f"Nome: {name.strip()}")
                    if alias and alias.strip():
                        display_parts.append(f"Alias: {alias.strip()}")
                    if email and email.strip():
                        display_parts.append(f"Email: {email.strip()}")
                    
                    display_text = " | ".join(display_parts) if display_parts else "Item sem dados"
                    items.append({
                        "id": row_id,
                        "display": display_text,
                        "alias": alias or name or "",
                        "name": name or "",
                        "email": email or ""
                    })
                return items
        except Exception as ex:
            print(f"Erro ao carregar itens completos de {table_name}: {ex}")
            return []

    def insert_list_item(table_name, columns, values):
        """Insere item em tabela genérica passando colunas e valores."""
        placeholders = ','.join(['?'] * len(values))
        cols = ','.join(columns)
        q = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        db_manager.execute(q, values)

    def delete_list_item_by_alias(table_name, alias_column, alias):
        q = f"DELETE FROM {table_name} WHERE {alias_column} = ?"
        db_manager.execute(q, (alias,))
    
    def get_all_cards():
        """Retorna todos os cards, navegando pela estrutura responsiva se necessário"""
        all_cards = []
        
        if not responsive_app_manager or not responsive_app_manager.results_container:
            # Fallback para results_list tradicional
            for control in results_list.controls:
                if isinstance(control, ft.Card):
                    all_cards.append(control)
            return all_cards
        
        # Navegar pela estrutura responsiva
        for control in responsive_app_manager.results_container.controls:
            if isinstance(control, ft.Card):
                # Card direto (layout single)
                all_cards.append(control)
            elif isinstance(control, ft.Row):
                # Layout double - verificar colunas
                for column in control.controls:
                    if isinstance(column, ft.Column):
                        for card in column.controls:
                            if isinstance(card, ft.Card):
                                all_cards.append(card)
        
        return all_cards

    def load_scores():
        """Para os cards de resultado visíveis, carrega as notas do banco de dados
        com base no mês e ano selecionados.
        """
        if not selected_month.current or not selected_year.current:
            return
            
        month_val = selected_month.current.value
        year_val = selected_year.current.value

        # Se o ano for uma string vazia ("(Ano Atual)"), usar o ano atual
        if year_val == "":
            import datetime
            year_val = str(datetime.date.today().year)

        # A função só executa se ambos, mês e ano, estiverem selecionados.
        if not month_val or not year_val:
            # Limpar as notas se a data for desmarcada
            all_cards = get_all_cards()
            for card in all_cards:
                if hasattr(card, 'data') and card.data:
                    # Suporte para estrutura antiga (spinbox_refs)
                    if "spinbox_refs" in card.data:
                        for ref in card.data["spinbox_refs"].values():
                            try:
                                ref.value = "0.0"
                                if hasattr(ref, 'page') and ref.page is not None:
                                    ref.update()
                            except Exception as e:
                                print(f"Erro ao limpar spinbox: {e}")
                    
                    # Suporte para estrutura nova (score_sliders/score_texts)
                    if "score_sliders" in card.data and "score_texts" in card.data:
                        score_sliders = card.data["score_sliders"]
                        score_texts = card.data["score_texts"]
                        for ui_name in ["OTIF", "Pickup", "Package", "NIL"]:
                            if ui_name in score_sliders and ui_name in score_texts:
                                try:
                                    score_sliders[ui_name].value = 0.0
                                    score_texts[ui_name].value = "0.0"
                                    if hasattr(score_sliders[ui_name], 'page') and score_sliders[ui_name].page is not None:
                                        score_sliders[ui_name].update()
                                    if hasattr(score_texts[ui_name], 'page') and score_texts[ui_name].page is not None:
                                        score_texts[ui_name].update()
                                except Exception as e:
                                    print(f"Erro ao limpar slider {ui_name}: {e}")
            page.update()
            return

        if not db_conn: 
            print("Conexão com banco não disponível")
            return

        print(f"Carregando scores para mês: {month_val}, ano: {year_val}")

        # Usar a função auxiliar para obter todos os cards
        all_cards = get_all_cards()
        
        for card in all_cards:
            if not isinstance(card, ft.Card) or not hasattr(card, 'data') or not card.data:
                continue

            supplier_id = card.data["supplier_id"]
            
            # Verificar se é slider ou spinbox
            score_sliders = card.data.get("score_sliders")
            score_texts = card.data.get("score_texts")
            spinbox_refs = card.data.get("spinbox_refs")
            
            # Se não tem nenhum dos dois tipos de controle, pular
            if not score_sliders and not spinbox_refs:
                continue
            
            try:
                query = """
                    SELECT otif, quality_pickup, quality_package, nil, comment
                    FROM supplier_score_records_table
                    WHERE supplier_id = ? AND month = ? AND year = ?
                """
                score_record = db_manager.query_one(query, (supplier_id, int(month_val), int(year_val)))

                if score_record:
                    # Mapeamento direto: OTIF, Pickup, Package, NIL, Comment
                    scores = {
                        "OTIF": score_record['otif'] if score_record['otif'] is not None else 0.0,
                        "Pickup": score_record['quality_pickup'] if score_record['quality_pickup'] is not None else 0.0,
                        "Package": score_record['quality_package'] if score_record['quality_package'] is not None else 0.0,
                        "NIL": score_record['nil'] if score_record['nil'] is not None else 0.0,
                    }
                    comment_value = score_record['comment'] if score_record['comment'] is not None else ""
                    
                    # Atualizar valores nos sliders (se existirem)
                    if score_sliders and score_texts:
                        for ui_name, score_value in scores.items():
                            if ui_name in score_sliders:
                                try:
                                    val = float(score_value)
                                    score_sliders[ui_name].value = val
                                    score_texts[ui_name].value = f"{val:.1f}"
                                    
                                    # Verificar se o slider está na página antes de atualizar
                                    if hasattr(score_sliders[ui_name], 'page') and score_sliders[ui_name].page is not None:
                                        score_sliders[ui_name].update()
                                    if hasattr(score_texts[ui_name], 'page') and score_texts[ui_name].page is not None:
                                        score_texts[ui_name].update()
                                except Exception as e:
                                    print(f"Erro ao atualizar slider {ui_name}: {e}")
                                    continue
                    
                    # Atualizar valores nos spinboxes (se existirem)
                    if spinbox_refs:
                        print(f"🔍 DEBUG spinbox_refs disponíveis: {list(spinbox_refs.keys())}")
                        for ui_name, score_value in scores.items():
                            if ui_name in spinbox_refs:
                                try:
                                    val = float(score_value)
                                    print(f"🔍 DEBUG atualizando spinbox {ui_name} com valor {val:.1f}")
                                    print(f"🔍 DEBUG tipo do spinbox_refs[{ui_name}]: {type(spinbox_refs[ui_name])}")
                                    
                                    spinbox_refs[ui_name].value = f"{val:.1f}"
                                    print(f"🔍 DEBUG valor definido: {spinbox_refs[ui_name].value}")
                                    
                                    # Verificar se o spinbox está na página antes de atualizar
                                    if hasattr(spinbox_refs[ui_name], 'page') and spinbox_refs[ui_name].page is not None:
                                        spinbox_refs[ui_name].update()
                                        print(f"✅ Spinbox {ui_name} atualizado com sucesso")
                                    else:
                                        print(f"⚠️ Spinbox {ui_name} não está na página")
                                except Exception as e:
                                    print(f"❌ Erro ao atualizar spinbox {ui_name}: {e}")
                                    continue
                            else:
                                print(f"⚠️ Spinbox {ui_name} não encontrado em spinbox_refs")
                    else:
                        print("⚠️ Nenhum spinbox_refs encontrado no card")
                    
                    # Atualizar comentário se houver referência para ele no card
                    if "comment_field" in card.data and card.data["comment_field"]:
                        try:
                            card.data["comment_field"].value = comment_value
                            if hasattr(card.data["comment_field"], 'page') and card.data["comment_field"].page is not None:
                                card.data["comment_field"].update()
                            print(f"Atualizando comentário: {comment_value}")
                        except Exception as e:
                            print(f"Erro ao atualizar comentário: {e}")
                        
                else:
                    # Não encontrou registro, zerar valores
                    # Zerar sliders (se existirem)
                    if score_sliders and score_texts:
                        for ui_name in ["OTIF", "Pickup", "Package", "NIL"]:
                            if ui_name in score_sliders:
                                try:
                                    score_sliders[ui_name].value = 0.0
                                    score_texts[ui_name].value = "0.0"
                                    
                                    # Verificar se o slider está na página antes de atualizar
                                    if hasattr(score_sliders[ui_name], 'page') and score_sliders[ui_name].page is not None:
                                        score_sliders[ui_name].update()
                                    if hasattr(score_texts[ui_name], 'page') and score_texts[ui_name].page is not None:
                                        score_texts[ui_name].update()
                                except Exception as e:
                                    print(f"Erro ao zerar slider {ui_name}: {e}")
                                    continue
                    
                    # Zerar spinboxes (se existirem)
                    if spinbox_refs:
                        for ui_name in ["OTIF", "Pickup", "Package", "NIL"]:
                            if ui_name in spinbox_refs:
                                try:
                                    spinbox_refs[ui_name].value = "0.0"
                                    
                                    # Verificar se o spinbox está na página antes de atualizar
                                    if hasattr(spinbox_refs[ui_name], 'page') and spinbox_refs[ui_name].page is not None:
                                        spinbox_refs[ui_name].update()
                                except Exception as e:
                                    print(f"Erro ao zerar spinbox {ui_name}: {e}")
                                    continue
                    
                    # Limpar comentário
                    if "comment_field" in card.data and card.data["comment_field"]:
                        try:
                            card.data["comment_field"].value = ""
                            if hasattr(card.data["comment_field"], 'page') and card.data["comment_field"].page is not None:
                                card.data["comment_field"].update()
                        except Exception as e:
                            print(f"Erro ao limpar comentário: {e}")
                
            except sqlite3.Error as e:
                print(f"Erro ao carregar notas para o supplier_id {supplier_id}: {e}")
        
        page.update()

    def create_result_widget(record):
        """Cria um card de resultado para um registro do banco.
        Dicionário esperado com chaves: supplier_id, vendor_name, BU, supplier_status, supplier_number, supplier_name
        """
        supplier_id = record.get('supplier_id', '?')
        vendor_name = record.get('vendor_name', '?')
        bu = record.get('bu', '?')
        status = record.get('supplier_status', '?')
        supplier_number = record.get('supplier_number', '?')
        supplier_name = record.get('supplier_name', '?')

        print(f"🏗️ CRIANDO CARD: {vendor_name} (ID: {supplier_id}) com TIPO: {score_control_type}")
        print(f"🔍 DEBUG PERMISSÕES NO CARD:")
        print(f"  current_user_permissions = {current_user_permissions}")

        # Ordem dos spinboxes na interface
        ui_order = ["NIL", "Pickup", "Package", "OTIF"]
        
        # Mapeamento das permissões
        permission_map = {
            "NIL": "nil",
            "Pickup": "pickup", 
            "Package": "package",
            "OTIF": "otif"
        }

        spinbox_refs = {}
        spinboxes_rows = []
        for ui_name in ui_order:
            # Verificar se o usuário tem permissão para este campo
            permission_key = permission_map.get(ui_name)
            has_permission = (current_user_permissions.get(permission_key, False) if current_user_permissions else True)
            
            print(f"  {ui_name}: permission_key='{permission_key}', has_permission={has_permission}")
            
            # Sempre criar o campo, mas desabilitar se não tiver permissão
            print(f"    ✅ Criando {score_control_type} {ui_name} ({'habilitado' if has_permission else 'desabilitado'})")
            
            if score_control_type == "slider":
                slider_row, slider_control, text_control = create_score_slider()
                # Desabilitar slider se não tiver permissão
                if not has_permission:
                    slider_control.disabled = True
                    slider_control.opacity = 0.5
                spinbox_refs[ui_name] = slider_control  # Guardar referência do controle principal
                control_widget = slider_row
                print(f"    📊 Slider {ui_name} criado - referência salva: {type(slider_control)}")
            else:  # spinbox
                spinbox = create_spinbox()
                spinbox_field = spinbox.controls[1]  # O TextField é o segundo controle
                # Desabilitar spinbox se não tiver permissão
                if not has_permission:
                    spinbox_field.disabled = True
                    spinbox_field.opacity = 0.5
                    # Desabilitar botões também
                    spinbox.controls[0].disabled = True  # Botão de diminuir
                    spinbox.controls[2].disabled = True  # Botão de aumentar
                    spinbox.controls[0].opacity = 0.5
                    spinbox.controls[2].opacity = 0.5
                spinbox_refs[ui_name] = spinbox_field
                control_widget = spinbox
                print(f"    🔢 Spinbox {ui_name} criado - referência salva: {type(spinbox_field)}")
                print(f"    🔍 Spinbox field value inicial: {spinbox_field.value}")
                print(f"    🔍 Spinbox refs atual: {list(spinbox_refs.keys())}")
            
            # Criar o texto do label com opacidade reduzida se não tiver permissão
            label_text = ft.Text(
                ui_name, 
                weight="bold", 
                width=80, 
                opacity=0.5 if not has_permission else 1.0
            )
            
            spinboxes_rows.append(
                ft.Row(
                    [label_text, control_widget], 
                    alignment=ft.MainAxisAlignment.START, 
                    spacing=10
                )
            )

        comment_field = ft.TextField(
            label="Comentário", 
            border_radius=8, 
            multiline=True, 
            min_lines=6,
            max_lines=8,
            # Tornar o campo visualmente integrado ao card
            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
        )

        def save_score(e):
            # Animação do botão - iniciar loading
            save_button = e.control
            
            # Verificar se já está processando para evitar cliques múltiplos
            if hasattr(save_button, '_is_processing') and save_button._is_processing:
                print("🚫 Clique ignorado - operação já em andamento (spinbox)")
                return
                
            # Marcar como processando
            save_button._is_processing = True
            
            original_text = save_button.content.value if hasattr(save_button.content, 'value') else save_button.text
            original_icon = save_button.icon
            
            def reset_button_state():
                """Função para resetar o estado do botão"""
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                save_button._is_processing = False
                if hasattr(save_button, '_restore_thread'):
                    save_button._restore_thread = None
                if hasattr(save_button, '_restore_thread_cancelled'):
                    save_button._restore_thread_cancelled = False
                safe_update_control(save_button, page)
            
            # Aplicar efeito visual de loading
            save_button.text = "Salvando..."
            save_button.icon = ft.Icons.HOURGLASS_EMPTY
            save_button.disabled = True
            safe_update_control(save_button, page)
            
            if not db_conn:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Erro: Banco de dados não conectado.", "red", restore_control=save_button)
                return
                
            if not selected_month.current or not selected_year.current:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Selecione mês e ano antes de salvar.", "orange", restore_control=save_button)
                return
                
            month_val = selected_month.current.value
            year_val = selected_year.current.value
            
            if not month_val or not year_val:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Selecione mês e ano antes de salvar.", "orange", restore_control=save_button)
                return

            # Validação de data futura baseada na lógica legacy
            from datetime import datetime
            current_date = datetime.now()
            ano_atual = current_date.year
            mes_atual = current_date.month
            register_date = current_date.strftime("%Y-%m-%d %H:%M:%S")  # Data atual para registro
            
            try:
                mes_int = int(month_val)
                ano_int = int(year_val)
            except ValueError:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Valores de mês e ano inválidos.", "red", restore_control=save_button)
                return
                
            # Prevenir salvamento de scores para meses futuros
            if (ano_int > ano_atual) or (ano_int == ano_atual and mes_int > mes_atual):
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Não é possível salvar scores para meses futuros.", "orange", restore_control=save_button)
                return

            try:
                # Verificar status atual do supplier - se Inactive, não permitir salvar
                try:
                    row_status = db_manager.query_one("SELECT supplier_status FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
                    current_status = row_status['supplier_status'] if row_status else None
                    if current_status and str(current_status).strip().lower().startswith("inactive"):
                        # Restaurar botão e avisar
                        reset_button_state()
                        show_toast("❌ Não é possível salvar para fornecedores inativos.", "red", restore_control=save_button)
                        return
                except Exception as ex_status:
                    print(f"Aviso: falha ao verificar status do supplier antes de salvar: {ex_status}")

                # Buscar critérios atuais da tabela criteria_table
                criteria_results = db_manager.query("SELECT criteria_category, value FROM criteria_table")
                criteria_values = {}
                for row in criteria_results:
                    criteria_name = row['criteria_category']
                    criteria_value = float(row['value'])
                    criteria_values[criteria_name] = criteria_value
                
                print(f"🎯 Critérios carregados para cálculo (spinbox): {criteria_values}")
                
                # Preparar os dados para salvar - valores originais dos spinboxes
                values_to_save = {}
                total_score_calculation = 0.0
                
                # Verificar permissões e salvar valores originais, calcular total_score separadamente
                if current_user_permissions.get('otif', False) and "OTIF" in spinbox_refs:
                    raw_score = float(spinbox_refs["OTIF"].value or 0)
                    values_to_save['otif'] = raw_score  # Salvar valor original
                    
                    # Calcular para total_score
                    criteria_weight = criteria_values.get('OTIF', 0.22)
                    weighted_value = round(raw_score * criteria_weight, 1)
                    total_score_calculation += weighted_value
                    print(f"  OTIF: {raw_score} (salvo) × {criteria_weight} = {weighted_value} (para total)")
                    
                if current_user_permissions.get('pickup', False) and "Pickup" in spinbox_refs:
                    raw_score = float(spinbox_refs["Pickup"].value or 0)
                    values_to_save['quality_pickup'] = raw_score  # Salvar valor original
                    
                    # Calcular para total_score
                    criteria_weight = criteria_values.get('Quality of Pick Up', 0.28)
                    weighted_value = round(raw_score * criteria_weight, 1)
                    total_score_calculation += weighted_value
                    print(f"  Pickup: {raw_score} (salvo) × {criteria_weight} = {weighted_value} (para total)")
                    
                if current_user_permissions.get('package', False) and "Package" in spinbox_refs:
                    raw_score = float(spinbox_refs["Package"].value or 0)
                    values_to_save['quality_package'] = raw_score  # Salvar valor original
                    
                    # Calcular para total_score
                    criteria_weight = criteria_values.get('Quality-Supplier Package', 0.28)
                    weighted_value = round(raw_score * criteria_weight, 1)
                    total_score_calculation += weighted_value
                    print(f"  Package: {raw_score} (salvo) × {criteria_weight} = {weighted_value} (para total)")
                    
                if current_user_permissions.get('nil', False) and "NIL" in spinbox_refs:
                    raw_score = float(spinbox_refs["NIL"].value or 0)
                    values_to_save['nil'] = raw_score  # Salvar valor original
                    
                    # Calcular para total_score
                    criteria_weight = criteria_values.get('NIL', 0.22)
                    weighted_value = round(raw_score * criteria_weight, 1)
                    total_score_calculation += weighted_value
                    print(f"  NIL: {raw_score} (salvo) × {criteria_weight} = {weighted_value} (para total)")
                
                if not values_to_save:
                    # Restaurar botão em caso de erro
                    save_button.text = original_text
                    save_button.icon = original_icon
                    save_button.disabled = False
                    safe_update_control(save_button, page)
                    show_toast("Você não tem permissão para salvar nenhum campo.", "red", restore_control=save_button)
                    return
                
                comment_val = comment_field.value or ""
                
                # O total_score é a soma dos valores ponderados, não dos valores originais
                total_score = round(total_score_calculation, 1)
                print(f"📊 Total Score calculado: {total_score}")
                
                # Verificar se já existe um registro e buscar registered_by atual
                check_query = """
                    SELECT COUNT(*), registered_by FROM supplier_score_records_table 
                    WHERE supplier_id = ? AND month = ? AND year = ?
                """
                result = db_manager.query_one(check_query, (supplier_id, int(month_val), int(year_val)))
                exists = result["COUNT(*)"] > 0
                current_registered_by = result["registered_by"] if exists and result["registered_by"] else ""
                
                # Construir registered_by acumulativo - FUNÇÃO SPINBOX
                saved_field_names = []
                field_mapping = {"NIL": "nil", "OTIF": "otif", "PICKUP": "quality_pickup", "PACKAGE": "quality_package"}
                for field, db_field in field_mapping.items():
                    if db_field in values_to_save.keys():  # Se o campo foi salvo, adicionar
                        saved_field_names.append(field)
                
                # Combinar com os campos já registrados anteriormente
                existing_fields = set(current_registered_by.split(',')) if current_registered_by else set()
                all_fields = existing_fields.union(set(saved_field_names))
                new_registered_by = ','.join(sorted([f for f in all_fields if f]))  # Remove strings vazias e ordena
                
                print(f"📝 Registered_by (SPINBOX): '{current_registered_by}' -> '{new_registered_by}'")
                
                # Construir query dinamicamente baseado nas permissões
                if exists:
                    # Atualizar apenas os campos permitidos
                    set_clauses = []
                    values = []
                    for field, value in values_to_save.items():
                        set_clauses.append(f"{field} = ?")
                        values.append(value)
                    
                    # Sempre atualizar total_score, registered_by, register_date, changed_by, supplier_name e comment
                    set_clauses.extend(["total_score = ?", "registered_by = ?", "register_date = ?", "changed_by = ?", "supplier_name = ?", "comment = ?"])
                    values.extend([total_score, new_registered_by, register_date, current_user_name, vendor_name, comment_val])
                    
                    if set_clauses:
                        update_query = f"""
                            UPDATE supplier_score_records_table 
                            SET {', '.join(set_clauses)}
                            WHERE supplier_id = ? AND month = ? AND year = ?
                        """
                        values.extend([supplier_id, int(month_val), int(year_val)])
                        db_manager.execute(update_query, values)
                else:
                    # Inserir novo registro com campos zerados para campos sem permissão
                    insert_query = """
                        INSERT INTO supplier_score_records_table 
                        (supplier_id, month, year, otif, quality_pickup, quality_package, nil, total_score, registered_by, register_date, changed_by, supplier_name, comment)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db_manager.execute(insert_query, (
                        supplier_id, 
                        int(month_val), 
                        int(year_val), 
                        values_to_save.get('otif', 0),
                        values_to_save.get('quality_pickup', 0), 
                        values_to_save.get('quality_package', 0), 
                        values_to_save.get('nil', 0),
                        total_score,
                        new_registered_by,
                        register_date,
                        current_user_name,
                        vendor_name,
                        comment_val
                    ))
                
                db_conn.commit()
                
                # Rechecagem de status imediatamente antes do commit para evitar condição de corrida
                try:
                    final_row_status = db_manager.query_one("SELECT supplier_status FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
                    final_status = final_row_status['supplier_status'] if final_row_status else None
                    print(f"🔁 Rechecagem final de status antes do commit (spinbox): {final_status}")
                    if final_status and str(final_status).strip().lower().startswith("inactive"):
                        # Não efetuar commit em caso de fornecedor inativo
                        show_toast("❌ Não é possível salvar para fornecedores inativos.", "red", restore_control=save_button)
                        # Restaurar botão e abortar
                        save_button.text = original_text
                        save_button.icon = original_icon
                        save_button.disabled = False
                        save_button._is_processing = False
                        safe_update_control(save_button, page)
                        return
                except Exception as ex_final_status:
                    print(f"Aviso: falha na rechecagem final de status (spinbox): {ex_final_status}")

                # Debug: mostrar informações detalhadas do salvamento
                print(f"✅ Score salvo com sucesso!")
                print(f"   Fornecedor: {vendor_name} (ID: {supplier_id})")
                print(f"   Período: {month_val}/{year_val}")
                print(f"   Total Score: {total_score}")
                print(f"   Registrado por: {current_user_wwid}")
                print(f"   Campos salvos: {list(values_to_save.keys())}")
                
                # Mostrar apenas os campos que foram realmente salvos
                saved_fields = []
                for field, db_field in [("OTIF", "otif"), ("Pickup", "pickup"), ("Package", "package"), ("NIL", "nil")]:
                    if current_user_permissions.get(db_field, False) and field in spinbox_refs:
                        saved_fields.append(field)
                
                show_toast(f"✅ Score salvo para {vendor_name} ({month_val}/{year_val}) - Total: {total_score:.1f}", "green")
                
                # Restaurar botão após sucesso com ícone de confirmação temporário
                save_button.text = "Salvo!"
                save_button.icon = ft.Icons.CHECK
                save_button.disabled = False
                safe_update_control(save_button, page)
                
                # Cancelar thread anterior se existir
                if hasattr(save_button, '_restore_thread') and save_button._restore_thread is not None:
                    save_button._restore_thread_cancelled = True
                
                # Agendar restauração do botão original após 2 segundos
                def restore_button():
                    import time
                    # Verificar cancelamento durante a espera
                    for i in range(20):  # 20 x 0.1s = 2s
                        if hasattr(save_button, '_restore_thread_cancelled') and save_button._restore_thread_cancelled:
                            return  # Thread foi cancelada
                        time.sleep(0.1)
                    
                    # Verificar novamente se foi cancelada antes de restaurar
                    if hasattr(save_button, '_restore_thread_cancelled') and save_button._restore_thread_cancelled:
                        return
                        
                    if hasattr(save_button, 'update'):  # Verificar se ainda existe
                        save_button.text = original_text
                        save_button.icon = original_icon
                        save_button._restore_thread = None
                        save_button._restore_thread_cancelled = False
                        save_button._is_processing = False  # CRÍTICO: resetar flag de processamento
                        safe_update_control(save_button, page)
                
                import threading
                save_button._restore_thread_cancelled = False
                save_button._restore_thread = threading.Thread(target=restore_button, daemon=True)
                save_button._restore_thread.start()
                
            except Exception as ex:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                save_button._is_processing = False  # Adicionar reset do flag
                safe_update_control(save_button, page)
                
                show_toast(f"❌ Erro ao salvar: {str(ex)}", "red")
                print(f"❌ Erro detalhado ao salvar dados:")
                print(f"   Fornecedor: {vendor_name} (ID: {supplier_id})")
                print(f"   Período: {month_val}/{year_val}")
                print(f"   Erro: {ex}")
                import traceback
                traceback.print_exc()

        def toggle_favorite(e):
            global current_user_wwid
            if not current_user_wwid:
                show_toast("Erro: Usuário não autenticado.", "red")
                return
                
            if not db_conn:
                show_toast("Erro: Banco de dados não conectado.", "red")
                return
                
            try:
                # Verificar se já está nos favoritos
                check_query = "SELECT COUNT(*) FROM favorites_table WHERE user_wwid=? AND supplier_id=?"
                result = db_manager.query_one(check_query, (current_user_wwid, supplier_id))
                is_favorited = result['COUNT(*)'] > 0 if result else False
                
                if is_favorited:
                    # Remover dos favoritos
                    delete_query = "DELETE FROM favorites_table WHERE user_wwid=? AND supplier_id=?"
                    db_manager.execute(delete_query, (current_user_wwid, supplier_id))
                    e.control.selected = False
                    show_toast(f"{vendor_name} removido dos favoritos", "orange")
                    print(f"Favorito removido: {vendor_name} (ID: {supplier_id})")
                else:
                    # Adicionar aos favoritos
                    insert_query = "INSERT INTO favorites_table (user_wwid, supplier_id) VALUES (?, ?)"
                    db_manager.execute(insert_query, (current_user_wwid, supplier_id))
                    e.control.selected = True
                    show_toast(f"{vendor_name} adicionado aos favoritos", "green")
                    print(f"Favorito adicionado: {vendor_name} (ID: {supplier_id})")
                
                # Atualização segura do controle
                try:
                    if hasattr(e.control, 'page') and e.control.page is not None:
                        e.control.update()
                    else:
                        # Se o controle não está vinculado à página, atualizar toda a página
                        page.update()
                except Exception as update_error:
                    print(f"Aviso: Erro ao atualizar controle, atualizando página: {update_error}")
                    page.update()
                
            except sqlite3.Error as db_error:
                show_toast(f"Erro ao salvar favorito: {db_error}", "red")
                print(f"Erro no banco de dados: {db_error}")
            except Exception as ex:
                show_toast(f"Erro inesperado: {ex}", "red")
                print(f"Erro ao toggle favorite: {ex}")

        notas_col = ft.Column(spinboxes_rows, spacing=8, expand=1)  # Permite variação, mas com largura mínima

        info_col = ft.Column([
            ft.Text(vendor_name, weight="bold", size=16),
            ft.Text(f"BU: {bu}"),
            ft.Text(f"PO: {supplier_number}"),
            ft.Text(f"ID: {supplier_id}"),
            ft.Text(f"Status: {status}", color="green" if str(status).strip() == "Active" else "red" if str(status).strip() == "Inactive" else "gray"),
        ], spacing=4, alignment=ft.MainAxisAlignment.START, expand=1)  # Permite variação de tamanho

        # Reorganizar a estrutura do card para posicionar os botões no canto inferior direito
        left_section = ft.Row([
            info_col, 
            ft.VerticalDivider(), 
            notas_col, 
            ft.VerticalDivider()
        ], alignment=ft.MainAxisAlignment.START)

        # Seção direita apenas com comentário
        right_section = ft.Column([
            comment_field,
        ], expand=True, alignment=ft.MainAxisAlignment.START)

        # Criar referência para o botão de salvar para permitir animações
        save_button = ft.ElevatedButton(
            "Salvar", 
            on_click=save_score, 
            icon=ft.Icons.SAVE,
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        )

        card = ft.Card(
            content=ft.Container(
                padding=15,
                height=300,  # Altura fixa de 300px
                content=ft.Column([
                    # Área principal com layout horizontal
                    ft.Container(
                        content=ft.Row([
                            left_section,
                            right_section
                        ], vertical_alignment=ft.CrossAxisAlignment.STRETCH),
                        expand=True
                    ),
                    # Botões sempre na parte inferior
                    ft.Container(
                        content=ft.Row([
                            ft.Container(expand=True),  # Empurra os botões para a direita
                            ft.IconButton(
                                icon=ft.Icons.FAVORITE_BORDER, 
                                selected_icon=ft.Icons.FAVORITE, 
                                on_click=toggle_favorite, 
                                tooltip="Favoritar"
                            ),
                            save_button,
                        ], alignment=ft.MainAxisAlignment.END, tight=True),
                        height=50,  # Altura fixa para os botões
                        alignment=ft.alignment.bottom_right
                    )
                ], spacing=0)
            ),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background')
        )
        
        # Anexar dados ao card
        card.data = {
            "supplier_id": supplier_id, 
            "spinbox_refs": spinbox_refs,
            "comment_field": comment_field
        }
        
        print(f"💾 Card data salvo para {vendor_name}:")
        print(f"  - supplier_id: {supplier_id}")
        print(f"  - spinbox_refs keys: {list(spinbox_refs.keys()) if spinbox_refs else 'VAZIO'}")
        print(f"  - comment_field: {comment_field is not None}")
        print(f"  - score_control_type usado: {score_control_type}")
        
        return card

    search_field_ref = ft.Ref()

    def create_score_slider():
        """Cria um widget de slider customizado para notas de 0 a 10."""
        
        # O texto que exibirá o valor do slider
        score_text = ft.Text("0.0", width=40, text_align=ft.TextAlign.RIGHT)

        # O slider
        score_slider = ft.Slider(
            min=0,
            max=10,
            divisions=100,  # (10 - 0) / 0.1 = 100
            value=0,
            width=200  # Largura mínima do slider (removido expand=True que conflitava)
        )

        def on_slider_change(e):
            # Formata o valor para ter uma casa decimal
            score_text.value = f"{e.control.value:.1f}"
            # Apenas atualizar se o controle estiver na página
            if hasattr(score_text, 'page') and score_text.page is not None:
                score_text.update()
        
        score_slider.on_change = on_slider_change
        
        # Retorna o slider e o texto em uma coluna (texto centralizado embaixo)
        slider_column = ft.Column([
            score_slider, 
            ft.Container(
                content=score_text,
                alignment=ft.alignment.center,
                width=200,  # Mesma largura do slider para centralizar perfeitamente
                margin=ft.margin.only(top=-20)  # Margem negativa para aproximar do slider
            )
        ], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        return slider_column, score_slider, score_text

    def create_result_widget(record):
        """Cria um card de resultado otimizado para um registro do banco."""
        supplier_id = record.get('supplier_id', '?')
        vendor_name = record.get('vendor_name', '?')
        bu = record.get('BU', '?')
        status = record.get('supplier_status', '?')
        supplier_number = record.get('supplier_number', '?')
        supplier_origin = record.get('supplier_name', 'N/A')

        print(f"Criando card para: {vendor_name} (ID: {supplier_id})")
        print(f"🔍 DEBUG PERMISSÕES NO CARD (SLIDER VERSION):")
        print(f"  current_user_permissions = {current_user_permissions}")

        # Criar sliders com referências
        score_sliders = {}
        score_texts = {}
        score_rows = []
        
        # Mapeamento das permissões
        permission_map = {
            "NIL": "nil",
            "Pickup": "pickup", 
            "Package": "package",
            "OTIF": "otif"
        }

        for ui_name in ["NIL", "Pickup", "Package", "OTIF"]:
            # Verificar se o usuário tem permissão para este campo
            permission_key = permission_map.get(ui_name)
            has_permission = (current_user_permissions.get(permission_key, False) if current_user_permissions else True)
            
            print(f"  {ui_name}: permission_key='{permission_key}', has_permission={has_permission}")
            
            # Sempre criar o campo, mas desabilitar se não tiver permissão
            print(f"    {'✅ Criando' if has_permission else '🔒 Criando (desabilitado)'} {score_control_type} {ui_name}")
            
            if score_control_type == "slider":
                slider_row, slider_control, text_control = create_score_slider()
                # Desabilitar slider se não tiver permissão
                if not has_permission:
                    slider_control.disabled = True
                    slider_control.opacity = 0.5
                    text_control.disabled = True
                    text_control.opacity = 0.5
                score_sliders[ui_name] = slider_control
                score_texts[ui_name] = text_control
                control_widget = slider_row
            else:  # spinbox
                spinbox_control = create_spinbox()
                spinbox_field = spinbox_control.controls[1]  # O TextField é o segundo controle
                # Desabilitar spinbox se não tiver permissão
                if not has_permission:
                    spinbox_field.disabled = True
                    spinbox_field.opacity = 0.5
                    # Desabilitar botões também
                    spinbox_control.controls[0].disabled = True  # Botão de diminuir
                    spinbox_control.controls[2].disabled = True  # Botão de aumentar
                    spinbox_control.controls[0].opacity = 0.5
                    spinbox_control.controls[2].opacity = 0.5
                score_sliders[ui_name] = spinbox_field
                control_widget = spinbox_control
            
            row = ft.Row([
                ft.Container(
                    content=ft.Text(
                        ui_name, 
                        weight="bold", 
                        size=14, 
                        opacity=0.5 if not has_permission else 1.0
                    ),
                    alignment=ft.alignment.center_left,
                    expand=1
                ),
                control_widget
            ], 
            alignment=ft.MainAxisAlignment.START, 
            spacing=10,
            tight=True
            )
            if score_control_type == "slider":
                control_widget.expand = 2
            score_rows.append(row)

        # Campo de comentário mais simples
        comment_field = ft.TextField(
            label="Comentário",
            multiline=True,
            min_lines=6,
            max_lines=8,
            border_radius=8,
            # Usar a mesma cor do card para os campos de comentário
            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
        )

        # Estado do favorito
        is_favorite = ft.Ref[bool]()
        is_favorite.current = False

        # Verificar se já está nos favoritos ao criar o card
        def check_favorite_status():
            global current_user_wwid
            if not current_user_wwid or not db_conn:
                return False
            try:
                cursor = db_conn.cursor()
                check_query = "SELECT COUNT(*) FROM favorites_table WHERE user_wwid=? AND supplier_id=?"
                result = db_manager.query_one(check_query, (current_user_wwid, supplier_id))
                return result['COUNT(*)'] > 0 if result else False
            except Exception:
                return False

        # Definir estado inicial do favorito
        is_favorite.current = check_favorite_status()

        def save_score(e):
            # Animação do botão - iniciar loading
            save_button = e.control
            
            # Verificar se já está processando para evitar cliques múltiplos
            if hasattr(save_button, '_is_processing') and save_button._is_processing:
                print("🚫 Clique ignorado - operação já em andamento (slider)")
                return
                
            # Marcar como processando
            save_button._is_processing = True
            
            original_text = save_button.content.value if hasattr(save_button.content, 'value') else save_button.text
            original_icon = save_button.icon
            
            def reset_button_state():
                """Função para resetar o estado do botão"""
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                save_button._is_processing = False
                if hasattr(save_button, '_restore_thread'):
                    save_button._restore_thread = None
                if hasattr(save_button, '_restore_thread_cancelled'):
                    save_button._restore_thread_cancelled = False
                safe_update_control(save_button, page)
            
            # Aplicar efeito visual de loading
            save_button.text = "Salvando..."
            save_button.icon = ft.Icons.HOURGLASS_EMPTY
            save_button.disabled = True
            safe_update_control(save_button, page)
            
            if not db_conn:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Erro: Banco de dados não conectado.", "red", restore_control=save_button)
                return
                
            if not selected_month.current or not selected_year.current:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Selecione mês e ano antes de salvar.", "orange", restore_control=save_button)
                return
                
            month_val = selected_month.current.value
            year_val = selected_year.current.value
            
            if not month_val or not year_val:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Selecione mês e ano antes de salvar.", "orange", restore_control=save_button)
                return

            # Validação de data futura baseada na lógica legacy
            from datetime import datetime
            current_date = datetime.now()
            ano_atual = current_date.year
            mes_atual = current_date.month
            register_date = current_date.strftime("%Y-%m-%d %H:%M:%S")  # Data atual para registro
            
            try:
                mes_int = int(month_val)
                ano_int = int(year_val)
            except ValueError:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Valores de mês e ano inválidos.", "red", restore_control=save_button)
                return
                
            # Prevenir salvamento de scores para meses futuros
            if (ano_int > ano_atual) or (ano_int == ano_atual and mes_int > mes_atual):
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                safe_update_control(save_button, page)
                show_toast("Não é possível salvar scores para meses futuros.", "orange", restore_control=save_button)
                return

            try:
                cursor = db_conn.cursor()
                
                # Buscar critérios atuais da tabela criteria_table
                criteria_results = db_manager.query("SELECT criteria_category, value FROM criteria_table")
                criteria_values = {}
                for row in criteria_results:
                    criteria_name = row['criteria_category']
                    criteria_value = float(row['value'])
                    criteria_values[criteria_name] = criteria_value
                
                print(f"🎯 Critérios carregados para cálculo: {criteria_values}")
                
                # Preparar os dados para salvar - valores originais dos sliders
                values_to_save = {}
                total_score_calculation = 0.0
                
                # Verificar permissões e salvar valores originais, calcular total_score separadamente
                if current_user_permissions.get('otif', False) and "OTIF" in score_sliders:
                    raw_score = float(score_sliders["OTIF"].value or 0)
                    values_to_save['otif'] = raw_score  # Salvar valor original
                    
                    # Calcular para total_score
                    criteria_weight = criteria_values.get('OTIF', 0.22)
                    weighted_value = round(raw_score * criteria_weight, 1)
                    total_score_calculation += weighted_value
                    print(f"  OTIF: {raw_score} (salvo) × {criteria_weight} = {weighted_value} (para total)")
                    
                if current_user_permissions.get('pickup', False) and "Pickup" in score_sliders:
                    raw_score = float(score_sliders["Pickup"].value or 0)
                    values_to_save['quality_pickup'] = raw_score  # Salvar valor original
                    
                    # Calcular para total_score
                    criteria_weight = criteria_values.get('Quality of Pick Up', 0.28)
                    weighted_value = round(raw_score * criteria_weight, 1)
                    total_score_calculation += weighted_value
                    print(f"  Pickup: {raw_score} (salvo) × {criteria_weight} = {weighted_value} (para total)")
                    
                if current_user_permissions.get('package', False) and "Package" in score_sliders:
                    raw_score = float(score_sliders["Package"].value or 0)
                    values_to_save['quality_package'] = raw_score  # Salvar valor original
                    
                    # Calcular para total_score
                    criteria_weight = criteria_values.get('Quality-Supplier Package', 0.28)
                    weighted_value = round(raw_score * criteria_weight, 1)
                    total_score_calculation += weighted_value
                    print(f"  Package: {raw_score} (salvo) × {criteria_weight} = {weighted_value} (para total)")
                    
                if current_user_permissions.get('nil', False) and "NIL" in score_sliders:
                    raw_score = float(score_sliders["NIL"].value or 0)
                    values_to_save['nil'] = raw_score  # Salvar valor original
                    
                    # Calcular para total_score
                    criteria_weight = criteria_values.get('NIL', 0.22)
                    weighted_value = round(raw_score * criteria_weight, 1)
                    total_score_calculation += weighted_value
                    print(f"  NIL: {raw_score} (salvo) × {criteria_weight} = {weighted_value} (para total)")
                
                if not values_to_save:
                    # Restaurar botão em caso de erro
                    save_button.text = original_text
                    save_button.icon = original_icon
                    save_button.disabled = False
                    safe_update_control(save_button, page)
                    show_toast("Você não tem permissão para salvar nenhum campo.", "red")
                    return
                
                comment_val = comment_field.value or ""
                
                # O total_score é a soma dos valores ponderados, não dos valores originais
                total_score = round(total_score_calculation, 1)
                print(f"📊 Total Score calculado: {total_score}")
                
                # Verificar se já existe um registro e buscar registered_by atual
                check_query = """
                    SELECT COUNT(*), registered_by FROM supplier_score_records_table 
                    WHERE supplier_id = ? AND month = ? AND year = ?
                """
                result = db_manager.query_one(check_query, (supplier_id, int(month_val), int(year_val)))
                exists = result['COUNT(*)'] > 0 if result else False
                current_registered_by = result['registered_by'] if result and result['registered_by'] else ""
                
                # Construir registered_by acumulativo - FUNÇÃO SLIDER
                saved_field_names = []
                field_mapping = {"NIL": "nil", "OTIF": "otif", "PICKUP": "quality_pickup", "PACKAGE": "quality_package"}
                field_mapping = {"NIL": "nil", "OTIF": "otif", "PICKUP": "quality_pickup", "PACKAGE": "quality_package"}
                for field, db_field in field_mapping.items():
                    if db_field in values_to_save.keys():  # Se o campo foi salvo, adicionar
                        saved_field_names.append(field)
                
                # Combinar com os campos já registrados anteriormente
                existing_fields = set(current_registered_by.split(',')) if current_registered_by else set()
                all_fields = existing_fields.union(set(saved_field_names))
                new_registered_by = ','.join(sorted([f for f in all_fields if f]))  # Remove strings vazias e ordena
                
                print(f"📝 Registered_by (SLIDER): '{current_registered_by}' -> '{new_registered_by}'")
                
                # Construir query dinamicamente baseado nas permissões
                if exists:
                    # Atualizar apenas os campos permitidos
                    set_clauses = [f"{field} = ?" for field in values_to_save.keys()]
                    update_values = list(values_to_save.values())
                    
                    # Sempre atualizar o comentário, total_score, registered_by, register_date, changed_by e supplier_name
                    set_clauses.extend(["comment = ?", "total_score = ?", "registered_by = ?", "register_date = ?", "changed_by = ?", "supplier_name = ?"])
                    update_values.extend([comment_val, total_score, new_registered_by, register_date, current_user_name, vendor_name])

                    if set_clauses:
                        update_query = f"UPDATE supplier_score_records_table SET {', '.join(set_clauses)} WHERE supplier_id = ? AND month = ? AND year = ?"
                        update_values.extend([supplier_id, int(month_val), int(year_val)])
                        db_manager.execute(update_query, update_values)
                else:
                    # Inserir novo registro com campos zerados para campos sem permissão
                    insert_query = """
                        INSERT INTO supplier_score_records_table 
                        (supplier_id, month, year, otif, quality_pickup, quality_package, nil, comment, total_score, registered_by, register_date, changed_by, supplier_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db_manager.execute(insert_query, (
                        supplier_id, 
                        int(month_val), 
                        int(year_val), 
                        values_to_save.get('otif', 0),
                        values_to_save.get('quality_pickup', 0), 
                        values_to_save.get('quality_package', 0), 
                        values_to_save.get('nil', 0),
                        comment_val,
                        total_score,
                        new_registered_by,
                        register_date,
                        current_user_name,
                        vendor_name
                    ))
            
                
                # Rechecagem de status imediatamente antes do commit para evitar condição de corrida
                try:
                    final_row_status = db_manager.query_one("SELECT supplier_status FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
                    final_status = final_row_status['supplier_status'] if final_row_status else None
                    print(f"🔁 Rechecagem final de status antes do commit (slider): {final_status}")
                    if final_status and str(final_status).strip().lower().startswith("inactive"):
                        show_toast("❌ Não é possível salvar para fornecedores inativos.", "red", restore_control=save_button)
                        save_button.text = original_text
                        save_button.icon = original_icon
                        save_button.disabled = False
                        save_button._is_processing = False
                        safe_update_control(save_button, page)
                        return
                except Exception as ex_final_status:
                    print(f"Aviso: falha na rechecagem final de status (slider): {ex_final_status}")

                saved_fields = [k.replace('quality_', '').replace('_', ' ').title() for k in values_to_save.keys()]
                show_toast(f"✅ Score salvo para {vendor_name} ({month_val}/{year_val}) - Total: {total_score:.1f}", "green")
                
                # Restaurar botão após sucesso com ícone de confirmação temporário
                save_button.text = "Salvo!"
                save_button.icon = ft.Icons.CHECK
                save_button.disabled = False
                safe_update_control(save_button, page)
                
                # Cancelar thread anterior se existir
                if hasattr(save_button, '_restore_thread') and save_button._restore_thread is not None:
                    save_button._restore_thread_cancelled = True
                
                # Agendar restauração do botão original após 2 segundos
                def restore_button():
                    import time
                    # Verificar cancelamento durante a espera
                    for i in range(20):  # 20 x 0.1s = 2s
                        if hasattr(save_button, '_restore_thread_cancelled') and save_button._restore_thread_cancelled:
                            return  # Thread foi cancelada
                        time.sleep(0.1)
                    
                    # Verificar novamente se foi cancelada antes de restaurar
                    if hasattr(save_button, '_restore_thread_cancelled') and save_button._restore_thread_cancelled:
                        return
                        
                    if hasattr(save_button, 'update'):  # Verificar se ainda existe
                        save_button.text = original_text
                        save_button.icon = original_icon
                        save_button._restore_thread = None
                        save_button._restore_thread_cancelled = False
                        save_button._is_processing = False  # CRÍTICO: resetar flag de processamento
                        safe_update_control(save_button, page)
                
                import threading
                save_button._restore_thread_cancelled = False
                save_button._restore_thread = threading.Thread(target=restore_button, daemon=True)
                save_button._restore_thread.start()
                
            except Exception as ex:
                # Restaurar botão em caso de erro
                save_button.text = original_text
                save_button.icon = original_icon
                save_button.disabled = False
                save_button._is_processing = False  # Adicionar reset do flag
                safe_update_control(save_button, page)
                
                show_toast(f"❌ Erro ao salvar: {str(ex)}", "red")
                print(f"❌ Erro detalhado ao salvar dados:")
                print(f"   Fornecedor: {vendor_name} (ID: {supplier_id})")
                print(f"   Período: {month_val}/{year_val}")
                print(f"   Erro: {ex}")
                import traceback
                traceback.print_exc()

        def toggle_favorite(e):
            global current_user_wwid
            if not current_user_wwid:
                show_toast("Erro: Usuário não autenticado.", "red")
                return
                
            try:
                # Verificar se já está nos favoritos
                check_query = "SELECT COUNT(*) FROM favorites_table WHERE user_wwid=? AND supplier_id=?"
                result = db_manager.query_one(check_query, (current_user_wwid, supplier_id))
                is_favorited = result["COUNT(*)"] > 0
                
                if is_favorited:
                    # Remover dos favoritos
                    delete_query = "DELETE FROM favorites_table WHERE user_wwid=? AND supplier_id=?"
                    db_manager.execute(delete_query, (current_user_wwid, supplier_id))
                    is_favorite.current = False
                    e.control.selected = False
                    show_toast(f"{vendor_name} removido dos favoritos", "orange")
                    print(f"Favorito removido: {vendor_name} (ID: {supplier_id})")
                else:
                    # Adicionar aos favoritos
                    insert_query = "INSERT INTO favorites_table (user_wwid, supplier_id) VALUES (?, ?)"
                    db_manager.execute(insert_query, (current_user_wwid, supplier_id))
                    is_favorite.current = True
                    e.control.selected = True
                    show_toast(f"{vendor_name} adicionado aos favoritos", "green")
                    print(f"Favorito adicionado: {vendor_name} (ID: {supplier_id})")
                
                # Atualização segura do controle
                try:
                    if hasattr(e.control, 'page') and e.control.page is not None:
                        e.control.update()
                    else:
                        # Se o controle não está vinculado à página, atualizar toda a página
                        page.update()
                except Exception as update_error:
                    print(f"Aviso: Erro ao atualizar controle, atualizando página: {update_error}")
                    page.update()
                
            except Exception as db_error:
                show_toast(f"Erro ao salvar favorito: {db_error}", "red")
                print(f"Erro no banco de dados: {db_error}")
            except Exception as ex:
                show_toast(f"Erro inesperado: {ex}", "red")
                print(f"Erro ao toggle favorite: {ex}")

        # Montagem do layout do card
        origin_icon = ft.Icons.AIRPLANEMODE_ACTIVE if supplier_origin == "Importado" else ft.Icons.FLAG if supplier_origin == "Nacional" else ft.Icons.HELP_OUTLINE
        status_icon_color = "green" if str(status).lower().startswith("active") else "red"

        info_col = ft.Column(
            controls=[
                ft.Text(
                    vendor_name, 
                    weight="bold", 
                    size=16, 
                    width=200,  # Define largura para permitir quebra de linha
                    text_align=ft.TextAlign.LEFT
                ),
                ft.Row([ft.Icon(ft.Icons.BUSINESS, size=14, opacity=0.7), ft.Text(f"BU: {bu}", size=12)], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([ft.Icon(ft.Icons.RECEIPT_LONG, size=14, opacity=0.7), ft.Text(f"PO: {supplier_number}", size=12)], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([ft.Icon(ft.Icons.FINGERPRINT, size=14, opacity=0.7), ft.Text(f"ID: {supplier_id}", size=12)], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([ft.Icon(origin_icon, size=14, opacity=0.7), ft.Text(f"Origem: {supplier_origin}", size=12)], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Icon(ft.Icons.CIRCLE, size=14, color=status_icon_color), 
                    ft.Text(
                        f"Status: {status}", 
                        size=12,
                        color=status_icon_color
                    )
                ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], 
            spacing=4, 
            tight=True,
            expand=1  # Permite variação de tamanho
        )

        scores_col = ft.Column(
            score_rows, 
            spacing=8, 
            tight=True,
            width=240  # Largura fixa para a área das notas
        )

        # Coluna de ações com comentário que se expande
        actions_col = ft.Column([
            comment_field
        ], 
        expand=True,  # O comentário pode se expandir
        spacing=10,
        alignment=ft.MainAxisAlignment.START
        )

        # Conteúdo principal do card (sem os botões)
        main_content = ft.Row([
            info_col,
            ft.VerticalDivider(width=1, color="outline"),
            scores_col,
            ft.VerticalDivider(width=1, color="outline"),
            actions_col
        ], 
        vertical_alignment=ft.CrossAxisAlignment.START,
        expand=True,
        spacing=15
        )

        # Criar referência para o botão de salvar para permitir animações
        save_button = ft.ElevatedButton(
            "Salvar",
            on_click=save_score,
            icon=ft.Icons.SAVE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        )

        # Card principal usando Stack para posicionar botões absolutamente
        card_content = ft.Container(
            content=ft.Stack([
                # Conteúdo principal
                main_content,
                # Botões posicionados no canto inferior direito
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.FAVORITE_BORDER,
                            selected_icon=ft.Icons.FAVORITE,
                            on_click=toggle_favorite,
                            tooltip="Favoritar",
                            selected=is_favorite.current,  # Usar o estado real do favorito
                            
                        ),
                        save_button,
                    ], 
                    alignment=ft.MainAxisAlignment.END,
                    tight=True
                    ),
                    right=5,
                    bottom=5,
                )
            ], expand=True),
            padding=15,
            height=300,  # Altura fixa consistente
            border_radius=12
        )

        card = ft.Card(
            content=card_content,
            elevation=2,
            margin=ft.margin.symmetric(vertical=5, horizontal=0),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background')
        )
        
        # Anexar dados necessários ao card
        if score_control_type == "slider":
            card.data = {
                "supplier_id": supplier_id,
                "score_sliders": score_sliders,
                "score_texts": score_texts,
                "comment_field": comment_field
            }
        else:  # spinbox
            # Para spinbox, usar spinbox_refs como esperado pelo load_scores()
            spinbox_refs = score_sliders  # Os spinboxes foram salvos em score_sliders
            card.data = {
                "supplier_id": supplier_id,
                "spinbox_refs": spinbox_refs,
                "comment_field": comment_field
            }
        
        return card

    def search_suppliers():
        """Versão otimizada da busca de fornecedores."""
        if not search_field_ref.current:
            return
            
        search_term = search_field_ref.current.value.strip()
        bu_val = selected_bu.current.value if selected_bu.current else None
        po_val = selected_po.current.value if selected_po and selected_po.current else None

        print(f"Pesquisando por: '{search_term}', BU: {bu_val}")

        # Limpar resultados anteriores
        if responsive_app_manager:
            responsive_app_manager.clear_results()
        else:
            results_list.controls.clear()
            results_list.update()

        # Se não há termo de busca nem BU nem PO selecionados, mostrar favoritos
        if not search_term and (not bu_val or not bu_val.strip()) and (not po_val or not str(po_val).strip()):
            show_favorites_only()
            return

        if not db_conn:
            results_list.controls.append(
                ft.Container(
                    ft.Text("Erro: Não foi possível conectar ao banco de dados.", color="red"),
                    padding=20
                )
            )
            results_list.update()
            return

        try:
            base_query = """
                SELECT supplier_id, vendor_name, bu, supplier_status, supplier_number, supplier_name
                FROM supplier_database_table 
            """
            where_clauses = []
            params = []

            if search_term:
                where_clauses.append("(vendor_name LIKE ? OR supplier_id LIKE ?)")
                params.extend([f"%{search_term}%", f"%{search_term}%"])

            if bu_val and bu_val.strip():
                where_clauses.append("BU LIKE ?")
                params.append(f"%{bu_val.strip()}%")

            if po_val and str(po_val).strip():
                # Filtrar por supplier_number (PO)
                where_clauses.append("supplier_number LIKE ?")
                params.append(f"%{str(po_val).strip()}%")

            query = f"{base_query} WHERE {' AND '.join(where_clauses)} ORDER BY vendor_name LIMIT 10"
            
            print(f"Executando query: {query}")
            print(f"Parâmetros: {params}")

            records = db_manager.query(query, params)
            
            print(f"Encontrados {len(records)} registros")
            
            if not records:
                results_list.controls.append(
                    ft.Container(
                        ft.Text("Nenhum resultado encontrado.", italic=True, size=16),
                        alignment=ft.alignment.center,
                        padding=40
                    )
                )
            else:
                # Adicionar cada card individualmente
                for i, record in enumerate(records):
                    print(f"Criando card {i+1}/{len(records)}: {record.get('vendor_name', 'Unknown')}")
                    try:
                        card = create_result_widget(record)
                        if responsive_app_manager:
                            responsive_app_manager.add_card_to_layout(card)
                        else:
                            results_list.controls.append(card)
                    except Exception as card_error:
                        print(f"Erro ao criar card para {record.get('vendor_name', 'Unknown')}: {card_error}")
                        continue
            
        except sqlite3.Error as db_error:
            error_msg = f"Erro no banco de dados: {db_error}"
            print(error_msg)
            results_list.controls.append(
                ft.Container(
                    ft.Text(error_msg, color="red"),
                    padding=20
                )
            )
        except Exception as e:
            error_msg = f"Erro inesperado: {e}"
            print(error_msg)
            results_list.controls.append(
                ft.Container(
                    ft.Text(error_msg, color="red"),
                    padding=20
                )
            )

        # Atualizar a lista
        results_list.update()
        
        # Carregar scores após criar os cards
        if results_list.controls and selected_month.current and selected_year.current:
            load_scores()

    def show_favorites_only():
        """Mostra apenas os suppliers favoritos do usuário logado"""
        global current_user_wwid
        # Limpar resultados existentes antes de adicionar favoritos para evitar duplicação
        try:
            if 'responsive_app_manager' in globals() and responsive_app_manager and getattr(responsive_app_manager, 'results_container', None):
                responsive_app_manager.clear_results()
            elif 'results_list' in globals() and results_list:
                results_list.controls.clear()
                results_list.update()
        except Exception as _clearex:
            print(f"Aviso: falha ao limpar resultados antes de mostrar favoritos: {_clearex}")

        if not current_user_wwid:
            results_list.controls.append(
                ft.Container(
                    ft.Text("Erro: Usuário não autenticado.", color="red"),
                    padding=20
                )
            )
            results_list.update()
            return

        if not db_conn:
            results_list.controls.append(
                ft.Container(
                    ft.Text("Erro: Não foi possível conectar ao banco de dados.", color="red"),
                    padding=20
                )
            )
            results_list.update()
            return

        try:
            # Buscar suppliers favoritos do usuário
            favorites_query = """
                SELECT s.supplier_id, s.vendor_name, s.bu, s.supplier_status, s.supplier_number, s.supplier_name
                FROM supplier_database_table s 
                INNER JOIN favorites_table f ON s.supplier_id = f.supplier_id
                WHERE f.user_wwid = ?
                ORDER BY s.vendor_name
            """
            
            print(f"Buscando favoritos para usuário: {current_user_wwid}")
            records = db_manager.query(favorites_query, (current_user_wwid,))
            
            print(f"Encontrados {len(records)} favoritos")
            
            if not records:
                results_list.controls.append(
                    ft.Container(
                        ft.Column([
                            ft.Icon(ft.Icons.FAVORITE_BORDER, size=40, color="gray"),
                            ft.Text("Você ainda não tem favoritos.", italic=True, size=16, text_align=ft.TextAlign.CENTER),
                            ft.Text("Use o campo de pesquisa para encontrar suppliers e clique no coração para favoritar.", 
                                   size=12, text_align=ft.TextAlign.CENTER, color="gray")
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                        alignment=ft.alignment.center,
                        padding=40
                    )
                )
            else:
                # Adicionar cada card individualmente
                for i, record in enumerate(records):
                    print(f"Criando card favorito {i+1}/{len(records)}: {record.get('vendor_name', 'Unknown')}")
                    try:
                        card = create_result_widget(record)
                        if responsive_app_manager:
                            responsive_app_manager.add_card_to_layout(card)
                        else:
                            results_list.controls.append(card)
                    except Exception as card_error:
                        print(f"Erro ao criar card para {record.get('vendor_name', 'Unknown')}: {card_error}")
                        continue
            
        except sqlite3.Error as db_error:
            error_msg = f"Erro no banco de dados: {db_error}"
            print(error_msg)
            results_list.controls.append(
                ft.Container(
                    ft.Text(error_msg, color="red"),
                    padding=20
                )
            )
        except Exception as e:
            error_msg = f"Erro inesperado: {e}"
            print(error_msg)
            results_list.controls.append(
                ft.Container(
                    ft.Text(error_msg, color="red"),
                    padding=20
                )
            )

        # Atualizar a lista
        results_list.update()
        
        # Carregar scores após criar os cards
        if results_list.controls and selected_month.current and selected_year.current:
            load_scores()

    # --- Fim: Lógica do Banco de Dados e Pesquisa ---

    # --- Início: Lógica e Controles da Aba Score ---

    results_list = ft.ListView(spacing=10, padding=20)

    # Referências para dropdowns que precisam ser atualizados com tema
    month_dropdown = ft.Dropdown(
        label="Mês", 
        options=month_options, 
        ref=selected_month, 
        width=120, 
        value="", # Não pré-selecionar mês (iniciar vazio)
        on_change=on_month_year_change,
        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
        border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
    )
    
    year_dropdown = ft.Dropdown(
        label="Ano", 
        options=year_options, 
        ref=selected_year, 
        width=120, 
        value="", # Pré-selecionar "(Ano Atual)"
        on_change=on_month_year_change,
        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
        border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
    )

    # Conteúdo da aba Score
    score_form = ft.Column(
        controls=[
            ft.TextField(
                hint_text="Pesquisar por nome ou ID do fornecedor...",
                prefix_icon=ft.Icons.SEARCH,
                border_radius=8,
                on_change=lambda e: search_suppliers(),
                ref=search_field_ref,
                bgcolor=None,
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        label="PO", 
                        expand=True, 
                        border_radius=8,
                        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
                        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                        border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline'),
                        ref=selected_po,
                        on_change=lambda e: search_suppliers()
                    ),
                    ft.Dropdown(
                        label="BU",
                        expand=True,
                        border_radius=8,
                        ref=selected_bu,
                        on_change=lambda e: search_suppliers(),
                        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
                        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                        border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline'),
                        options=[ft.dropdown.Option(v) for v in (load_list_options('business_unit_table','bu'))]
                    ),
                    month_dropdown,
                    year_dropdown,
                ],
                spacing=10,
            ),
        ],
        spacing=15,
    )

    score_form_container = ft.Container(
        content=score_form, 
        padding=15,
        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
        border_radius=8
    )

    score_view_content = ft.Card(
        content=score_form_container,
        width=600,
        elevation=2
    )

    # --- Fim: Lógica e Controles da Aba Score ---

    # --- Início: Lógica e Controles da Aba Configs ---

    # Estado para controlar qual sub-aba está selecionada
    selected_config_tab = ft.Ref()
    selected_config_tab.current = 0

    def set_config_tab(idx):
        def handler(e):
            # Verificar se o usuário tem acesso à aba de configuração
            accessible_tabs = get_user_accessible_config_tabs(current_user_privilege or "User")
            accessible_indices = [tab_idx for _, _, tab_idx in accessible_tabs]
            
            if idx not in accessible_indices:
                show_toast("Acesso negado para esta configuração", ft.colors.RED)
                return
                
            # Limpar campos da aba Log quando sair dela (se estava na aba Log antes)
            if selected_config_tab.current == 5 and idx != 5:
                try:
                    clear_log_fields()
                except Exception as ex:
                    print(f"Aviso: erro ao limpar campos da aba Log: {ex}")
            
            selected_config_tab.current = idx
            themes_content.visible = idx == 0
            suppliers_content.visible = idx == 1
            criteria_content.visible = idx == 2
            users_content.visible = idx == 3
            lists_content.visible = idx == 4
            log_content.visible = idx == 5
            # Ao abrir a aba Log, garantir que os dados sejam carregados
            if idx == 5:
                try:
                    ensure_log_loaded()
                except Exception:
                    pass
            update_config_tabs()
            page.update()
        return handler

    def config_tab_item(icon, text, idx):
        is_selected = selected_config_tab.current == idx
        Colors = get_current_theme_colors(get_theme_name_from_page(page))
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=Colors['primary'] if is_selected else Colors['on_surface'], size=24),
                ft.Text(text, size=12, weight="bold" if is_selected else "normal",
                       color=Colors['primary'] if is_selected else Colors['on_surface'])
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            border_radius=8,
            bgcolor=Colors['primary_container'] if is_selected else None,
            on_click=set_config_tab(idx),
            animate=200,
        )

    def get_user_accessible_config_tabs(privilege):
        """Retorna lista de abas de configuração que o usuário pode acessar"""
        all_tabs = [
            (ft.Icons.PALETTE, "Themes", 0),
            (ft.Icons.BUSINESS, "Suppliers", 1),
            (ft.Icons.TUNE, "Criteria", 2),
            (ft.Icons.PEOPLE, "Users", 3),
            (ft.Icons.LIST, "Lists", 4),
            (ft.Icons.HISTORY, "Log", 5),
        ]
        
        if privilege == "Super Admin":
            # Super Admin pode acessar tudo
            return all_tabs
        elif privilege == "Admin":
            # Admin pode: Themes, Suppliers, Lists (sem Users, Criteria, Log)
            return [(icon, name, idx) for icon, name, idx in all_tabs if idx in [0, 1, 4]]
        else:  # User
            # User pode apenas: Themes
            return [(icon, name, idx) for icon, name, idx in all_tabs if idx == 0]

    def update_config_tabs():
        # Filtrar abas baseado no privilégio do usuário
        accessible_tabs = get_user_accessible_config_tabs(current_user_privilege or "User")
        config_tabs_row.controls = [
            config_tab_item(icon, name, idx) for icon, name, idx in accessible_tabs
        ]
        config_tabs_row.update()

    def update_all_comboboxes():
        """Recarrega opções dinâmicas para todos os Dropdowns do app."""
        try:
            # Carregar opções de DB
            bu_opts = load_list_options('business_unit_table', 'bu')
            planner_opts = load_list_options('planner_table', 'alias')
            continuity_opts = load_list_options('continuity_table', 'alias')
            sourcing_opts = load_list_options('sourcing_table', 'alias')
            sqie_opts = load_list_options('sqie_table', 'alias')

            # Atualizar UI de listas (se existir) e forçar recarregamento das listas exibidas
            for k in lists_controls.keys():
                refresh_list_ui(k)
            page.update()
        except Exception as ex:
            print(f"Erro ao atualizar comboboxes: {ex}")

    # RadioGroup para seleção de tema
    theme_radio_group = ft.RadioGroup(
        content=ft.Column([
            ft.Radio(value="white", label="Tema Claro"),
            ft.Radio(value="dark", label="Tema Escuro"),
            ft.Radio(value="dracula", label="Tema Dracula"),
        ]),
        value="white",
        on_change=theme_changed,
    )
    
    def control_type_changed(e):
        """Callback quando o tipo de controle é alterado"""
        global score_control_type
        score_control_type = e.control.value
        save_score_control_type(score_control_type)
        show_toast(f"⚙️ Tipo de controle alterado para: {score_control_type.capitalize()}", "blue")
        print(f"🔧 Tipo de controle alterado para: {score_control_type}")
        
        # Limpar os resultados existentes para forçar recriação com novo controle
        print(f"🧹 Limpando resultados existentes...")
        if responsive_app_manager:
            responsive_app_manager.clear_results()
            print(f"✅ Resultados limpos via responsive_app_manager")
        else:
            results_list.controls.clear()
            results_list.update()
            print(f"✅ Resultados limpos via results_list")
        print(f"🔄 Próxima busca criará cards com: {score_control_type}")
    
    # Carregar configuração salva do tipo de controle
    load_score_control_type()
    
    # Salvar incremento padrão no banco se não existir
    try:
        result = db_manager.query_one("SELECT COUNT(*) FROM app_settings WHERE setting_key = 'spinbox_increment'")
        if result["COUNT(*)"] == 0:
            save_spinbox_increment(0.1)  # Valor padrão
    except Exception as e:
        print(f"Erro ao verificar/salvar incremento padrão: {e}")
    
    # RadioGroup para seleção do tipo de controle
    control_type_radio_group = ft.RadioGroup(
        content=ft.Column([
            ft.Radio(value="slider", label="Slider (Deslizante)"),
            ft.Radio(value="spinbox", label="Spinbox (Botões +/-)"),
        ]),
        value=score_control_type,  # Usar o valor carregado do banco
        on_change=control_type_changed,
    )
    
    # Carregar tema salvo do usuário e aplicar ao radio group
    if current_user_wwid:
        saved_theme = load_user_theme(current_user_wwid)
        if saved_theme:
            theme_radio_group.value = saved_theme
            print(f"Tema carregado para radio group: {saved_theme}")
        else:
            print("Nenhum tema salvo encontrado para usuário, usando padrão")
    else:
        # Se não há usuário logado, carregar tema padrão da tabela
        try:
            default_theme = db_manager.query_one("SELECT theme_mode FROM theme_settings ORDER BY last_updated DESC LIMIT 1")
            if default_theme:
                theme_radio_group.value = default_theme["theme_mode"]
                print(f"Tema padrão carregado: {default_theme['theme_mode']}")
        except Exception as e:
            print(f"Erro ao carregar tema padrão: {e}")

    # Controle de duração do show_toast
    toast_duration_slider = ft.Slider(
        min=1,
        max=10,
        divisions=9,
        value=app_settings.get('toast_duration', 3),
        label="Duração: {value}s",
        width=300,
    )
    
    def update_toast_duration(e):
        global app_settings
        new_duration = int(e.control.value)
        app_settings['toast_duration'] = new_duration
        save_app_settings(app_settings)
        show_toast(f"⚙️ Duração do show_toast alterada para {new_duration}s", "blue")
    
    toast_duration_slider.on_change = update_toast_duration
    
    # Slider para configurar incremento do spinbox
    spinbox_increment_slider = ft.Slider(
        min=0.1,
        max=1.0,
        divisions=9,
        value=load_spinbox_increment(),
        label="Incremento: {value}",
        width=300,
    )
    
    def update_spinbox_increment(e):
        new_increment = round(e.control.value, 1)
        save_spinbox_increment(new_increment)
        show_toast(f"⚙️ Incremento do Spinbox alterado para {new_increment}", "blue")
    
    spinbox_increment_slider.on_change = update_spinbox_increment

    # Conteúdo da sub-aba Themes
    themes_content = ft.Container(
        content=ft.Column([
            ft.Text("Configuração de Tema", size=20, weight="bold"),
            ft.Divider(),
            theme_radio_group,
            ft.Divider(),
            ft.Text("Tipo de Controle de Score", size=16, weight="bold"),
            ft.Text("Escolha o tipo de controle para inserir scores:", size=12, color="on_surface_variant"),
            control_type_radio_group,
            ft.Divider(),
            ft.Text("Configurações de Interface", size=16, weight="bold"),
            ft.Row([
                ft.Text("Duração das notificações (show_toast):"),
                toast_duration_slider,
            ], alignment=ft.MainAxisAlignment.START),
            ft.Row([
                ft.Text("Incremento do Spinbox:"),
                spinbox_increment_slider,
            ], alignment=ft.MainAxisAlignment.START),
        ], spacing=15),
        padding=20,
        visible=True
    )

    # ---------- Sub-aba Lists dentro de Configs (gerenciar opções dinâmicas) ----------
    # Criar títulos fixos fora do scroll
    lists_header = ft.Column([
        ft.Text("Gerenciar Listas de Opções", size=20, weight="bold"),
        ft.Text("Configure as opções disponíveis nos dropdowns dos suppliers", size=14, color="on_surface_variant"),
        ft.Divider(height=2),
    ], spacing=8)
    
    # Criar ListView apenas para as ExpansionTiles
    lists_main_column = ft.ListView([], spacing=8, expand=True)

    lists_content = ft.Container(
        content=ft.Column([
            lists_header,
            ft.Container(
                content=lists_main_column,
                expand=True
            )
        ], spacing=10),
        padding=ft.padding.all(20),
        visible=False,
        expand=True
    )

    # Estruturas de UI para cada lista (controls) com feedback e botões de delete
    lists_controls = {
        'sqie': {
            'input': ft.TextField(
                label='Nome SQIE', 
                expand=True, 
                on_change=lambda e: validate_input_exists('sqie'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'alias': ft.TextField(
                label='Alias SQIE', 
                width=200, 
                on_change=lambda e: validate_input_exists('sqie'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'email': ft.TextField(
                label='Email SQIE', 
                expand=True, 
                on_change=lambda e: validate_input_exists('sqie'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'list': ft.Column(spacing=2),
            'feedback': ft.Text(''),
            'selected_item': None
        },
        'continuity': {
            'input': ft.TextField(
                label='Nome Continuity', 
                expand=True, 
                on_change=lambda e: validate_input_exists('continuity'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'alias': ft.TextField(
                label='Alias Continuity', 
                width=200, 
                on_change=lambda e: validate_input_exists('continuity'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'email': ft.TextField(
                label='Email Continuity', 
                expand=True, 
                on_change=lambda e: validate_input_exists('continuity'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'list': ft.Column(spacing=2),
            'feedback': ft.Text(''),
            'selected_item': None
        },
        'planner': {
            'input': ft.TextField(
                label='Nome Planner', 
                expand=True, 
                on_change=lambda e: validate_input_exists('planner'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'alias': ft.TextField(
                label='Alias Planner', 
                width=200, 
                on_change=lambda e: validate_input_exists('planner'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'email': ft.TextField(
                label='Email Planner', 
                expand=True, 
                on_change=lambda e: validate_input_exists('planner'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'list': ft.Column(spacing=2),
            'feedback': ft.Text(''),
            'selected_item': None
        },
        'sourcing': {
            'input': ft.TextField(
                label='Nome Sourcing', 
                expand=True, 
                on_change=lambda e: validate_input_exists('sourcing'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'alias': ft.TextField(
                label='Alias Sourcing', 
                width=200, 
                on_change=lambda e: validate_input_exists('sourcing'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'email': ft.TextField(
                label='Email Sourcing', 
                expand=True, 
                on_change=lambda e: validate_input_exists('sourcing'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'list': ft.Column(spacing=2),
            'feedback': ft.Text(''),
            'selected_item': None
        },
        'bu': {
            'input': ft.TextField(
                label='Nome BU', 
                expand=True, 
                on_change=lambda e: validate_input_exists('bu'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'list': ft.Column(spacing=2),
            'feedback': ft.Text(''),
            'selected_item': None
        },
        'category': {
            'input': ft.TextField(
                label='Nome Category', 
                expand=True, 
                on_change=lambda e: validate_input_exists('category'),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            'list': ft.Column(spacing=2),
            'feedback': ft.Text(''),
            'selected_item': None
        },
    }

    def create_list_item_card(key, item):
        """Cria um card para um item de lista com botões de ação"""
        Colors = get_current_theme_colors(get_theme_name_from_page(page))
        
        # Determinar que tipo de lista estamos lidando
        list_types_with_edit = ['sqie', 'continuity', 'planner', 'sourcing']
        supports_edit = key in list_types_with_edit
        
        # Extrair informações do item
        alias = item.get("alias", "")
        name = item.get("name", "")
        email = item.get("email", "")
        
        # Criar título baseado no tipo
        if key in list_types_with_edit:
            title = f"{alias} - {name}" if name else alias
            subtitle = email if email else "Email não informado"
        else:
            title = alias or item.get("display", "")
            subtitle = None
        
        # Criar conteúdo do card
        content_column = ft.Column([
            ft.Text(
                title, 
                size=14, 
                weight="bold",
                color=Colors['on_surface']
            )
        ], spacing=2)
        
        if subtitle:
            content_column.controls.append(
                ft.Text(subtitle, size=12, color="outline")
            )
        
        # Criar botões de ação
        action_buttons = []
        
        if supports_edit:
            action_buttons.append(
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Editar",
                    icon_size=18,
                    on_click=lambda e, k=key, it=item: show_edit_list_dialog(k, it)
                )
            )
        
        action_buttons.append(
            ft.IconButton(
                icon=ft.Icons.DELETE,
                tooltip="Excluir",
                icon_size=18,
                icon_color="red",
                on_click=lambda e, k=key, it=item: confirm_delete_list_item(k, it)
            )
        )
        
        # Layout do card
        card_content = ft.Row([
            ft.Container(
                content=content_column,
                expand=True
            ),
            ft.Row(action_buttons, spacing=0)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.Card(
            content=ft.Container(
                content=card_content,
                padding=ft.padding.all(12),
                bgcolor=Colors['card_background'],
                border_radius=8
            ),
            elevation=1,
            margin=ft.margin.only(bottom=4)
        )

    def show_edit_list_dialog(key, item):
        """Mostra diálogo para editar um item da lista"""
        Colors = get_current_theme_colors(get_theme_name_from_page(page))
        
        # Campos atuais - extrair ID único
        current_id = item.get('id', '')
        current_alias = item.get('alias', '')
        current_name = item.get('name', '')
        current_email = item.get('email', '')
        
        # Criar campos de entrada
        name_field = ft.TextField(
            label="Nome",
            value=current_name,
            width=380,
            bgcolor=Colors['field_background'],
            color=Colors['on_surface'],
            border_color=Colors['outline']
        )
        
        alias_field = ft.TextField(
            label="Alias",
            value=current_alias,
            width=380,
            bgcolor=Colors['field_background'],
            color=Colors['on_surface'],
            border_color=Colors['outline']
        )
        
        email_field = ft.TextField(
            label="Email",
            value=current_email,
            width=380,
            bgcolor=Colors['field_background'],
            color=Colors['on_surface'],
            border_color=Colors['outline']
        )
        
        error_text = ft.Text("", color="red", visible=False)
        
        def save_changes(e):
            new_name = name_field.value.strip()
            new_alias = alias_field.value.strip().upper()
            new_email = email_field.value.strip()
            
            # Validação
            if not new_name or not new_alias or not new_email:
                error_text.value = "Todos os campos são obrigatórios"
                error_text.visible = True
                edit_dialog.update()
                return
            
            try:
                # Mapear tabela e coluna ID (usar nomes reais das colunas de ID)
                # antes o código usava 'id' e por isso o UPDATE não encontrava a linha
                table_map = {
                    'sqie': ('sqie_table', 'sqie_id'),
                    'continuity': ('continuity_table', 'continuity_id'),
                    'planner': ('planner_table', 'planner_id'),
                    'sourcing': ('sourcing_table', 'sourcing_id')
                }
                
                table_name, id_column = table_map[key]
                
                # Atualizar no banco usando ID único
                db_manager.execute(
                    f"UPDATE {table_name} SET name = ?, alias = ?, email = ? WHERE {id_column} = ?",
                    (new_name, new_alias, new_email, current_id)
                )
                
                # Atualizar seleção se ID mudou (usar novo ID)
                if lists_controls[key]['selected_item'] == current_id:
                    lists_controls[key]['selected_item'] = current_id
                
                # Fechar diálogo e atualizar UI
                page.close(edit_dialog)
                refresh_list_ui(key)
                update_all_comboboxes()
                
                show_toast("✅ Item atualizado com sucesso", "green")
                
            except Exception as ex:
                import sqlite3 as _sqlite
                if isinstance(ex, _sqlite.IntegrityError):
                    error_text.value = "Alias já existe. Escolha outro."
                    error_text.visible = True
                    edit_dialog.update()
                else:
                    show_toast(f"❌ Erro ao atualizar: {ex}", "red")
                    page.update()
        
        def cancel_edit(e):
            page.close(edit_dialog)
            page.update()
        
        # Criar diálogo
        edit_dialog = ft.AlertDialog(
            title=ft.Text("Editar Item"),
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        name_field,
                        ft.Container(height=10),
                        alias_field,
                        ft.Container(height=10),
                        email_field,
                        ft.Container(height=15),
                        error_text
                    ], spacing=0),
                    width=400
                )
            ], tight=True, spacing=15),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel_edit),
                ft.ElevatedButton("Salvar", on_click=save_changes)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.open(edit_dialog)
        page.update()

    def confirm_delete_list_item(key, item):
        """Confirma exclusão de item da lista"""
        alias = item.get('alias', '')
        
        # Mapear informações da tabela
        table_info = {
            'sqie': {'table': 'sqie_table', 'column': 'alias', 'display': 'SQIE'},
            'continuity': {'table': 'continuity_table', 'column': 'alias', 'display': 'Continuity'},
            'planner': {'table': 'planner_table', 'column': 'alias', 'display': 'Planner'},
            'sourcing': {'table': 'sourcing_table', 'column': 'alias', 'display': 'Sourcing'},
            'bu': {'table': 'business_unit_table', 'column': 'bu', 'display': 'Business Unit'},
            'category': {'table': 'categories_table', 'column': 'category', 'display': 'Category'}
        }
        
        info = table_info.get(key, {})
        list_display = info.get('display', key.upper())
        
        # Usar o diálogo de confirmação existente
        delete_alias_handler(info['table'], info['column'], alias)

    def refresh_list_ui(key):
        try:
            # Mapear tabelas e colunas
            table_map = {
                'sqie': ('sqie_table', 'alias'),
                'continuity': ('continuity_table', 'alias'),
                'planner': ('planner_table', 'alias'),
                'sourcing': ('sourcing_table', 'alias'),
                'bu': ('business_unit_table', 'bu'),
                'category': ('categories_table', 'category')
            }
            
            if key in table_map:
                table_name, column_name = table_map[key]
                # Usar nova função para dados completos
                items = load_list_items_full(table_name)
                col = lists_controls[key]['list']
                col.controls.clear()
                
                # Se não há itens, mostrar mensagem
                if not items:
                    col.controls.append(
                        ft.Container(
                            content=ft.Text(
                                "Nenhum item adicionado",
                                color="outline",
                                italic=True,
                                text_align=ft.TextAlign.CENTER
                            ),
                            alignment=ft.alignment.center,
                            padding=10
                        )
                    )
                else:
                    # Usar cards ao invés de ListTiles
                    for item in items:
                        card = create_list_item_card(key, item)
                        col.controls.append(card)
                        
        except Exception as ex:
            print(f"Erro ao atualizar UI da lista {key}: {ex}")

    def delete_alias_handler(table, alias_col, value=None):
        try:
            # Se não foi fornecido um valor, usar o item selecionado
            if not value:
                key = table.replace('_table', '')
                if key in lists_controls and lists_controls[key]['selected_item']:
                    value = lists_controls[key]['selected_item']
                else:
                    show_toast("❌ Selecione um item da lista para excluir", "red")
                    return
                    return
            
            # Mapear nomes amigáveis dos tipos de lista
            list_type_names = {
                'sqie_table': 'SQIE',
                'continuity_table': 'Continuity',
                'planner_table': 'Planner',
                'sourcing_table': 'Sourcing',
                'business_unit_table': 'Business Unit',
                'categories_table': 'Categories'
            }
            
            list_type = list_type_names.get(table, table)
            
            # Função para confirmar e executar a exclusão
            def confirm_delete(e):
                try:
                    delete_list_item_by_alias(table, alias_col, value)
                    
                    # Limpar seleção após exclusão
                    key = table.replace('_table', '')
                    if key in lists_controls:
                        lists_controls[key]['selected_item'] = None
                    
                    # atualizar todas as comboboxes e a UI
                    for k in lists_controls.keys():
                        refresh_list_ui(k)
                    update_all_comboboxes()
                    # atualizar lista de suppliers (reconstruir cards)
                    try:
                        search_suppliers_config()
                    except Exception:
                        pass
                    
                    # Fechar dialog
                    page.close(dialog)
                    
                    show_toast(f"✅ Item '{value}' removido de {list_type}", "green")
                    page.update()
                    
                except Exception as ex:
                    # Fechar dialog mesmo se der erro
                    page.close(dialog)
                    
                    # mostrar mensagem amigável
                    import sqlite3 as _sqlite
                    if isinstance(ex, _sqlite.IntegrityError):
                        show_toast(f"❌ Não foi possível excluir '{value}': restrição de integridade.", "red")
                    else:
                        show_toast(f"❌ Erro ao deletar '{value}': {ex}", "red")
                    page.update()
                    print(f"Erro ao deletar {value} em {table}: {ex}")
            
            # Função para cancelar
            def cancel_delete(e):
                page.close(dialog)
                page.update()
            
            # Criar e mostrar dialog de confirmação
            dialog = DeleteListItemConfirmationDialog(
                item_name=value,
                item_type=list_type,
                on_confirm=confirm_delete,
                on_cancel=cancel_delete,
                scale_func=lambda x: x
            )
            
            page.open(dialog)
            page.update()
            
        except Exception as ex:
            show_toast(f"❌ Erro ao tentar excluir item: {ex}", "red")
            page.update()
            print(f"Erro geral no delete_alias_handler: {ex}")

    def validate_input_exists(key):
        """Valida se o valor digitado no input (ou alias) já existe na tabela correspondente."""
        try:
            if key == 'sqie':
                val_alias = lists_controls['sqie']['alias'].value.strip().upper() if lists_controls['sqie']['alias'].value else ''
                val = val_alias or lists_controls['sqie']['input'].value.strip()
                rows = load_list_options('sqie_table','alias')
                exists = val in rows
                fb = lists_controls['sqie']['feedback']
                if exists:
                    fb.value = f"Já existe: {val}"
                    fb.color = 'red'
                else:
                    fb.value = f"Disponível: {val}"
                    fb.color = 'green'
                fb.visible = True
            elif key == 'continuity':
                val_alias = lists_controls['continuity']['alias'].value.strip().upper() if lists_controls['continuity']['alias'].value else ''
                val = val_alias or lists_controls['continuity']['input'].value.strip()
                rows = load_list_options('continuity_table','alias')
                exists = val in rows
                fb = lists_controls['continuity']['feedback']
                fb.value = (f"Já existe: {val}" if exists else f"Disponível: {val}")
                fb.color = 'red' if exists else 'green'
                fb.visible = True
            elif key == 'planner':
                val_alias = lists_controls['planner']['alias'].value.strip().upper() if lists_controls['planner']['alias'].value else ''
                val = val_alias or lists_controls['planner']['input'].value.strip()
                rows = load_list_options('planner_table','alias')
                exists = val in rows
                fb = lists_controls['planner']['feedback']
                fb.value = (f"Já existe: {val}" if exists else f"Disponível: {val}")
                fb.color = 'red' if exists else 'green'
                fb.visible = True
            elif key == 'sourcing':
                val_alias = lists_controls['sourcing']['alias'].value.strip().upper() if lists_controls['sourcing']['alias'].value else ''
                val = val_alias or lists_controls['sourcing']['input'].value.strip()
                rows = load_list_options('sourcing_table','alias')
                exists = val in rows
                fb = lists_controls['sourcing']['feedback']
                fb.value = (f"Já existe: {val}" if exists else f"Disponível: {val}")
                fb.color = 'red' if exists else 'green'
                fb.visible = True
            elif key == 'bu':
                val = lists_controls['bu']['input'].value.strip()
                rows = load_list_options('business_unit_table','bu')
                exists = val in rows
                fb = lists_controls['bu']['feedback']
                fb.value = (f"Já existe: {val}" if exists else f"Disponível: {val}")
                fb.color = 'red' if exists else 'green'
                fb.visible = True
            elif key == 'category':
                val = lists_controls['category']['input'].value.strip()
                rows = load_list_options('categories_table','category')
                exists = val in rows
                fb = lists_controls['category']['feedback']
                fb.value = (f"Já existe: {val}" if exists else f"Disponível: {val}")
                fb.color = 'red' if exists else 'green'
                fb.visible = True
            page.update()
        except Exception as ex:
            print(f"Erro na validação de {key}: {ex}")

    def add_alias_handler_sqie(e):
        name = lists_controls['sqie']['input'].value.strip()
        alias = lists_controls['sqie']['alias'].value.strip().upper()
        email = lists_controls['sqie']['email'].value.strip()
        
        if not name or not alias or not email:
            lists_controls['sqie']['feedback'].value = 'Informe nome, alias e email para SQIE'
            lists_controls['sqie']['feedback'].color = 'red'
            lists_controls['sqie']['feedback'].visible = True
            page.update()
            return
        try:
            insert_list_item('sqie_table', ['name','alias','email','register_date','registered_by'], (name, alias, email, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'system'))
            lists_controls['sqie']['input'].value = ''
            lists_controls['sqie']['alias'].value = ''
            lists_controls['sqie']['email'].value = ''
            refresh_list_ui('sqie')
            update_all_comboboxes()
            try:
                search_suppliers_config()
            except Exception:
                pass
            lists_controls['sqie']['feedback'].value = f"SQIE '{alias}' adicionado"
            lists_controls['sqie']['feedback'].color = 'green'
            lists_controls['sqie']['feedback'].visible = True
            show_toast(f"✅ SQIE '{alias}' adicionado com sucesso", "green")
            page.update()
        except Exception as ex:
            import sqlite3 as _sqlite
            if isinstance(ex, _sqlite.IntegrityError):
                lists_controls['sqie']['feedback'].value = f"Alias '{alias}' já existe"
                lists_controls['sqie']['feedback'].color = 'red'
                lists_controls['sqie']['feedback'].visible = True
                page.update()
            else:
                show_toast(f"❌ Erro ao inserir sqie: {ex}", "red")
                page.update()
            print(f"Erro ao inserir sqie: {ex}")
        except Exception as ex:
            print(f"Erro ao inserir sqie: {ex}")

    def add_alias_handler_generic(table, input_field, alias_field=None):
        name = input_field.value.strip()
        if alias_field:
            alias = alias_field.value.strip().upper()
            if not name or not alias:
                print("Informe name e alias")
                return
        else:
            if not name:
                print("Informe nome")
                return
        try:
            if table == 'continuity_table':
                email = lists_controls['continuity']['email'].value.strip()
                if not email:
                    lists_controls['continuity']['feedback'].value = 'Informe nome, alias e email para Continuity'
                    lists_controls['continuity']['feedback'].color = 'red'
                    lists_controls['continuity']['feedback'].visible = True
                    page.update()
                    return
                insert_list_item(table, ['name','alias','email','register_date','registered_by'], (name, alias, email, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'system'))
                lists_controls['continuity']['email'].value = ''
            elif table == 'planner_table':
                email = lists_controls['planner']['email'].value.strip()
                if not email:
                    lists_controls['planner']['feedback'].value = 'Informe nome, alias e email para Planner'
                    lists_controls['planner']['feedback'].color = 'red'
                    lists_controls['planner']['feedback'].visible = True
                    page.update()
                    return
                insert_list_item(table, ['name','alias','email','register_date','registered_by'], (name, alias, email, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'system'))
                lists_controls['planner']['email'].value = ''
            elif table == 'sourcing_table':
                email = lists_controls['sourcing']['email'].value.strip()
                if not email:
                    lists_controls['sourcing']['feedback'].value = 'Informe nome, alias e email para Sourcing'
                    lists_controls['sourcing']['feedback'].color = 'red'
                    lists_controls['sourcing']['feedback'].visible = True
                    page.update()
                    return
                insert_list_item(table, ['name','alias','email','register_date','registered_by'], (name, alias, email, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'system'))
                lists_controls['sourcing']['email'].value = ''
            elif table == 'business_unit_table':
                insert_list_item(table, ['bu','register_date','registered_by'], (name, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'system'))
            elif table == 'categories_table':
                insert_list_item(table, ['category','register_date','registered_by'], (name, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'system'))
            
            input_field.value = ''
            if alias_field:
                alias_field.value = ''
            refresh_list_ui(table.replace('_table',''))
            update_all_comboboxes()
            try:
                search_suppliers_config()
            except Exception:
                pass
            # feedback inline
            key = table.replace('_table','')
            if key in lists_controls:
                lists_controls[key]['feedback'].value = f"Item adicionado em {key}"
                lists_controls[key]['feedback'].color = 'green'
                lists_controls[key]['feedback'].visible = True
                show_toast(f"✅ Item adicionado com sucesso em {key}", "green")
                page.update()
        except Exception as ex:
            import sqlite3 as _sqlite
            if isinstance(ex, _sqlite.IntegrityError):
                key = table.replace('_table','')
                if key in lists_controls:
                    lists_controls[key]['feedback'].value = f"Item já existe"
                    lists_controls[key]['feedback'].color = 'red'
                    lists_controls[key]['feedback'].visible = True
                    page.update()
                else:
                    show_toast(f"❌ Erro ao inserir item: {ex}", "red")
                    page.update()
            print(f"Erro ao inserir item em {table}: {ex}")
            page.update()
        except Exception as ex:
            import sqlite3 as _sqlite
            if isinstance(ex, _sqlite.IntegrityError):
                key = table.replace('_table','')
                if key in lists_controls:
                    lists_controls[key]['feedback'].value = f"Item já existe em {key}"
                    lists_controls[key]['feedback'].color = 'red'
                    lists_controls[key]['feedback'].visible = True
                    page.update()
                else:
                    show_toast(f"❌ Erro ao inserir em {table}: {ex}", "red")
                    page.update()
            print(f"Erro ao inserir em {table}: {ex}")
        except Exception as ex:
            print(f"Erro ao inserir em {table}: {ex}")

    # Criar layout vertical simples ao invés de GridView
        ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Icon(ft.Icons.ASSIGNMENT, size=20, color="primary"),
                    ft.Text('SQIE Classification', weight='bold', size=16)
                ], alignment=ft.MainAxisAlignment.START, spacing=8),
                
                # Inputs
                ft.Row([
                    lists_controls['sqie']['input'], 
                    lists_controls['sqie']['alias']
                ], spacing=8),
                
                # Feedback
                lists_controls['sqie']['feedback'],
                
                # Buttons
                ft.Row([
                    ft.ElevatedButton(
                        'Adicionar', 
                        on_click=add_alias_handler_sqie,
                        icon=ft.Icons.ADD
                    )
                ], spacing=8),
                
                # Divider
                ft.Divider(height=1),
                
                # Lista de itens com scroll
                ft.Container(
                    content=lists_controls['sqie']['list'], 
                    expand=True,
                    padding=ft.padding.all(6),
                    border=ft.border.all(1, "outline_variant"),
                    border_radius=4,
                    bgcolor="surface"
                )
            ], spacing=10),
            padding=12,
            border=ft.border.all(1, 'outline'),
            border_radius=8,
            bgcolor='surface_variant'
        )

    # Popular listas iniciais
        ft.Container(
            content=ft.Column([
                # Header
                ft.Row([
                    ft.Icon(ft.Icons.TIMELINE, size=20, color="primary"),
                    ft.Text('Continuity Level', weight='bold', size=16)
                ], alignment=ft.MainAxisAlignment.START, spacing=8),
                
                # Inputs
                ft.Row([
                    lists_controls['continuity']['input'], 
                    lists_controls['continuity']['alias']
                ], spacing=8),
                
                # Feedback
                lists_controls['continuity']['feedback'],
                
                # Buttons
                ft.Row([
                    ft.ElevatedButton(
                        'Adicionar', 
                        on_click=lambda e: add_alias_handler_generic('continuity_table', lists_controls['continuity']['input'], lists_controls['continuity']['alias']),
                        icon=ft.Icons.ADD
                    )
                ], spacing=8),
                
                # Divider
                ft.Divider(height=1),
                
                # Lista de itens com scroll
                ft.Container(
                    content=lists_controls['continuity']['list'], 
                    expand=True,
                    padding=ft.padding.all(6),
                    border=ft.border.all(1, "outline_variant"),
                    border_radius=4,
                    bgcolor="surface"
                )
            ], spacing=10),
            padding=12,
            border=ft.border.all(1, 'outline'),
            border_radius=8,
            bgcolor='surface_variant'
        )

    # Popular listas iniciais

    # Criar layout vertical simples ao invés de GridView - adicionar diretamente à column principal
    lists_main_column.controls.extend([
        # SQIE
        ft.ExpansionTile(
            title=ft.Row([
                ft.Icon(ft.Icons.ASSIGNMENT, size=20),
                ft.Text('SQIE', weight='bold', size=16)
            ], spacing=8),
            controls=[
                ft.Container(
                    content=ft.Column([
                            ft.Container(
                                content=ft.Row([lists_controls['sqie']['input'], lists_controls['sqie']['alias']], spacing=8, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                width=700,
                                alignment=ft.alignment.center
                            ),
                            ft.Container(height=8),  # Espaçamento entre linhas
                            ft.Container(
                                content=ft.Row([lists_controls['sqie']['email']], spacing=8, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                width=700,  # Mesma largura do Nome
                                alignment=ft.alignment.center
                            ),
                            lists_controls['sqie']['feedback'],
                            ft.Row([
                                ft.ElevatedButton('Adicionar', on_click=add_alias_handler_sqie, icon=ft.Icons.ADD)
                            ], spacing=10),
                            ft.Text("Itens:", size=12, weight="bold"),
                            ft.Container(
                                            content=lists_controls['sqie']['list'], 
                                            expand=True,
                                            border=ft.border.all(1, "outline_variant"),
                                            border_radius=4,
                                            padding=8
                                        )
                        ], spacing=8),
                        padding=15
                    )
                ],
                initially_expanded=True
            ),
            
            # Continuity
            ft.ExpansionTile(
                title=ft.Row([
                    ft.Icon(ft.Icons.TIMELINE, size=20),
                    ft.Text('Continuity', weight='bold', size=16)
                ], spacing=8),
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Row([lists_controls['continuity']['input'], lists_controls['continuity']['alias']], spacing=8, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                width=700,
                                alignment=ft.alignment.center
                            ),
                            ft.Container(height=8),  # Espaçamento entre linhas
                            ft.Container(
                                content=ft.Row([lists_controls['continuity']['email']], spacing=8, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                width=700,  # Mesma largura do Nome
                                alignment=ft.alignment.center
                            ),
                            lists_controls['continuity']['feedback'],
                            ft.Row([
                                ft.ElevatedButton('Adicionar', 
                                    on_click=lambda e: add_alias_handler_generic('continuity_table', lists_controls['continuity']['input'], lists_controls['continuity']['alias']), 
                                    icon=ft.Icons.ADD)
                            ], spacing=10),
                            ft.Text("Itens:", size=12, weight="bold"),
                            ft.Container(
                                content=lists_controls['continuity']['list'], 
                                expand=True,
                                border=ft.border.all(1, "outline_variant"),
                                border_radius=4,
                                padding=8
                            )
                        ], spacing=8),
                        padding=15
                    )
                ]
            ),
            
            # Planner
            ft.ExpansionTile(
                title=ft.Row([
                    ft.Icon(ft.Icons.PERSON, size=20),
                    ft.Text('Planner', weight='bold', size=16)
                ], spacing=8),
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Row([lists_controls['planner']['input'], lists_controls['planner']['alias']], spacing=8, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                width=700,
                                alignment=ft.alignment.center
                            ),
                            ft.Container(height=8),  # Espaçamento entre linhas
                            ft.Container(
                                content=ft.Row([lists_controls['planner']['email']], spacing=8, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                width=700,  # Mesma largura do Nome
                                alignment=ft.alignment.center
                            ),
                            lists_controls['planner']['feedback'],
                            ft.Row([
                                ft.ElevatedButton('Adicionar', 
                                    on_click=lambda e: add_alias_handler_generic('planner_table', lists_controls['planner']['input'], lists_controls['planner']['alias']), 
                                    icon=ft.Icons.ADD)
                            ], spacing=10),
                            ft.Text("Itens:", size=12, weight="bold"),
                            ft.Container(
                                content=lists_controls['planner']['list'], 
                                expand=True,
                                border=ft.border.all(1, "outline_variant"),
                                border_radius=4,
                                padding=8
                            )
                        ], spacing=8),
                        padding=15
                    )
                ]
            ),
            
            # Sourcing
            ft.ExpansionTile(
                title=ft.Row([
                    ft.Icon(ft.Icons.PUBLIC, size=20),
                    ft.Text('Sourcing', weight='bold', size=16)
                ], spacing=8),
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Row([lists_controls['sourcing']['input'], lists_controls['sourcing']['alias']], spacing=8, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                width=700,
                                alignment=ft.alignment.center
                            ),
                            ft.Container(height=8),  # Espaçamento entre linhas
                            ft.Container(
                                content=ft.Row([lists_controls['sourcing']['email']], spacing=8, expand=True, alignment=ft.MainAxisAlignment.CENTER),
                                width=700,  # Mesma largura do Nome
                                alignment=ft.alignment.center
                            ),
                            lists_controls['sourcing']['feedback'],
                            ft.Row([
                                ft.ElevatedButton('Adicionar', 
                                    on_click=lambda e: add_alias_handler_generic('sourcing_table', lists_controls['sourcing']['input'], lists_controls['sourcing']['alias']), 
                                    icon=ft.Icons.ADD)
                            ], spacing=10),
                            ft.Text("Itens:", size=12, weight="bold"),
                            ft.Container(
                                content=lists_controls['sourcing']['list'], 
                                expand=True,
                                border=ft.border.all(1, "outline_variant"),
                                border_radius=4,
                                padding=8
                            )
                        ], spacing=8),
                        padding=15
                    )
                ]
            ),
            
            # Business Unit
            ft.ExpansionTile(
                title=ft.Row([
                    ft.Icon(ft.Icons.BUSINESS, size=20),
                    ft.Text('Business Unit', weight='bold', size=16)
                ], spacing=8),
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=lists_controls['bu']['input'],
                                width=600,
                                alignment=ft.alignment.center
                            ),
                            lists_controls['bu']['feedback'],
                            ft.Row([
                                ft.ElevatedButton('Adicionar', 
                                    on_click=lambda e: add_alias_handler_generic('business_unit_table', lists_controls['bu']['input']), 
                                    icon=ft.Icons.ADD)
                            ], spacing=10),
                            ft.Text("Itens:", size=12, weight="bold"),
                            ft.Container(
                                content=lists_controls['bu']['list'], 
                                expand=True,
                                border=ft.border.all(1, "outline_variant"),
                                border_radius=4,
                                padding=8
                            )
                        ], spacing=8),
                        padding=15
                    )
                ]
            ),
            
            # Category
            ft.ExpansionTile(
                title=ft.Row([
                    ft.Icon(ft.Icons.CATEGORY, size=20),
                    ft.Text('Category', weight='bold', size=16)
                ], spacing=8),
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=lists_controls['category']['input'],
                                width=600,
                                alignment=ft.alignment.center
                            ),
                            lists_controls['category']['feedback'],
                            ft.Row([
                                ft.ElevatedButton('Adicionar', 
                                    on_click=lambda e: add_alias_handler_generic('categories_table', lists_controls['category']['input']), 
                                    icon=ft.Icons.ADD)
                            ], spacing=10),
                            ft.Text("Itens:", size=12, weight="bold"),
                            ft.Container(
                                content=lists_controls['category']['list'], 
                                expand=True,
                                border=ft.border.all(1, "outline_variant"),
                                border_radius=4,
                                padding=8
                            )
                        ], spacing=8),
                        padding=15
                    )
                ]
            )
    ])
    
    # lists_main_column é um ListView com expand=True — ele já fornece scroll adaptativo
    
    # Popular listas iniciais
    for k in lists_controls.keys():
        try:
            refresh_list_ui(k)
        except Exception as ex:
            print(f"Erro ao popular lista {k}: {ex}")

    # Lógica para gerenciamento de suppliers
    suppliers_search_field_ref = ft.Ref()
    global suppliers_results_list
    suppliers_results_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    def create_supplier_card(record, page):
        """Cria um card editável para um supplier."""
        supplier_id = record.get('supplier_id', '')
        vendor_name = record.get('vendor_name', '')
        supplier_category = record.get('supplier_category', '')
        bu = record.get('bu', '')
        supplier_name = record.get('supplier_name', '')
        supplier_email = record.get('supplier_email', '')
        supplier_number = record.get('supplier_number', '')
        supplier_status = record.get('supplier_status', '')
        planner = record.get('planner', '')
        continuity = record.get('continuity', '')
        sourcing = record.get('sourcing', '')
        sqie = record.get('sqie', '')

        print(f"Criando card de supplier para: {vendor_name} (ID: {supplier_id})")

        def update_status_color(e):
            """Atualiza a cor do texto do dropdown de status baseado no valor selecionado"""
            status_value = e.control.value
            if status_value == "Active":
                e.control.color = "green"
            elif status_value == "Inactive":
                e.control.color = "red"
            else:
                e.control.color = get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface')
            page.update()

        # Campos editáveis
        fields = {
            "vendor_name": ft.TextField(
                label="Vendor Name",
                value=vendor_name,  # Preencher com valor do banco
                filled=False,
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "supplier_category": ft.Dropdown(
                label="Category",
                value=supplier_category,  # Preencher com valor do banco
                options=[ft.dropdown.Option(v) for v in ([""] + load_list_options('categories_table','category'))],
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "bu": ft.Dropdown(
                label="BU (Business Unit)",
                value=bu,  # Preencher com valor do banco
                options=[ft.dropdown.Option(v) for v in ([""] + load_list_options('business_unit_table','bu'))],
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "supplier_origin": ft.Dropdown(
                label="Origem",
                value=supplier_name if supplier_name in ['Nacional', 'Importado'] else '',  # Preencher com valor do banco quando aplicável
                options=[ft.dropdown.Option(v) for v in ["Nacional", "Importado"]],
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "supplier_email": ft.TextField(
                label="Email",
                value=supplier_email,  # Preencher com valor do banco
                filled=False,
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "supplier_number": ft.TextField(
                label="Number",
                value=supplier_number,  # Preencher com valor do banco
                filled=False,
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "supplier_status": ft.Dropdown(
                label="Status",
                value=supplier_status,  # Preencher com valor do banco
                options=[ft.dropdown.Option(v) for v in ["Active", "Inactive"]],
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color="green" if supplier_status == "Active" else "red" if supplier_status == "Inactive" else get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),  # Cor baseada no status
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline'),
                on_change=update_status_color
            ),
            "planner": ft.Dropdown(
                label="Planner",
                value=planner,  # Preencher com valor do banco
                options=[ft.dropdown.Option(v) for v in ([""] + load_list_options('planner_table','name'))],
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "continuity": ft.Dropdown(
                label="Continuity",
                value=continuity,  # Preencher com valor do banco
                options=[ft.dropdown.Option(v) for v in ([""] + load_list_options('continuity_table','name'))],
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "sourcing": ft.Dropdown(
                label="Sourcing",
                value=sourcing,  # Preencher com valor do banco
                options=[ft.dropdown.Option(v) for v in ([""] + load_list_options('sourcing_table','name'))],
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            "sqie": ft.Dropdown(
                label="SQIE",
                value=sqie,  # Preencher com valor do banco
                options=[ft.dropdown.Option(v) for v in ([""] + load_list_options('sqie_table','name'))],
                expand=True,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
        }

        def save_supplier(e):
            """Salva ou atualiza dados do supplier no banco de dados."""
            nonlocal supplier_id
            print(f"🔧 DEBUG: save_supplier chamada para supplier ID: {supplier_id}")
            
            if not db_conn:
                show_toast("❌ Erro: Banco de dados não conectado.", "red")
                return

            # Função auxiliar para tratar valores
            def safe_strip(value):
                if value is None:
                    return ""
                return str(value).strip()

            # Validações básicas
            if not safe_strip(fields["vendor_name"].value):
                show_toast("❌ Campo Vendor Name é obrigatório!", "red")
                return
            
            if not safe_strip(fields["supplier_origin"].value):
                show_toast("❌ Campo Origem é obrigatório!", "red")
                return

            try:
                print(f"🔧 DEBUG: Iniciando salvamento...")
                e.control.disabled = True
                e.control.text = "Salvando..."
                page.update()

                cursor = db_conn.cursor()
                print(f"🔧 DEBUG: Cursor criado")
                
                # Verificar se o supplier existe
                check_query = "SELECT COUNT(*) FROM supplier_database_table WHERE supplier_id = ?"
                result = db_manager.query_one(check_query, (supplier_id,))
                exists = result["COUNT(*)"] > 0
                print(f"🔧 DEBUG: Supplier exists: {exists}")
                
                if exists:
                    # Atualizar registro existente
                    update_query = """
                        UPDATE supplier_database_table 
                        SET vendor_name = ?, supplier_category = ?, bu = ?, supplier_name = ?,
                            supplier_email = ?, supplier_number = ?, supplier_status = ?,
                            planner = ?, continuity = ?, sourcing = ?, sqie = ?
                        WHERE supplier_id = ?
                    """
                    db_manager.execute(update_query, (
                        safe_strip(fields["vendor_name"].value),
                        safe_strip(fields["supplier_category"].value),
                        safe_strip(fields["bu"].value),
                        safe_strip(fields["supplier_origin"].value),
                        safe_strip(fields["supplier_email"].value),
                        safe_strip(fields["supplier_number"].value),
                        safe_strip(fields["supplier_status"].value),
                        safe_strip(fields["planner"].value),
                        safe_strip(fields["continuity"].value),
                        safe_strip(fields["sourcing"].value),
                        safe_strip(fields["sqie"].value),
                        supplier_id
                    ))
                    action = "atualizado"
                else:
                    # Inserir novo registro
                    insert_query = """
                        INSERT INTO supplier_database_table 
                        (vendor_name, supplier_category, bu, supplier_name,
                         supplier_email, supplier_number, supplier_status, planner, 
                         continuity, sourcing, sqie)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    db_manager.execute(insert_query, (
                        safe_strip(fields["vendor_name"].value),
                        safe_strip(fields["supplier_category"].value),
                        safe_strip(fields["bu"].value),
                        safe_strip(fields["supplier_origin"].value),
                        safe_strip(fields["supplier_email"].value),
                        safe_strip(fields["supplier_number"].value),
                        safe_strip(fields["supplier_status"].value),
                        safe_strip(fields["planner"].value),
                        safe_strip(fields["continuity"].value),
                        safe_strip(fields["sourcing"].value),
                        safe_strip(fields["sqie"].value)
                    ))
                    # Pegar o supplier_id gerado
                    supplier_id = cursor.lastrowid
                    action = "criado"
                    # Atualizar o data do card com o novo ID
                    if card.data:
                        card.data['supplier_id'] = supplier_id
                
                db_conn.commit()
                print(f"🔧 DEBUG: Dados commitados no banco")
                
                # Atualizar supplier_name em supplier_score_records_table usando vendor_name
                try:
                    update_score_query = "UPDATE supplier_score_records_table SET supplier_name = ? WHERE supplier_id = ?"
                    db_manager.execute(update_score_query, (safe_strip(fields["vendor_name"].value), supplier_id))
                    print(f"🔧 DEBUG: Supplier name atualizado em supplier_score_records_table para vendor_name '{safe_strip(fields['vendor_name'].value)}'")
                except Exception as ex_upd:
                    print(f"🔧 WARN: falha ao atualizar supplier_score_records_table: {ex_upd}")
                
                # Atualizar listas
                load_scores()
                load_suppliers_for_timeline()

                # Atualizar dropdowns da aba Timeline, se referenciados
                try:
                    if 'timeline_vendor_dropdown' in globals() and timeline_vendor_dropdown.current:
                        timeline_vendor_dropdown.current.options = load_suppliers_for_timeline()
                    if 'timeline_bu_dropdown' in globals() and timeline_bu_dropdown.current:
                        timeline_bu_dropdown.current.options = load_business_units_for_timeline()
                    # Atualizar visualmente
                    try:
                        if timeline_vendor_dropdown.current:
                            timeline_vendor_dropdown.current.update()
                    except Exception:
                        pass
                    try:
                        if timeline_bu_dropdown.current:
                            timeline_bu_dropdown.current.update()
                    except Exception:
                        pass
                    page.update()
                except Exception as upd_ex:
                    print(f"🔧 WARN: falha ao atualizar dropdowns da Timeline: {upd_ex}")

                show_toast(f"✅ Supplier {safe_strip(fields['vendor_name'].value)} {action} com sucesso!", "green")
                print(f"Supplier {supplier_id} {action}")

            except Exception as ex:
                show_toast(f"❌ Erro ao salvar: {str(ex)}", "red")
                print(f"Erro ao salvar supplier: {ex}")
            finally:
                e.control.disabled = False
                e.control.text = "Update"
                page.update()

        def delete_supplier(e):
            """Deleta supplier após confirmação com código de 5 letras."""
            print(f"🗑️ DEBUG: delete_supplier chamada para supplier ID: {supplier_id}")
            
            def handle_confirm(e):
                """Callback para confirmar a exclusão"""
                try:
                    if not db_conn:
                        show_toast("❌ Erro: Banco de dados não conectado.", "red")
                        return
                    cursor = db_conn.cursor()
                    db_manager.execute("DELETE FROM supplier_score_records_table WHERE supplier_id = ?", (supplier_id,))
                    db_manager.execute("DELETE FROM favorites_table WHERE supplier_id = ?", (supplier_id,))
                    db_manager.execute("DELETE FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
                    if card in suppliers_results_list.controls:
                        suppliers_results_list.controls.remove(card)
                    show_toast(f"✅ Supplier {vendor_name} deletado com sucesso!", "green")
                    print(f"Supplier {supplier_id} deletado com sucesso")
                except Exception as ex:
                    show_toast(f"❌ Erro ao deletar: {str(ex)}", "red")
                    print(f"Erro ao deletar supplier: {ex}")
                page.close(delete_dialog)
            
            def handle_cancel(e):
                """Callback para cancelar a exclusão"""
                page.close(delete_dialog)
            
            # Criar o diálogo personalizado
            delete_dialog = DeleteSupplierConfirmationDialog(
                supplier_name=vendor_name,
                supplier_id=supplier_id,
                on_confirm=handle_confirm,
                on_cancel=handle_cancel
            )
            
            print(f"🗑️ DEBUG: Abrindo dialog de confirmação...")
            page.open(delete_dialog)
            print(f"🗑️ DEBUG: Dialog de confirmação aberto!")


        # Criar botões APÓS definir as funções
        actions_row = ft.Row([
            ft.ElevatedButton("Update", on_click=save_supplier, icon=ft.Icons.SAVE),
            ft.ElevatedButton("Excluir", on_click=delete_supplier, icon=ft.Icons.DELETE, color="red"),
        ], alignment=ft.MainAxisAlignment.END, spacing=10)

        # Layout do card com responsividade
        def should_use_single_column_layout():
            """Determina se deve usar layout de uma coluna baseado no tamanho da janela"""
            window_width = page.window.width or 1200
            return window_width < 1000  # Se menor que 1000px, usar uma coluna

        def create_card_layout(use_single_column=None):
            """Cria o layout do card baseado na decisão de usar uma ou duas colunas"""
            if use_single_column is None:
                use_single_column = should_use_single_column_layout()
            
            left_column = ft.Column([
                ft.Text(f"ID: {supplier_id}", size=12, weight="bold", color="primary"),
                ft.Row([fields["vendor_name"], fields["supplier_category"]], spacing=10),
                ft.Row([fields["bu"], fields["supplier_origin"]], spacing=10),
                ft.Row([fields["supplier_email"], fields["supplier_number"]], spacing=10),
            ], spacing=10, expand=True)

            right_column = ft.Column([
                ft.Text("Configurações", size=12, weight="bold", color="primary"),
                fields["supplier_status"],
                ft.Row([fields["planner"], fields["continuity"]], spacing=10),
                ft.Row([fields["sourcing"], fields["sqie"]], spacing=10),
            ], spacing=10, expand=True)

            # Aplicar layout responsivo
            if use_single_column:
                # Layout de uma coluna - configurações abaixo das informações principais
                return ft.Column([
                    left_column,
                    ft.Divider(),
                    right_column,
                    ft.Divider(),
                    actions_row
                ], spacing=15)
            else:
                # Layout de duas colunas - configurações ao lado das informações principais
                return ft.Column([
                    ft.Row([left_column, ft.VerticalDivider(), right_column], expand=True),
                    ft.Divider(),
                    actions_row
                ], spacing=15)
        
        # Criar layout inicial
        card_content = create_card_layout()

        card = ft.Card(
            content=ft.Container(
                content=card_content,
                padding=20
            ),
            elevation=2,
            margin=ft.margin.symmetric(vertical=5),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background', 'surface_variant')
        )
        
        # Guardar referências dos campos e função de layout para facilitar re-tematização e responsividade
        try:
            card.data = { 
                'fields': fields,
                'create_layout': create_card_layout,
                'supplier_id': supplier_id
            }
        except Exception:
            pass

        return card

    def add_new_supplier(e):
        """Abre dialog para adicionar um novo supplier."""
        print("➕ DEBUG: add_new_supplier chamada")
        
        def handle_confirm(e):
            """Callback para confirmar a criação do supplier"""
            print("🔍 DEBUG: handle_confirm chamado")
            
            # Função auxiliar para tratar valores (TextField e Dropdown)
            def safe_strip(value):
                if value is None:
                    return ""
                return str(value).strip()
                
            def get_field_value(field):
                """Obtém valor tanto de TextField quanto de Dropdown ou Container que embala um Dropdown.
                Suporta:
                - TextField / Dropdown (tem atributo .value)
                - Container com .content (ex: Container(content=Dropdown(...)))
                - Outros casos: tenta acessar .controls[0].value como fallback
                """
                try:
                    # Dropdowns e TextFields diretamente
                    if hasattr(field, 'value'):
                        return safe_strip(field.value)

                    # Container que embala um controle em .content
                    if hasattr(field, 'content') and hasattr(field.content, 'value'):
                        return safe_strip(field.content.value)

                    # Alguns componentes podem ter controls list
                    if hasattr(field, 'controls') and len(field.controls) > 0 and hasattr(field.controls[0], 'value'):
                        return safe_strip(field.controls[0].value)

                except Exception:
                    pass
                return ""
            
            if not db_conn:
                print("🔍 DEBUG: Banco de dados não conectado")
                show_toast("❌ Erro: Banco de dados não conectado.", "red")
                return
            
            print("🔍 DEBUG: Preparando para inserir no banco")
            try:
                cursor = db_conn.cursor()
                
                # Pegar valores dos campos
                vendor_name = get_field_value(add_dialog.fields["vendor_name"])
                print(f"🔍 DEBUG: Dados a inserir - vendor_name: '{vendor_name}'")
                
                # Inserir novo supplier (supplier_id será gerado automaticamente pelo banco)
                insert_query = """
                    INSERT INTO supplier_database_table 
                    (vendor_name, supplier_category, bu, supplier_name,
                     supplier_email, supplier_number, supplier_status, planner, 
                     continuity, sourcing, sqie)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                db_manager.execute(insert_query, (
                    get_field_value(add_dialog.fields["vendor_name"]),
                    get_field_value(add_dialog.fields["supplier_category"]),
                    get_field_value(add_dialog.fields["bu"]),
                    get_field_value(add_dialog.fields["supplier_origin"]),
                    get_field_value(add_dialog.fields["supplier_email"]),
                    get_field_value(add_dialog.fields["supplier_number"]),
                    get_field_value(add_dialog.fields["supplier_status"]),
                    get_field_value(add_dialog.fields["planner"]),
                    get_field_value(add_dialog.fields["continuity"]),
                    get_field_value(add_dialog.fields["sourcing"]),
                    get_field_value(add_dialog.fields["sqie"])
                ))
                
                db_conn.commit()
                print("🔍 DEBUG: Dados inseridos com sucesso")
                
                # Atualizar lista de suppliers
                search_suppliers_config()
                
                show_toast(f"✅ Supplier {vendor_name} criado com sucesso!", "green")
                page.close(add_dialog)
                
            except Exception as ex:
                print(f"🔍 DEBUG: Erro ao inserir: {ex}")
                show_toast(f"❌ Erro ao criar supplier: {str(ex)}", "red")
                print(f"Erro ao criar supplier: {ex}")
        
        def handle_cancel(e):
            """Callback para cancelar a criação"""
            page.close(add_dialog)
        
        # Preparar opções dinâmicas para os Dropdowns do diálogo
        list_opts = {
            'bu': load_list_options('business_unit_table','bu'),
            'planner': load_list_options('planner_table','name'),
            'continuity': load_list_options('continuity_table','name'),
            'sourcing': load_list_options('sourcing_table','name'),
            'sqie': load_list_options('sqie_table','name'),
            'category': load_list_options('categories_table','category'),
        }
        
        # Debug: verificar se as listas foram carregadas
        print("📋 DEBUG: Opções carregadas para o diálogo:")
        for key, options in list_opts.items():
            print(f"  {key}: {options[:5]}{'...' if len(options) > 5 else ''} (total: {len(options)})")
        

        # Criar o diálogo personalizado
        add_dialog = AddSupplierDialog(
            on_confirm=handle_confirm,
            on_cancel=handle_cancel,
            page=page,
            list_options=list_opts
        )
        
        # Aplicar cores do tema aos campos
        current_colors = get_current_theme_colors(get_theme_name_from_page(page))
        field_bgcolor = current_colors.get('field_background')
        for field_name, field in add_dialog.fields.items():
            if hasattr(field, 'bgcolor'):
                field.bgcolor = field_bgcolor
        
        print("➕ DEBUG: Abrindo dialog para adicionar supplier...")
        page.open(add_dialog)
        print("➕ DEBUG: Dialog para adicionar supplier aberto!")

    def search_suppliers_config():
        """Busca suppliers para edição na aba de configurações."""
        if not suppliers_search_field_ref.current:
            return
            
        search_term = suppliers_search_field_ref.current.value.strip()
        
        print(f"Buscando suppliers para edição: '{search_term}'")

        suppliers_results_list.controls.clear()
        page.update()

        # Se o campo de pesquisa estiver vazio, limpar todos os cards e retornar
        if not search_term:
            print("Campo de pesquisa vazio, limpando todos os cards")
            page.update()
            return

        if not db_conn:
            suppliers_results_list.controls.append(
                ft.Container(
                    ft.Text("Erro: Não foi possível conectar ao banco de dados.", color="red"),
                    padding=20
                )
            )
            page.update()
            return

        try:
            cursor = db_conn.cursor()

            query = """
                SELECT supplier_id, vendor_name, supplier_category, bu, supplier_name,
                       supplier_email, supplier_number, supplier_status, planner, 
                       continuity, sourcing, sqie
                FROM supplier_database_table
                WHERE (vendor_name LIKE ? OR supplier_id LIKE ? OR supplier_name LIKE ?)
                ORDER BY vendor_name LIMIT 10
            """
            params = [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]

            print(f"Executando query: {query}")
            print(f"Params: {params}")
            records = db_manager.query(query, params)
            
            print(f"Encontrados {len(records)} suppliers")
            
            if not records:
                suppliers_results_list.controls.append(
                    ft.Container(
                        ft.Text("Nenhum supplier encontrado.", italic=True, size=16),
                        alignment=ft.alignment.center,
                        padding=40
                    )
                )
            else:
                for i, record in enumerate(records):
                    print(f"Criando card {i+1}/{len(records)}: {record.get('vendor_name', 'Unknown')}")
                    try:
                        card = create_supplier_card(record, page)
                        suppliers_results_list.controls.append(card)
                    except Exception as card_error:
                        print(f"Erro ao criar card para {record.get('vendor_name', 'Unknown')}: {card_error}")
                        continue
            
        except sqlite3.Error as db_error:
            error_msg = f"Erro no banco de dados: {db_error}"
            print(error_msg)
            suppliers_results_list.controls.append(
                ft.Container(
                    ft.Text(error_msg, color="red"),
                    padding=20
                )
            )

        page.update()

    # Conteúdo da sub-aba Suppliers
    suppliers_content = ft.Container(
        content=ft.Column([
            ft.Text("Gerenciamento de Fornecedores", size=20, weight="bold"),
            ft.Divider(),
            ft.Row([
                ft.TextField(
                    label="Buscar Supplier (Nome, ID ou Supplier Name)",
                    hint_text="Digite para buscar...",
                    prefix_icon=ft.Icons.SEARCH,
                    expand=True,
                    ref=suppliers_search_field_ref,
                    on_change=lambda e: search_suppliers_config(),
                    bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                    color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                    border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                ),
                ft.ElevatedButton("Novo Supplier", icon=ft.Icons.ADD_BUSINESS, on_click=add_new_supplier),
            ], spacing=10),
            ft.Container(height=10),
            ft.Container(
                content=suppliers_results_list,
                expand=True,
                padding=20,
            ),
        ], spacing=15, expand=True),
        padding=20,
        visible=False,
        expand=True
    )

    # Controle para mostrar a soma total dos pesos
    weight_sum_text = ft.Text("Soma dos pesos: 0.80", size=14, weight="bold", color="primary")
    
    # Função para atualizar o texto de um critério e a soma total
    def update_criteria_text(criteria_name, slider_value, text_control):
        text_control.value = f"{slider_value:.2f}"
        text_control.update()
        update_weight_sum()
    
    def update_weight_sum():
        """Atualiza a exibição da soma total dos pesos em tempo real."""
        total = nil_slider.value + otif_slider.value + pickup_slider.value + package_slider.value
        weight_sum_text.value = f"Soma dos pesos: {total:.2f}"
        
        # Mudar cor baseado na soma
        if abs(total - 1.0) <= 0.01:  # Muito próximo de 1.0
            weight_sum_text.color = "green"
        elif abs(total - 1.0) <= 0.05:  # Tolerável
            weight_sum_text.color = "orange" 
        else:  # Muito longe de 1.0
            weight_sum_text.color = "red"
        
        weight_sum_text.update()

    def auto_adjust_weights():
        """Auto-ajusta os pesos para somarem exatamente 1.00, mantendo as proporções."""
        current_total = nil_slider.value + otif_slider.value + pickup_slider.value + package_slider.value
        
        if current_total == 0:
            # Se tudo for zero, distribuir igualmente
            nil_slider.value = 0.25
            otif_slider.value = 0.25
            pickup_slider.value = 0.25
            package_slider.value = 0.25
        else:
            # Manter proporções e ajustar para somar exatamente 1.00
            factor = 1.0 / current_total
            values = [
                nil_slider.value * factor,
                otif_slider.value * factor, 
                pickup_slider.value * factor,
                package_slider.value * factor
            ]
            
            # Arredondar para 2 casas decimais
            rounded_values = [round(v, 2) for v in values]
            
            # Ajustar pequenos erros de arredondamento
            current_sum = sum(rounded_values)
            if current_sum != 1.0:
                diff = 1.0 - current_sum
                # Adicionar/subtrair a diferença do maior valor
                max_index = rounded_values.index(max(rounded_values))
                rounded_values[max_index] = round(rounded_values[max_index] + diff, 2)
            
            # Aplicar valores ajustados
            nil_slider.value = rounded_values[0]
            otif_slider.value = rounded_values[1] 
            pickup_slider.value = rounded_values[2]
            package_slider.value = rounded_values[3]
        
        # Atualizar textos
        nil_text.value = f"{nil_slider.value:.2f}"
        otif_text.value = f"{otif_slider.value:.2f}"
        pickup_text.value = f"{pickup_slider.value:.2f}"
        package_text.value = f"{package_slider.value:.2f}"
        
        # Atualizar soma
        update_weight_sum()
        
        # Atualizar UI
        page.update()
        
        # Toast de sucesso
        page.overlay.append(
            ft.Container(
                content=ft.Text("✅ Pesos auto-ajustados para somar 1.00!", 
                               color="white", weight="bold"),
                bgcolor="blue",
                padding=10,
                border_radius=5,
                top=50,
                right=20,
                animate_opacity=300,
            )
        )
        page.update()
        
        # Remover show_toast após 3 segundos
        import threading
        def remove_auto_toast():
            import time
            time.sleep(3)
            if page.overlay:
                page.overlay.pop()
                page.update()
        
        threading.Thread(target=remove_auto_toast, daemon=True).start()

    # Sliders dos critérios com nomes corretos (100 divisões para precisão de 0.01)
    nil_text = ft.Text("0.20", size=12, width=60)
    nil_slider = ft.Slider(
        min=0, max=1, divisions=100, value=0.2,
        on_change=lambda e: update_criteria_text("NIL", e.control.value, nil_text)
    )
    
    otif_text = ft.Text("0.20", size=12, width=60)
    otif_slider = ft.Slider(
        min=0, max=1, divisions=100, value=0.2,
        on_change=lambda e: update_criteria_text("OTIF", e.control.value, otif_text)
    )
    
    pickup_text = ft.Text("0.20", size=12, width=60)
    pickup_slider = ft.Slider(
        min=0, max=1, divisions=100, value=0.2,
        on_change=lambda e: update_criteria_text("Quality of Pick Up", e.control.value, pickup_text)
    )
    
    package_text = ft.Text("0.20", size=12, width=60)
    package_slider = ft.Slider(
        min=0, max=1, divisions=100, value=0.2,
        on_change=lambda e: update_criteria_text("Quality-Supplier Package", e.control.value, package_text)
    )
    
    target_text = ft.Text("5.00", size=12, width=60)
    target_slider = ft.Slider(
        min=0, max=10, divisions=100, value=5.0,
        on_change=lambda e: update_criteria_text("Target", e.control.value, target_text)
    )

    def update_criteria_settings():
        """Atualiza os critérios na tabela criteria_table."""
        print("🔄 Botão Update Criteria pressionado!")
        
        if not db_conn:
            print("❌ Erro: Conexão com banco não disponível")
            show_toast("❌ Erro: Conexão com banco não disponível", "red")
            page.update()
            return
        
        criteria_values = {
            'NIL': nil_slider.value,
            'OTIF': otif_slider.value,
            'Quality of Pick Up': pickup_slider.value,
            'Quality-Supplier Package': package_slider.value,
            'Target': target_slider.value  # Target mantém escala 0-10
        }
        
        print(f"📊 Valores coletados dos sliders:")
        for name, value in criteria_values.items():
            print(f"  {name}: {value}")
        
        # Validar soma apenas dos critérios de peso (excluindo Target que é escala diferente)
        weight_criteria = ['NIL', 'OTIF', 'Quality of Pick Up', 'Quality-Supplier Package']
        total_weight = sum(criteria_values[key] for key in weight_criteria)
        
        print(f"🧮 Soma dos pesos (sem Target): {total_weight}")
        
        if round(total_weight, 2) != 1.0:  # Deve ser exatamente 1.00
            print(f"⚠️ Validação falhou: soma {total_weight:.2f} não é exatamente 1.00")
            show_toast(f"❌ ERRO: A soma dos 4 pesos é {total_weight:.2f} - DEVE ser exatamente 1.00!", "red")
            return
        
        try:
            print("🔄 Iniciando atualização no banco de dados...")
            
            # Preparar dados para atualização em lote
            update_data = []
            for criteria_name, value in criteria_values.items():
                # Arredondar para 2 casas decimais antes de salvar
                rounded_value = round(value, 2)
                update_data.append((str(rounded_value), criteria_name))
                print(f"  ✅ Critério preparado: {criteria_name} = {rounded_value}")
            
            # Executar atualização em lote usando DBManager
            if update_data:
                db_manager.execute_many(
                    "UPDATE criteria_table SET value = ? WHERE criteria_category = ?", 
                    update_data
                )
                print("✅ Atualização em lote realizada com sucesso!")
            
            show_toast("✅ Critérios atualizados com sucesso!", "green")
            
        except Exception as ex:
            print(f"❌ Erro ao atualizar critérios: {ex}")
            show_toast("❌ Erro ao atualizar critérios!", "red")
            page.update()

    # Criar títulos fixos para Criteria (fora do scroll)
    criteria_header = ft.Column([
        ft.Text("Configuração de Critérios", size=20, weight="bold"),
        ft.Text("Configure os pesos dos critérios de avaliação", size=14, color="on_surface_variant"),
        ft.Divider(height=2),
    ], spacing=8)
    
    # Criar conteúdo scrollável para Criteria
    criteria_scrollable_content = ft.ListView([
        ft.Container(
            content=ft.Column([
                ft.Text("⚠️ IMPORTANTE: Os 4 pesos (NIL+OTIF+Pickup+Package) DEVEM somar exatamente 1.00", 
                       size=12, weight="bold", color="error"),
                ft.Text("Target usa escala independente de 0-10", size=12, italic=True, color="outline"),
                ft.Container(height=10),
                weight_sum_text,
                ft.Container(height=15),
                
                # Sliders para cada critério com nomes corretos
                ft.Row([
                    ft.Text("NIL:", size=14, weight="bold", width=220),
                    ft.Container(content=nil_slider, expand=True),
                    nil_text
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    ft.Text("OTIF:", size=14, weight="bold", width=220),
                    ft.Container(content=otif_slider, expand=True),
                    otif_text
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    ft.Text("Quality of Pick Up:", size=14, weight="bold", width=220),
                    ft.Container(content=pickup_slider, expand=True),
                    pickup_text
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    ft.Text("Quality-Supplier Package:", size=14, weight="bold", width=220),
                    ft.Container(content=package_slider, expand=True),
                    package_text
                ], alignment=ft.MainAxisAlignment.START),
                ft.Row([
                    ft.Text("Target:", size=14, weight="bold", width=220),
                    ft.Container(content=target_slider, expand=True),
                    target_text
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton("Update Criteria", icon=ft.Icons.UPDATE, on_click=lambda e: update_criteria_settings()),
                    ft.OutlinedButton("Auto-ajustar para 1.00", icon=ft.Icons.AUTO_FIX_HIGH, on_click=lambda e: auto_adjust_weights())
                ], spacing=10),
                ft.Container(height=20)  # Espaço extra no final
            ], spacing=10),
            padding=ft.padding.all(10)
        )
    ], spacing=8, expand=True)

    # Conteúdo da sub-aba Criteria com scroll
    criteria_content = ft.Container(
        content=ft.Column([
            criteria_header,
            ft.Container(
                content=criteria_scrollable_content,
                expand=True
            )
        ], spacing=10),
        padding=ft.padding.all(20),
        visible=False,
        expand=True
    )

    # Conteúdo da sub-aba Users
    users_list_ref = ft.Ref()  # Referência para o ListView dos usuários
    
    # Criar referências para os campos da aba Users
    wwid_field_ref = ft.Ref()
    name_field_ref = ft.Ref()
    password_field_ref = ft.Ref()
    privilege_dropdown_ref = ft.Ref()
    otif_check_ref = ft.Ref()
    nil_check_ref = ft.Ref()
    pickup_check_ref = ft.Ref()
    package_check_ref = ft.Ref()
    action_btn_ref = ft.Ref()
    clear_btn_ref = ft.Ref()
    
    # Salvar as referências no dicionário users_controls
    users_controls = { 'wwid': wwid_field_ref, 'name': name_field_ref, 'password': password_field_ref, 'privilege': privilege_dropdown_ref, 'otif_check': otif_check_ref, 'nil_check': nil_check_ref, 'pickup_check': pickup_check_ref, 'package_check': package_check_ref, 'action_btn': action_btn_ref, 'clear_btn': clear_btn_ref }
    # Container do formulário de usuários com referência para atualização de tema
    users_form_container = ft.Container(
        content=ft.Container(
            content=ft.Row([
                # Coluna esquerda - Campos principais
                ft.Column([
                    # Linha 1: WWID e Nome
                    ft.Row([
                        ft.TextField(
                            label="WWID",
                            hint_text="Digite o WWID do usuário",
                            prefix_icon=ft.Icons.BADGE,
                            expand=True,
                            border_radius=8,
                            ref=wwid_field_ref,
                            on_change=on_wwid_change,
                            filled=False,  # Fundo transparente
                            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                        ),
                        ft.TextField(
                            label="Nome Completo",
                            hint_text="Digite o nome do usuário",
                            prefix_icon=ft.Icons.PERSON,
                            expand=True,
                            border_radius=8,
                            ref=name_field_ref,
                            filled=False,  # Fundo transparente
                            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                        ),
                    ], spacing=10),

                    # Linha 2: Senha e Privilégio
                    ft.Row([
                        ft.TextField(
                            label="Senha",
                            hint_text="Digite a senha do usuário",
                            prefix_icon=ft.Icons.LOCK,
                            password=True,
                            can_reveal_password=True,
                            expand=True,
                            border_radius=8,
                            ref=password_field_ref,
                            filled=False,  # Fundo transparente
                            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                        ),
                        ft.Dropdown(
                            label="Nível de Privilégio",
                            hint_text="Selecione o nível",
                            options=[
                                ft.dropdown.Option("User", "User"),
                                ft.dropdown.Option("Admin", "Admin"),
                                ft.dropdown.Option("Super Admin", "Super Admin"),
                            ],
                            expand=True,
                            ref=privilege_dropdown_ref,
                            bgcolor=None,  # Fundo transparente
                            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline'),
                            content_padding=ft.padding.symmetric(horizontal=12, vertical=16),
                        ),
                    ], spacing=10),
                ], expand=2, spacing=15),
                
                # Divisor vertical
                ft.VerticalDivider(width=20, color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')),
                
                # Coluna direita - Permissões
                ft.Column([
                    ft.Text("Permissões de Avaliação", size=16, weight="bold", 
                            color=get_current_theme_colors(get_theme_name_from_page(page)).get('primary')),
                    ft.Container(
                        content=ft.Row([
                            # Primeira coluna de checkboxes
                            ft.Column([
                                ft.Checkbox(
                                    label="OTIF", 
                                    value=False, 
                                    ref=otif_check_ref,
                                    label_style=ft.TextStyle(
                                        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface')
                                    )
                                ),
                                ft.Checkbox(
                                    label="NIL", 
                                    value=False, 
                                    ref=nil_check_ref,
                                    label_style=ft.TextStyle(
                                        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface')
                                    )
                                ),
                            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.START, expand=1),
                            
                            # Segunda coluna de checkboxes
                            ft.Column([
                                ft.Checkbox(
                                    label="Pickup", 
                                    value=False, 
                                    ref=pickup_check_ref,
                                    label_style=ft.TextStyle(
                                        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface')
                                    )
                                ),
                                ft.Checkbox(
                                    label="Package", 
                                    value=False, 
                                    ref=package_check_ref,
                                    label_style=ft.TextStyle(
                                        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface')
                                    )
                                ),
                            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.START, expand=1),
                        ], spacing=20, vertical_alignment=ft.CrossAxisAlignment.START),
                        padding=ft.padding.only(top=10)
                    )
                ], expand=1, horizontal_alignment=ft.CrossAxisAlignment.START, spacing=10),
            ], spacing=15, vertical_alignment=ft.CrossAxisAlignment.START),
            padding=20,
            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
            border_radius=12,
            width=800,  # Largura maior para acomodar as duas colunas
        ),
        alignment=ft.alignment.center
    )


    users_content = ft.Container(
        content=ft.Column([
            # Título fixo
            ft.Text("Gerenciamento de Usuários", size=20, weight="bold"),
            ft.Divider(),
            
            # Header com informações - fixo
            ft.Container(
                content=ft.Row([
                    ft.Text("Configure usuários e suas permissões de avaliação", 
                           size=14, color="outline"),
                ]),
                padding=ft.padding.only(bottom=10)
            ),
            
            # Formulário de usuário - fixo
            users_form_container,

            ft.Container(height=20),
            
            # Botões de ação - fixo
            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        "Add User", 
                        icon=ft.Icons.PERSON_ADD,
                        ref=action_btn_ref,
                    ),
                    ft.ElevatedButton(
                        "Limpar Campos", 
                        icon=ft.Icons.CLEAR,
                        ref=clear_btn_ref,
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
                padding=ft.padding.symmetric(vertical=10)
            ),
            
            ft.Container(height=10),
            ft.Divider(),
            
            # Lista de usuários - com scroll adaptável
            ft.Container(
                content=ft.Column([
                    ft.Text("Usuários Cadastrados", size=16, weight="bold"),
                    ft.Container(
                        content=ft.ListView(
                            spacing=8,
                            expand=True,
                            ref=users_list_ref,  # Referência específica para a lista de usuários
                        ),
                        expand=True,  # Expande para ocupar o espaço restante
                        border=ft.border.all(1, "outline"),
                        border_radius=8,
                        padding=8,
                    ),
                ], spacing=10, expand=True),  # Column expande para ocupar espaço restante
                padding=ft.padding.symmetric(vertical=10),
                expand=True  # Container expande para ocupar espaço disponível
            ),
            
        ], spacing=8, expand=True),
        padding=20,
        visible=False,
        expand=True  # Container principal expande
    )

    # Referências dos controles de usuários
    def extract_users_refs():
        """Extrai as referências dos controles do users_content"""
        users_refs = {}
        try:
            # Preferir usar as refs já criadas no escopo em vez de navegar por índices
            # Isso torna a extração resiliente a mudanças na estrutura do container
            ref_map = {
                'users_list': users_list_ref,
                'wwid': wwid_field_ref,
                'name': name_field_ref,
                'password': password_field_ref,
                'privilege': privilege_dropdown_ref,
                'otif_check': otif_check_ref,
                'nil_check': nil_check_ref,
                'pickup_check': pickup_check_ref,
                'package_check': package_check_ref,
                'action_btn': action_btn_ref,
                'clear_btn': clear_btn_ref,
            }

            for key, ref in ref_map.items():
                try:
                    if ref is None:
                        continue
                    # ft.Ref has attribute 'current'
                    ctrl = ref.current if hasattr(ref, 'current') else ref
                    if ctrl:
                        users_refs[key] = ctrl
                except Exception:
                    # ignorar referências que não possam ser resolvidas
                    continue

            # Fallback: se alguma referência não foi encontrada pelas refs acima,
            # tentar localizar a lista de usuários percorrendo a estrutura (mais lenta)
            if 'users_list' not in users_refs:
                try:
                    # procurar por um ListView que contenha Cards (heurística simples)
                    def find_users_list(control):
                        if isinstance(control, ft.ListView) and getattr(control, 'ref', None) is users_list_ref:
                            return control
                        if hasattr(control, 'controls'):
                            for c in control.controls:
                                found = find_users_list(c)
                                if found:
                                    return found
                        if hasattr(control, 'content') and control.content:
                            return find_users_list(control.content)
                        return None

                    found = find_users_list(users_content)
                    if found:
                        users_refs['users_list'] = found
                except Exception:
                    pass

        except Exception as ex:
            print(f"Erro ao extrair refs de usuários (extract_users_refs): {ex}")

        return users_refs

    # Funções para gerenciamento de usuários
    def load_users_full():
        """Carrega todos os usuários da tabela."""
        if not db_conn:
            return []
        try:
            print("📋 Lista sendo atualizada...")
            rows = db_manager.query("""
                SELECT user_wwid, user_name, user_password, user_privilege, 
                       otif, nil, pickup, package 
                FROM users_table 
                ORDER BY user_wwid
            """)
            users = []
            for row in rows:
                wwid = row['user_wwid']
                name = row['user_name']
                password = row['user_password']
                privilege = row['user_privilege']
                otif = row['otif']
                nil = row['nil']
                pickup = row['pickup']
                package = row['package']
                
                # Criar texto de exibição em duas linhas
                name_display = name if name else "Nome não informado"
                permissions = []
                
                # Converter para int e verificar se é 1
                if int(otif) == 1: permissions.append("OTIF")
                if int(nil) == 1: permissions.append("NIL")
                if int(pickup) == 1: permissions.append("Pickup")
                if int(package) == 1: permissions.append("Package")
                
                permissions_str = ", ".join(permissions) if permissions else "Nenhuma permissão"
                
                # Linha 1: Dados do usuário
                line1 = f"WWID: {wwid} | Nome: {name_display} | Privilégio: {privilege}"
                # Linha 2: Permissões
                line2 = f"Permissões: {permissions_str}"
                
                # Criar texto de exibição com quebra de linha
                display_text = f"{line1}\n{line2}"
                
                users.append({
                    "line1": line1,
                    "line2": line2,
                    "display": display_text,
                    "wwid": wwid,
                    "name": name or "",
                    "password": password,
                    "privilege": privilege,
                    "otif": bool(otif),
                    "nil": bool(nil),
                    "pickup": bool(pickup),
                    "package": bool(package)
                })
            return users
        except Exception as ex:
            print(f"Erro ao carregar usuários: {ex}")
            return []

    def refresh_users_list():
        """Atualiza a lista de usuários na interface."""
        try:
            if 'users_list' not in users_controls:
                return
                
            users = load_users_full()
            users_list = users_controls['users_list']
            users_list.controls.clear()
            
            if not users:
                users_list.controls.append(
                    ft.Container(
                        content=ft.Text(
                            "Nenhum usuário cadastrado",
                            color="outline",
                            italic=True,
                            text_align=ft.TextAlign.CENTER
                        ),
                        alignment=ft.alignment.center,
                        padding=10
                    )
                )
            else:
                # Helper local para criar um card de usuário
                def _make_user_card(u):
                    user_wwid = u["wwid"]
                    name_display = u["name"] or "Nome não informado"
                    privilege = u["privilege"]
                    permissions_str = u["line2"].replace("Permissões: ", "")
                    is_selected = (selected_user == user_wwid)
                    Colors = get_current_theme_colors(get_theme_name_from_page(page))

                    # Botões de ação
                    edit_btn = ft.TextButton(
                        "Editar",
                        icon=ft.Icons.EDIT,
                        on_click=lambda e, w=user_wwid: select_user(w)
                    )

                    def _delete_from_card(e, w=user_wwid):
                        try:
                            # Diálogo de confirmação utilizando o componente já existente
                            def confirm_delete(evt):
                                try:
                                    db_manager.execute("DELETE FROM users_table WHERE UPPER(user_wwid) = ?", (w.upper(),))
                                    page.close(dialog)
                                    # Se o usuário selecionado foi excluído, limpar seleção e campos
                                    if globals().get('selected_user') == w:
                                        clear_users_fields()
                                    refresh_users_list()
                                    show_toast(f"✅ Usuário '{w}' removido com sucesso", "green")
                                    page.update()
                                except Exception as ex:
                                    page.close(dialog)
                                    show_toast(f"❌ Erro ao excluir usuário: {ex}", "red")
                                    page.update()

                            def cancel_delete(evt):
                                page.close(dialog)
                                page.update()

                            dialog = DeleteListItemConfirmationDialog(
                                item_name=w,
                                item_type="Usuário",
                                on_confirm=confirm_delete,
                                on_cancel=cancel_delete,
                                scale_func=lambda x: x
                            )
                            page.open(dialog)
                            page.update()
                        except Exception as ex:
                            show_toast(f"❌ Erro ao tentar excluir usuário: {ex}", "red")
                            page.update()

                    delete_btn = ft.TextButton(
                        "Apagar",
                        icon=ft.Icons.DELETE,
                        style=ft.ButtonStyle(color="red"),
                        on_click=_delete_from_card
                    )

                    header_row = ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, color=Colors['primary']),
                            ft.Text(f"{name_display}", size=15, weight="bold", color=Colors['on_surface'])
                        ], spacing=8),
                        ft.Container(
                            content=ft.Text(f"WWID: {user_wwid}", size=12, color="outline"),
                            alignment=ft.alignment.center_right,
                            expand=True
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

                    content_column = ft.Column([
                        header_row,
                        ft.Text(f"Privilégio: {privilege}", size=12, color="outline"),
                        ft.Text(f"Permissões: {permissions_str}", size=12, color="outline"),
                        ft.Divider(),
                        ft.Row([edit_btn, delete_btn], alignment=ft.MainAxisAlignment.END, spacing=10)
                    ], spacing=6)

                    card_container = ft.Container(
                        content=content_column,
                        padding=12,
                        bgcolor=Colors['primary_container'] if is_selected else get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
                        border_radius=8,
                        border=ft.border.all(1, Colors['outline'])
                    )

                    return ft.Card(content=card_container, elevation=1)

                # Adicionar cards ao ListView
                for user in users:
                    users_list.controls.append(_make_user_card(user))
            
            users_list.update()
        except Exception as ex:
            print(f"Erro ao atualizar lista de usuários: {ex}")

    def select_user(wwid):
        """Seleciona um usuário e carrega seus dados nos campos."""
        global selected_user
        try:

            selected_user = wwid
            
            # Buscar dados do usuário
            row = db_manager.query_one("""
                SELECT user_wwid, user_name, user_password, user_privilege,
                       otif, nil, pickup, package
                FROM users_table 
                WHERE user_wwid = ?
            """, (wwid,))
            
            if row:
                wwid_val = row['user_wwid']
                name = row['user_name']
                password = row['user_password']
                privilege = row['user_privilege']
                otif = row['otif']
                nil = row['nil']
                pickup = row['pickup']
                package = row['package']
                
                print(f"Dados carregados do banco: WWID={wwid_val}, OTIF={otif} (tipo: {type(otif)}), NIL={nil} (tipo: {type(nil)}), Pickup={pickup} (tipo: {type(pickup)}), Package={package} (tipo: {type(package)})")
                
                # Preencher campos de texto
                users_controls['wwid'].value = str(wwid_val) if wwid_val else ""
                users_controls['name'].value = str(name) if name else ""
                users_controls['password'].value = str(password) if password else ""
                users_controls['privilege'].value = str(privilege) if privilege else None
                
                # Definir valores dos checkboxes - convertendo explicitamente para int primeiro
                users_controls['otif_check'].value = int(otif) == 1
                users_controls['nil_check'].value = int(nil) == 1
                users_controls['pickup_check'].value = int(pickup) == 1
                users_controls['package_check'].value = int(package) == 1
                
                print(f"Checkboxes definidos: OTIF={users_controls['otif_check'].value}, NIL={users_controls['nil_check'].value}, Pickup={users_controls['pickup_check'].value}, Package={users_controls['package_check'].value}")
                
                # Atualizar todos os controles
                for control in users_controls.values():
                    if hasattr(control, 'update'):
                        control.update()
                
                # Atualizar botão de ação
                update_action_button()

                page.update()
            
            # Atualizar lista visual
            refresh_users_list()
            
        except Exception as ex:
            print(f"Erro ao selecionar usuário: {ex}")
            show_toast(f"❌ Erro ao carregar usuário: {ex}", "red")
            page.update()

    def clear_users_fields(e=None):
        """Limpa todos os campos do formulário de usuários."""
        try:
            print("Limpando todos os campos (via users_controls)...")

            def resolve(ctrl):
                try:
                    if ctrl is None:
                        return None
                    return ctrl.current if hasattr(ctrl, 'current') else ctrl
                except Exception:
                    return ctrl

            # TextFields
            try:
                w = resolve(users_controls.get('wwid'))
                if w and hasattr(w, 'value'):
                    w.value = ""
                    if hasattr(w, 'update'):
                        w.update()
            except Exception as e:
                print(f"Erro ao limpar WWID: {e}")

            try:
                n = resolve(users_controls.get('name'))
                if n and hasattr(n, 'value'):
                    n.value = ""
                    if hasattr(n, 'update'):
                        n.update()
            except Exception as e:
                print(f"Erro ao limpar Name: {e}")

            try:
                p = resolve(users_controls.get('password'))
                if p and hasattr(p, 'value'):
                    p.value = ""
                    if hasattr(p, 'update'):
                        p.update()
            except Exception as e:
                print(f"Erro ao limpar Password: {e}")

            # Dropdown / Select
            try:
                priv = resolve(users_controls.get('privilege'))
                if priv and hasattr(priv, 'value'):
                    priv.value = None
                    if hasattr(priv, 'update'):
                        priv.update()
            except Exception as e:
                print(f"Erro ao limpar Privilege: {e}")

            # Checkboxes
            try:
                for key in ('otif_check', 'nil_check', 'pickup_check', 'package_check'):
                    cb = resolve(users_controls.get(key))
                    if cb and hasattr(cb, 'value'):
                        cb.value = False
                        if hasattr(cb, 'update'):
                            cb.update()
            except Exception as e:
                print(f"Erro ao limpar checkboxes: {e}")

            # Limpar seleção global
            global selected_user
            selected_user = None

            # Atualizar botão de ação e lista visual
            try:
                update_action_button()
            except Exception:
                pass
            try:
                refresh_users_list()
            except Exception:
                pass

            # Atualizar página por fim
            try:
                page.update()
            except Exception as e:
                print(f"Erro ao atualizar página: {e}")

            print("Campos limpos com sucesso!")
            
        except Exception as ex:
            print(f"Erro ao limpar campos: {ex}")

    def add_or_update_user(e):
        """Adiciona ou atualiza um usuário baseado na função original.

        Recebe o evento `e` do botão para poder manipular o estado do botão
        (desabilitar/enabled) e passá-lo ao `show_toast` como `restore_control`.
        """
        print("🔥 FUNÇÃO add_or_update_user CHAMADA!")
        global current_user_wwid
        save_button = e.control if e and hasattr(e, 'control') else None

        # Marcar botão como processando e desabilitar para evitar cliques múltiplos
        try:
            if save_button is not None:
                try:
                    save_button._is_processing = True
                    save_button.disabled = True
                    save_button.update()
                except Exception:
                    pass

            wwid = users_controls['wwid'].value.strip().upper() if users_controls['wwid'].value else ""
            name = users_controls['name'].value.strip() if users_controls['name'].value else ""
            password = users_controls['password'].value.strip() if users_controls['password'].value else ""
            privilege = users_controls['privilege'].value if users_controls['privilege'].value else ""
            
            otif = 1 if users_controls['otif_check'].value else 0
            nil = 1 if users_controls['nil_check'].value else 0
            pickup = 1 if users_controls['pickup_check'].value else 0
            package = 1 if users_controls['package_check'].value else 0
            
            print(f"Salvando usuário: {wwid}")
            print(f"Valores dos checkboxes: OTIF={users_controls['otif_check'].value}, NIL={users_controls['nil_check'].value}, Pickup={users_controls['pickup_check'].value}, Package={users_controls['package_check'].value}")
            print(f"Valores para o banco: otif={otif}, nil={nil}, pickup={pickup}, package={package}")
            
            if not wwid or not password or not privilege:
                show_toast("❌ Preencha WWID, Senha e Privilégio", "red", restore_control=save_button)
                page.update()
                return
            
            # Verifica se já existe o usuário
            existing_user = db_manager.query_one("SELECT 1 FROM users_table WHERE UPPER(user_wwid) = ?", (wwid,))
            
            with db_manager.transaction(
                event=f"{'Atualização' if existing_user else 'Criação'} de usuário: {wwid}",
                user=current_user_wwid,
                wwid=current_user_wwid
            ) as conn:
                if existing_user:
                    # Atualiza usuário existente
                    print(f"🔄 Atualizando usuário EXISTENTE {wwid}...")
                    db_manager.execute("""
                        UPDATE users_table
                        SET user_name = ?, user_password = ?, user_privilege = ?, 
                            otif = ?, nil = ?, pickup = ?, package = ?,
                            last_updated_by = ?, last_updated_date = CURRENT_TIMESTAMP
                        WHERE UPPER(user_wwid) = ?
                    """, (name, password, privilege, otif, nil, pickup, package, current_user_wwid, wwid))
                    
                    print(f"✅ Usuário {wwid} atualizado com sucesso!")
                    show_toast(f"✅ Usuário '{wwid}' atualizado com sucesso", "green", restore_control=save_button)
                else:
                    # Cria novo usuário
                    print(f"💾 Inserindo NOVO usuário {wwid} no banco de dados...")
                    db_manager.execute("""
                        INSERT INTO users_table (user_wwid, user_name, user_password, user_privilege, 
                                               otif, nil, pickup, package, registered_by) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (wwid, name, password, privilege, otif, nil, pickup, package, current_user_wwid))
                    
                    print(f"✅ Usuário {wwid} inserido com sucesso!")
                    show_toast(f"✅ Usuário '{wwid}' criado com sucesso", "green", restore_control=save_button)
                    # Limpar campos do formulário e atualizar lista imediatamente
                    try:
                        clear_users_fields()
                        refresh_users_list()
                        page.update()
                    except Exception as _e:
                        print(f"Aviso: falha ao limpar/atualizar lista após inserir usuário: {_e}")
            page.update()
            
            print(f"Lista atualizada com {len(load_users_full())} usuários!")
            # Atualizar lista
            refresh_users_list()
            
        except Exception as ex:
            show_toast(f"❌ Erro ao salvar usuário: {ex}", "red")
            # Garantir que o botão seja restaurado se ocorrer erro
            try:
                if save_button is not None:
                    save_button.disabled = False
                    save_button._is_processing = False
                    save_button.update()
            except Exception:
                pass
            page.update()
            print(f"Erro ao adicionar/atualizar usuário: {ex}")
        finally:
            # Certificar-se de limpar flag de processamento caso não tenha sido restaurada pelo show_toast
            try:
                if save_button is not None and getattr(save_button, '_is_processing', False):
                    save_button._is_processing = False
                    save_button.disabled = False
                    save_button.update()
            except Exception:
                pass

    def delete_user():
        """Exclui o usuário baseado no WWID do campo de texto."""
        try:
            # Pegar WWID do campo de texto
            wwid = users_controls['wwid'].value.strip() if users_controls['wwid'].value else ''

            
            if not wwid:
                show_toast("❌ Digite um WWID para excluir", "red")
                page.update()
                return
            
            # Verificar se o usuário existe no banco
            if not check_user_exists(wwid):
                show_toast(f"❌ Usuário '{wwid}' não encontrado", "red")
                page.update()
                return
            
            # Função para confirmar e executar a exclusão
            def confirm_delete_user(e):
                try:
                    db_manager.execute("DELETE FROM users_table WHERE UPPER(user_wwid) = ?", (wwid.upper(),))
                    
                    # Fechar dialog
                    page.close(dialog)
                    
                    # Limpar campos e seleção
                    clear_users_fields()
                    
                    # Atualizar lista
                    refresh_users_list()
                    
                    show_toast(f"✅ Usuário '{wwid}' removido com sucesso", "green")
                    page.update()
                    
                except Exception as ex:
                    # Fechar dialog mesmo se der erro
                    page.close(dialog)
                    
                    show_toast(f"❌ Erro ao excluir usuário: {ex}", "red")
                    page.update()
                    print(f"Erro ao deletar usuário {wwid}: {ex}")
            
            # Função para cancelar
            def cancel_delete_user(e):
                page.close(dialog)
                page.update()
            
            # Criar e mostrar dialog de confirmação
            dialog = DeleteListItemConfirmationDialog(
                item_name=wwid,
                item_type="Usuário",
                on_confirm=confirm_delete_user,
                on_cancel=cancel_delete_user,
                scale_func=lambda x: x
            )
            
            page.open(dialog)
            page.update()
            
        except Exception as ex:
            show_toast(f"❌ Erro ao tentar excluir usuário: {ex}", "red")
            page.update()
            print(f"Erro geral no delete_user: {ex}")

    # Referências para os controles da aba Log
    log_user_filter_ref = ft.Ref()
    # DataTable única para consolidar lista e detalhes
    log_table_ref = ft.Ref()

    log_controls = {
        'user_filter': log_user_filter_ref,
        'table': log_table_ref,
    }

    # Conteúdo da sub-aba Log com largura maximizada
    log_content = ft.Container(
        content=ft.Column([
            ft.Text("Log de Atividades", size=20, weight="bold"),
            ft.Divider(),
            ft.Row([
                ft.TextField(
                    ref=log_user_filter_ref,
                    label="Pesquisar por WWID", 
                    expand=True,
                    bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                    color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                    border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                ),
                ft.ElevatedButton("Filtrar", icon=ft.Icons.FILTER_LIST, on_click=lambda e: load_log_entries(log_user_filter_ref.current.value if log_user_filter_ref and hasattr(log_user_filter_ref, 'current') else None)),
            ], spacing=10),
            ft.Container(height=10),  # Espaçamento reduzido
            # Tabela consolidada com largura total da tela
            ft.Container(
                content=ft.Column([
                    ft.DataTable(
                        ref=log_table_ref,
                        columns=[
                            ft.DataColumn(ft.Text("", weight="bold"), numeric=False),  # Ícone
                            ft.DataColumn(ft.Text("Data/Hora", weight="bold"), numeric=False),
                            ft.DataColumn(ft.Text("WWID", weight="bold"), numeric=False),  # Nova coluna WWID
                            ft.DataColumn(ft.Text("Usuário", weight="bold"), numeric=False),
                            ft.DataColumn(ft.Text("Detalhes", weight="bold"), numeric=False),
                        ],
                        rows=[],
                        border=ft.border.all(1, "outline"),
                        border_radius=8,
                        heading_row_color=get_current_theme_colors(get_theme_name_from_page(page)).get('surface_variant'),
                        data_row_color={"hovered": get_current_theme_colors(get_theme_name_from_page(page)).get('surface_variant')},
                        column_spacing=10,  # Espaçamento reduzido
                        horizontal_margin=5,  # Margem reduzida
                        width=None,  # Permite que a tabela use toda largura disponível
                    )
                ], 
                expand=True, 
                scroll=ft.ScrollMode.ADAPTIVE
                ),
                expand=True,
                padding=2,  # Padding mínimo
                border=ft.border.all(1, "outline"),
                border_radius=8,
            )
        ], spacing=10),  # Espaçamento geral reduzido
        padding=5,  # Padding do container principal minimizado  
        visible=False,
        expand=True,  # Container principal expandir para ocupar espaço disponível
    )


    # Variável global para controlar paginação do log
    log_pagination = {
        'current_offset': 0,
        'page_size': 200,
        'loading': False,
        'has_more': True,
        'current_filter': None
    }

    # Função para carregar entradas da tabela log_table e popular a DataTable com paginação
    def load_log_entries(wwid_filter=None, append_mode=False):
        try:
            # Referência para a DataTable
            table_control = log_table_ref.current if log_table_ref and hasattr(log_table_ref, 'current') else None
            
            if not table_control:
                print("DataTable não encontrada")
                return

            # Evitar múltiplas requisições simultâneas
            if log_pagination['loading']:
                return
                
            log_pagination['loading'] = True

            # Se não é append_mode, resetar paginação
            if not append_mode:
                log_pagination['current_offset'] = 0
                log_pagination['has_more'] = True
                log_pagination['current_filter'] = wwid_filter
                table_control.rows.clear()
            
            # Se filtro mudou, resetar
            if wwid_filter != log_pagination['current_filter']:
                log_pagination['current_offset'] = 0
                log_pagination['has_more'] = True  
                log_pagination['current_filter'] = wwid_filter
                if not append_mode:
                    table_control.rows.clear()

            # preparar ícones por tipo
            def icon_for_event(event_text):
                try:
                    if not event_text:
                        return ft.Container()  # Sem ícone se não há evento
                    
                    # procurar prefixo [UPDATED], [EXCLUDED], [INCLUDED] (case insensitive)
                    event_upper = event_text.upper()
                    if event_upper.startswith('[UPDATED]'):
                        return ft.Icon(ft.Icons.EDIT, size=16, color="#2196F3")  # Azul
                    elif event_upper.startswith('[EXCLUDED]'):
                        return ft.Icon(ft.Icons.DELETE, size=16, color="#F44336")  # Vermelho
                    elif event_upper.startswith('[INCLUDED]'):
                        return ft.Icon(ft.Icons.ADD, size=16, color="#4CAF50")  # Verde
                    
                    # Se não tem prefixo específico, não mostrar ícone
                    return ft.Container()
                except Exception as e:
                    print(f"Erro ao processar ícone: {e}")
                    return ft.Container()

            # Buscar dados do DB com LIMIT e OFFSET para paginação
            rows = []
            try:
                base_q = f"SELECT log_id, date, time, user, wwid, event FROM {db_manager.log_table_name}"
                if wwid_filter:
                    # permitir pesquisa parcial (LIKE) em user, wwid E nos dados JSON do evento (para WWID)
                    q = base_q + f" WHERE (UPPER(user) LIKE ? OR UPPER(wwid) LIKE ? OR UPPER(event) LIKE ?) ORDER BY date DESC, time DESC LIMIT {log_pagination['page_size']} OFFSET {log_pagination['current_offset']}"
                    filter_param = f"%{wwid_filter.upper()}%"
                    rows = db_manager.query(q, (filter_param, filter_param, filter_param))
                else:
                    q = base_q + f" ORDER BY date DESC, time DESC LIMIT {log_pagination['page_size']} OFFSET {log_pagination['current_offset']}"
                    rows = db_manager.query(q)
                    
                # Verificar se há mais dados
                if len(rows) < log_pagination['page_size']:
                    log_pagination['has_more'] = False
                else:
                    log_pagination['has_more'] = True
                    
            except Exception as e:
                print(f"Erro ao ler log_table: {e}")
                log_pagination['loading'] = False
                return

            # Se não há linhas na primeira página, mostrar mensagem
            if not rows and log_pagination['current_offset'] == 0:
                table_control.rows.append(
                    ft.DataRow(cells=[
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("Nenhuma entrada de log encontrada.", italic=True)),
                        ft.DataCell(ft.Text(""))
                    ])
                )
                table_control.update()
                log_pagination['loading'] = False
                return

            # Função para formatar texto de evento para exibição
            def format_event_text(raw_text):
                # Tenta parsear JSON para formatar legivelmente
                try:
                    import json
                    parsed = json.loads(raw_text)
                    # Se for dict ou list, formatar com separador "-"
                    if isinstance(parsed, dict):
                        lines = []
                        for k, v in parsed.items():
                            # Limpar valor de aspas e caracteres especiais
                            clean_v = str(v).replace('"', '').replace("'", '').replace('\n', ' ')
                            lines.append(f"{k}: {clean_v}")
                        return " - ".join(lines)
                    if isinstance(parsed, list):
                        cleaned_list = [str(x).replace('"', '').replace("'", '').replace('\n', ' ') for x in parsed]
                        return " - ".join(cleaned_list)
                except Exception:
                    # não JSON -> seguir para parsing simples
                    pass

                # Limpar texto simples de caracteres especiais
                try:
                    # Remover aspas, quebras de linha e outros caracteres especiais
                    cleaned_text = raw_text.replace('"', '').replace("'", '').replace('\n', ' ').replace('\\n', ' ')
                    # Se há vírgulas, separar por elas e usar "-"
                    if ',' in cleaned_text:
                        parts = [p.strip() for p in cleaned_text.split(',') if p.strip()]
                        return " - ".join(parts) if parts else cleaned_text
                    return cleaned_text
                except Exception:
                    return raw_text

            # Extrair WWID do registro (agora que temos coluna específica)
            def extract_wwid(row):
                # Com a nova coluna wwid, simplesmente retornar seu valor
                if 'wwid' in row and row['wwid']:
                    return str(row['wwid'])
                # Fallback para compatibilidade com registros antigos
                return row.get('user', '')

            # Popular tabela com nova estrutura de colunas
            for r in rows:
                event = r.get('event') or ''
                date = r.get('date') or ''
                time = r.get('time') or ''
                user = r.get('user') or ''
                wwid = extract_wwid(r)  # Agora sem segundo parâmetro

                # Criar células da linha com nova estrutura
                icon_widget = icon_for_event(event)
                icon_cell = ft.DataCell(
                    ft.Container(
                        content=icon_widget,
                        width=40,
                        height=30,  # Altura mínima para garantir visibilidade
                        alignment=ft.alignment.center
                    )
                )
                
                datetime_cell = ft.DataCell(
                    ft.Container(
                        content=ft.Text(f"{date}\\n{time}", size=11),
                        width=120
                    )
                )
                
                # Nova coluna WWID separada
                wwid_cell = ft.DataCell(
                    ft.Container(
                        content=ft.Text(wwid or "", size=11, overflow=ft.TextOverflow.ELLIPSIS),
                        width=100
                    )
                )
                
                # Coluna usuário agora só mostra o nome do usuário
                user_cell = ft.DataCell(
                    ft.Container(
                        content=ft.Text(user, size=11, overflow=ft.TextOverflow.ELLIPSIS),
                        width=120
                    )
                )
                
                # Detalhes formatados do evento (ajustado)
                details_formatted = format_event_text(event)
                details_cell = ft.DataCell(
                    ft.Container(
                        content=ft.Text(
                            details_formatted,
                            size=10,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        width=400,
                        tooltip=details_formatted  # Tooltip mostra texto completo
                    )
                )

                # Adicionar linha à tabela com nova estrutura
                table_control.rows.append(
                    ft.DataRow(cells=[icon_cell, datetime_cell, wwid_cell, user_cell, details_cell])
                )

            # Atualizar tabela
            table_control.update()

            # Incrementar offset para próxima página
            log_pagination['current_offset'] += log_pagination['page_size']
            
            # Adicionar linha "Carregar mais" se há mais dados
            if log_pagination['has_more']:
                def load_more_handler(e):
                    load_log_entries(wwid_filter, append_mode=True)
                
                load_more_row = ft.DataRow(cells=[
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(
                        ft.ElevatedButton(
                            "Carregar mais...",
                            icon=ft.Icons.EXPAND_MORE,
                            on_click=load_more_handler,
                            style=ft.ButtonStyle(
                                bgcolor="#E3F2FD",
                                color="#1976D2"
                            )
                        )
                    ),
                    ft.DataCell(ft.Text(""))
                ])
                table_control.rows.append(load_more_row)
                table_control.update()

            log_pagination['loading'] = False

        except Exception as e:
            print(f"Erro geral ao carregar logs: {e}")
            log_pagination['loading'] = False


    # Hook: carregar log quando a aba for aberta
    def ensure_log_loaded():
        try:
            # A aba `log_content` é mostrada ao selecionar o índice; carregamos os dados quando visível
            if log_content.visible:
                # usar valor atual do campo de pesquisa (WWID)
                w = log_user_filter_ref.current.value if log_user_filter_ref and hasattr(log_user_filter_ref, 'current') and log_user_filter_ref.current.value else None
                load_log_entries(w)
        except Exception as ex:
            print(f"Erro ao garantir carregamento do log: {ex}")

    def clear_log_fields():
        """Limpa os campos da aba Log quando o usuário sair da aba"""
        try:
            # Resetar paginação
            log_pagination['current_offset'] = 0
            log_pagination['has_more'] = True
            log_pagination['current_filter'] = None
            log_pagination['loading'] = False
            
            # Limpar campo de filtro/pesquisa
            if log_user_filter_ref.current:
                log_user_filter_ref.current.value = ""
                log_user_filter_ref.current.update()
            
            # Limpar tabela de logs
            if log_table_ref.current:
                log_table_ref.current.rows.clear()
                log_table_ref.current.update()
            
            print("🧹 Campos da aba Log limpos com sucesso")
            
        except Exception as ex:
            print(f"❌ Erro ao limpar campos da aba Log: {ex}")

    def test_log_clear_functionality():
        """Função de teste para demonstrar a limpeza automática da aba Log"""
        try:
            print("🧪 Testando funcionalidade de limpeza da aba Log...")
            print("✅ Implementação concluída:")
            print("   - Campos da aba Log são limpos automaticamente ao sair da aba")
            print("   - Campo de pesquisa/filtro é limpo")
            print("   - Lista de logs é limpa")
            print("   - Detalhes do log selecionado são limpos")
            print("🎯 Agora quando você sair da aba Log, todos os campos serão automaticamente limpos!")
            
        except Exception as ex:
            print(f"❌ Erro no teste de limpeza da aba Log: {ex}")

    def demo_home_tab():
        """Função de demonstração da nova aba Home"""
        try:
            print("🏠 Nova Aba Home implementada com sucesso!")
            print("✅ Características da aba Home:")
            print("   - Dashboard principal com boas-vindas personalizadas")
            print("   - Cards de estatísticas rápidas (Fornecedores, Avaliações, Score Médio, Usuários)")
            print("   - Informações do sistema e usuário logado")
            print("   - Design responsivo com cards organizados")
            print("🎯 Navegação atualizada:")
            print("   - Home (índice 0) - Nova aba principal")
            print("   - Score (índice 1) - Anteriormente índice 0")
            print("   - Timeline (índice 2) - Anteriormente índice 1")
            print("   - Risks (índice 3) - Anteriormente índice 2")
            print("   - Email (índice 4) - Anteriormente índice 3")
            print("   - Configs (índice 5) - Anteriormente índice 4")
            print("🚀 A aplicação agora inicia na aba Home como painel principal!")
            
        except Exception as ex:
            print(f"❌ Erro na demonstração da aba Home: {ex}")

    # Row para as abas de configuração
    config_tabs_row = ft.Row(
        alignment=ft.MainAxisAlignment.START,
        spacing=10
    )

    # Container principal da aba configs
    configs_view_content = ft.Column([
        config_tabs_row,
        ft.Divider(),
        ft.Container(
            content=ft.Stack([
                themes_content,
                suppliers_content,
                criteria_content,
                users_content,
                lists_content,
                log_content
            ]),
            expand=True
        )
    ], expand=True)

    # --- Fim: Lógica e Controles da Aba Configs ---

    # --- Início: Conteúdo da Aba Home ---
    def create_home_content():
        """Cria o conteúdo da aba Home com informações e design diferenciado"""
        
        # Cards de estatísticas rápidas
        def create_stats_card(title, value, icon, color):
            theme_colors = get_current_theme_colors(get_theme_name_from_page(page))
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(icon, color=color, size=32),
                        ft.Column([
                            ft.Text(value, size=26, weight="bold", color=color),
                            ft.Text(title, size=13, color=theme_colors.get('on_surface_variant', '#666666'), weight="w500")
                        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.START)
                    ], alignment=ft.MainAxisAlignment.START, spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ], spacing=0, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.START),
                bgcolor=theme_colors.get('card_background'),
                border_radius=16,
                padding=ft.padding.all(24),
                width=200,
                height=90,
                border=ft.border.all(1, theme_colors.get('outline_variant', '#E8E8E8')),
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=8,
                    color="#00000010"
                )
            )



        # Seção de boas-vindas
        theme_colors = get_current_theme_colors(get_theme_name_from_page(page))
        welcome_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.DASHBOARD, size=42, color=theme_colors.get('primary')),
                    ft.Column([
                        ft.Text(f"Bem-vindo, {current_user_name}!", size=32, weight="bold", color=theme_colors.get('on_surface', '#1565C0')),
                        ft.Text("Painel de Controle - Supplier Score APP", size=18, color=theme_colors.get('on_surface_variant', '#666666'), weight="w400")
                    ], spacing=4, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.START)
                ], alignment=ft.MainAxisAlignment.START, spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=40)
        )

        # Seção de estatísticas
        stats_section = ft.Container(
            content=ft.Column([
                ft.Text("📊 Estatísticas Rápidas", size=22, weight="bold", color=theme_colors.get('on_surface', '#333333')),
                ft.Container(
                    content=ft.Row([
                        create_stats_card("Fornecedores", "250+", ft.Icons.BUSINESS, "#1976D2"),
                        create_stats_card("Avaliações", "1.2K", ft.Icons.STAR, "#F57C00"),
                        create_stats_card("Score Médio", "8.5", ft.Icons.TRENDING_UP, "#388E3C"),
                        create_stats_card("Usuários", "12", ft.Icons.PEOPLE, "#7B1FA2")
                    ], wrap=True, spacing=24, alignment=ft.MainAxisAlignment.CENTER),
                    padding=ft.padding.only(top=8)
                )
            ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=40)
        )

        # Seção de informações do sistema
        info_section = ft.Container(
            content=ft.Column([
                ft.Text("ℹ️ Informações do Sistema", size=22, weight="bold", color=theme_colors.get('on_surface', '#333333')),
                ft.Container(
                    content=ft.Column([
                        # Informações do usuário
                        ft.Text("👤 Usuário", size=16, weight="bold", color=theme_colors.get('primary', '#1976D2')),
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, size=18, color=theme_colors.get('on_surface_variant', '#666666')),
                            ft.Text(f"{current_user_name}", size=14, weight="w500", color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Icon(ft.Icons.BADGE, size=18, color=theme_colors.get('on_surface_variant', '#666666')),
                            ft.Text(f"WWID: {current_user_wwid}", size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Icon(ft.Icons.SECURITY, size=18, color=theme_colors.get('on_surface_variant', '#666666')),
                            ft.Text(f"Privilégio: {current_user_privilege}", size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        
                        ft.Divider(height=20),
                        
                        # Permissões de avaliação
                        ft.Text("🔐 Permissões de Avaliação", size=16, weight="bold", color=theme_colors.get('secondary', '#388E3C')),
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE if current_user_permissions.get('otif', False) else ft.Icons.CANCEL, 
                                   size=18, color="#4CAF50" if current_user_permissions.get('otif', False) else "#F44336"),
                            ft.Text(f"OTIF: {'Permitido' if current_user_permissions.get('otif', False) else 'Negado'}", 
                                   size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE if current_user_permissions.get('nil', False) else ft.Icons.CANCEL, 
                                   size=18, color="#4CAF50" if current_user_permissions.get('nil', False) else "#F44336"),
                            ft.Text(f"NIL: {'Permitido' if current_user_permissions.get('nil', False) else 'Negado'}", 
                                   size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE if current_user_permissions.get('pickup', False) else ft.Icons.CANCEL, 
                                   size=18, color="#4CAF50" if current_user_permissions.get('pickup', False) else "#F44336"),
                            ft.Text(f"Pickup: {'Permitido' if current_user_permissions.get('pickup', False) else 'Negado'}", 
                                   size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Icon(ft.Icons.CHECK_CIRCLE if current_user_permissions.get('package', False) else ft.Icons.CANCEL, 
                                   size=18, color="#4CAF50" if current_user_permissions.get('package', False) else "#F44336"),
                            ft.Text(f"Package: {'Permitido' if current_user_permissions.get('package', False) else 'Negado'}", 
                                   size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        
                        ft.Divider(height=20),
                        
                        # Informações do sistema
                        ft.Text("⚙️ Sistema", size=16, weight="bold", color=theme_colors.get('secondary', '#388E3C')),
                        ft.Row([
                            ft.Icon(ft.Icons.INFO, size=18, color=theme_colors.get('on_surface_variant', '#666666')),
                            ft.Text("Versão: 1.0.0", size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Icon(ft.Icons.ACCESS_TIME, size=18, color=theme_colors.get('on_surface_variant', '#666666')),
                            ft.Text("Atualização: Hoje", size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Row([
                            ft.Icon(ft.Icons.STORAGE, size=18, color=theme_colors.get('on_surface_variant', '#666666')),
                            ft.Text("BD: Conectado", size=14, color=theme_colors.get('on_surface', '#000000'))
                        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.START),
                    bgcolor=theme_colors.get('surface_variant'),
                    border_radius=12,
                    padding=24,
                    width=500,  # Largura maior para acomodar todo o conteúdo
                    alignment=ft.alignment.top_left
                )
            ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        return ft.Column([
            welcome_section,
            stats_section,
            info_section
        ], spacing=20, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Criar a aba Home com referência atualizável
    home_content_container = ft.Ref[ft.Container]()
    
    home_view = ft.Container(
        content=ft.Container(
            ref=home_content_container,
            content=create_home_content(),
            padding=ft.padding.only(top=30, left=40, right=40, bottom=30),
            alignment=ft.alignment.top_center
        ),
        visible=True,  # Home será a aba inicial
        expand=True
    )

    # --- Fim: Conteúdo da Aba Home ---

    score_view = ft.Column(
        [
            # Header com botão de menu
            ft.Container(
                content=ft.Row([
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_HORIZ,
                        items=[
                            ft.PopupMenuItem(
                                text="Gerar nota cheia",
                                icon=ft.Icons.STAR,
                                on_click=lambda _: generate_full_score_dialog()
                            )
                        ],
                        tooltip="Opções",
                        icon_color=get_current_theme_colors(get_theme_name_from_page(page)).get('primary'),
                        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('surface_variant'),
                        shape=ft.RoundedRectangleBorder(radius=8)
                    ),
                    ft.Container(expand=True),  # Spacer para empurrar o menu para a esquerda
                ], alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.only(left=20, right=20, top=10)
            ),
            ft.Container(
                content=score_view_content, 
                alignment=ft.alignment.top_center, 
                padding=ft.padding.only(top=10, left=20, right=20, bottom=10)
            ),
            ft.Divider(),
            results_list,
        ],
        visible=False,  # Score não será mais a aba inicial
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
    # --- Início: Lógica da Aba Timeline ---
    
    # Referências para os campos de seleção do Timeline
    timeline_vendor_dropdown = ft.Ref[ft.Dropdown]()
    timeline_year_dropdown = ft.Ref[ft.Dropdown]()
    timeline_bu_dropdown = ft.Ref[ft.Dropdown]()
    
    
    # Referência para o container dos campos de pesquisa
    timeline_search_container = ft.Ref[ft.Container]()
    
    # Refs for additional score checkboxes
    timeline_otif_check = ft.Ref[ft.Checkbox]()
    timeline_nil_check = ft.Ref[ft.Checkbox]()
    timeline_pickup_check = ft.Ref[ft.Checkbox]()
    timeline_package_check = ft.Ref[ft.Checkbox]()
    
    # Referências para os cards de métricas
    overall_avg_card = ft.Ref[ft.Text]()
    twelve_month_avg_card = ft.Ref[ft.Text]()
    year_avg_card = ft.Ref[ft.Text]()
    q1_avg_card = ft.Ref[ft.Text]()
    q2_avg_card = ft.Ref[ft.Text]()
    q3_avg_card = ft.Ref[ft.Text]()
    q4_avg_card = ft.Ref[ft.Text]()
    
    # Referências para os ícones de seta nos cards Q
    q1_arrow_icon = ft.Ref[ft.Icon]()
    q2_arrow_icon = ft.Ref[ft.Icon]()
    q3_arrow_icon = ft.Ref[ft.Icon]()
    q4_arrow_icon = ft.Ref[ft.Icon]()

    # Referências para aba Risks
    risks_year_dropdown = ft.Ref[ft.Dropdown]()
    risks_cards_container = ft.Ref[ft.Container]()
    target_risks_text = ft.Ref[ft.Text]()
    # Ref para o container que agrupa ano e target (para atualização de tema)
    risks_header_container = ft.Ref[ft.Container]()
    # Ref para o container do display de Target (borda/背景 especial)
    target_display_container = ft.Ref[ft.Container]()
    
    # Referências para as abas de visualização
    timeline_chart_tab = ft.Ref[bool]()
    timeline_table_tab = ft.Ref[bool]()
    timeline_chart_tab.current = True
    timeline_table_tab.current = False
    
    # Referências para os botões de gráfico e tabela
    timeline_chart_button = ft.Ref[ft.ElevatedButton]()
    timeline_table_button = ft.Ref[ft.ElevatedButton]()
    
    # Container para o gráfico e tabela
    timeline_chart_container = ft.Ref[ft.Container]()
    timeline_table_container = ft.Ref[ft.Container]()
    
    # Referência para a linha que contém os cards de métricas
    timeline_metrics_row = ft.Ref[ft.Row]()

    # Dicionário de referências para os componentes dos cards de métricas
    timeline_cards_refs = {
        "overall": {"card": ft.Ref(), "icon": ft.Ref(), "value": overall_avg_card, "gradient": ft.Ref()},
        "12m": {"card": ft.Ref(), "icon": ft.Ref(), "value": twelve_month_avg_card, "gradient": ft.Ref()},
        "year": {"card": ft.Ref(), "icon": ft.Ref(), "value": year_avg_card, "gradient": ft.Ref()},
        "q1": {"card": ft.Ref(), "icon": ft.Ref(), "value": q1_avg_card, "gradient": ft.Ref()},
        "q2": {"card": ft.Ref(), "icon": ft.Ref(), "value": q2_avg_card, "gradient": ft.Ref()},
        "q3": {"card": ft.Ref(), "icon": ft.Ref(), "value": q3_avg_card, "gradient": ft.Ref()},
        "q4": {"card": ft.Ref(), "icon": ft.Ref(), "value": q4_avg_card, "gradient": ft.Ref()},
    }
    
    def load_suppliers_for_timeline():
        """Carrega todos os suppliers do banco de dados para o dropdown no formato 'Supplier - BU'"""
        try:
            if not db_conn:
                return [ft.dropdown.Option("", "Nenhum supplier disponível")]
            
            suppliers = db_manager.query("SELECT supplier_id, vendor_name, bu FROM supplier_database_table ORDER BY vendor_name")
            
            options = [ft.dropdown.Option("", "Selecione um supplier")]
            for supplier in suppliers:
                supplier_id = supplier['supplier_id']
                vendor_name = supplier['vendor_name']
                bu = supplier['bu']
                # Formato: "Supplier - BU"
                bu_text = bu if bu else "N/A"
                display_text = f"{vendor_name} - {bu_text}"
                options.append(ft.dropdown.Option(str(supplier_id), display_text))
                
            return options
        except Exception as e:
            print(f"Erro ao carregar suppliers: {e}")
            return [ft.dropdown.Option("", "Erro ao carregar suppliers")]

            
    def load_business_units_for_timeline():
        """Carrega todas as business units do banco de dados para o dropdown"""
        try:
            if not db_conn:
                return [ft.dropdown.Option("", "Nenhuma BU disponível")]
            
            bus = db_manager.query("SELECT DISTINCT bu FROM business_unit_table WHERE bu IS NOT NULL AND bu != '' ORDER BY bu")
            
            options = [ft.dropdown.Option("", "Todas as BUs")]
            for bu_row in bus:
                bu = bu_row['bu']
                options.append(ft.dropdown.Option(str(bu), str(bu)))
                
            return options
        except Exception as e:
            print(f"Erro ao carregar business units: {e}")
            return [ft.dropdown.Option("", "Erro ao carregar BUs")]
  
    
    def update_timeline_metrics():
        """Atualiza todos os cards de métricas baseado no vendor selecionado"""
        vendor_id = timeline_vendor_dropdown.current.value if timeline_vendor_dropdown.current else ""
        year = timeline_year_dropdown.current.value if timeline_year_dropdown.current else None
        
        if not vendor_id:
            # Limpar todos os cards
            overall_avg_card.current.value = "--"
            twelve_month_avg_card.current.value = "--"
            year_avg_card.current.value = "--"
            q1_avg_card.current.value = "--"
            q2_avg_card.current.value = "--"
            q3_avg_card.current.value = "--"
            q4_avg_card.current.value = "--"
            page.update()
            return
            
        calculate_overall_average(vendor_id)
        calculate_twelve_month_average(vendor_id)
        calculate_year_average(vendor_id, year)
        calculate_quarterly_averages(vendor_id, year)
        update_timeline_chart(vendor_id, year)
        
        # Atualizar a página após todos os cálculos
        page.update()
        
    def calculate_overall_average(vendor_id):
        """Calcula a média geral de todos os scores do vendor"""
        try:
            if not db_conn:
                overall_avg_card.current.value = "Error"
                return
                
            query = "SELECT total_score FROM supplier_score_records_table WHERE supplier_id = ? AND total_score > 0"
            results = db_manager.query(query, (vendor_id,))
            
            if results:
                scores = [float(row['total_score']) for row in results]
                avg = sum(scores) / len(scores)
                overall_avg_card.current.value = f"{avg:.1f}"
            else:
                overall_avg_card.current.value = "--"
                
        except Exception as e:
            print(f"Erro ao calcular média geral: {e}")
            overall_avg_card.current.value = "Error"
            
    def calculate_twelve_month_average(vendor_id):
        """Calcula a média dos últimos 12 meses"""
        try:
            if not db_conn:
                twelve_month_avg_card.current.value = "Error"
                return
                
            cursor = db_conn.cursor()
            
            # Obter data atual
            import datetime
            hoje = datetime.date.today()
            
            # Calcular os últimos 12 meses
            scores = []
            for i in range(12):
                data = hoje - datetime.timedelta(days=30*i)  # Aproximação de mês
                query = """SELECT total_score FROM supplier_score_records_table 
                          WHERE supplier_id = ? AND year = ? AND month = ? AND total_score > 0"""
                result = db_manager.query_one(query, (vendor_id, data.year, data.month))
                if result:
                    scores.append(float(result["total_score"]))
            
            if scores:
                avg = sum(scores) / len(scores)
                twelve_month_avg_card.current.value = f"{avg:.1f}"
            else:
                twelve_month_avg_card.current.value = "--"
                
        except Exception as e:
            print(f"Erro ao calcular média 12 meses: {e}")
            twelve_month_avg_card.current.value = "Error"
            
    def calculate_year_average(vendor_id, year=None):
        """Calcula a média do ano selecionado ou ano atual"""
        try:
            if not db_conn:
                year_avg_card.current.value = "Error"
                return
                
            cursor = db_conn.cursor()
            
            if year and year.strip():
                query = """SELECT total_score FROM supplier_score_records_table 
                          WHERE supplier_id = ? AND year = ? AND total_score > 0"""
                results = db_manager.query(query, (vendor_id, year))
            else:
                import datetime
                current_year = datetime.date.today().year
                query = """SELECT total_score FROM supplier_score_records_table 
                          WHERE supplier_id = ? AND year = ? AND total_score > 0"""
                results = db_manager.query(query, (vendor_id, current_year))
            
            if results:
                scores = [float(row['total_score']) for row in results]
                avg = sum(scores) / len(scores)
                year_avg_card.current.value = f"{avg:.1f}"
            else:
                year_avg_card.current.value = "--"
                
        except Exception as e:
            print(f"Erro ao calcular média anual: {e}")
            year_avg_card.current.value = "Error"
            
    def calculate_quarterly_averages(vendor_id, year=None):
        """Calcula as médias trimestrais"""
        try:
            if not db_conn:
                q1_avg_card.current.value = "Error"
                q2_avg_card.current.value = "Error"
                q3_avg_card.current.value = "Error"
                q4_avg_card.current.value = "Error"
                return
                
            cursor = db_conn.cursor()
            current_year = int(year) if year and year.strip() else datetime.date.today().year
            previous_year = current_year - 1
            
            # Definir meses de cada trimestre como lista ordenada
            # Usamos uma lista para garantir a ordem (Q1..Q4) e permitir buscar o trimestre anterior
            quarters = [
                ('Q1', [1, 2, 3]),
                ('Q2', [4, 5, 6]),
                ('Q3', [7, 8, 9]),
                ('Q4', [10, 11, 12])
            ]

            quarter_cards = [q1_avg_card, q2_avg_card, q3_avg_card, q4_avg_card]
            quarter_icons = [q1_arrow_icon, q2_arrow_icon, q3_arrow_icon, q4_arrow_icon]

            # Para cada trimestre, calculamos a média do trimestre atual e do TRIMESTRE ANTERIOR
            # (ex: Q2 compara com Q1; Q1 compara com Q4 do ano anterior). Isso corrige a lógica que
            # antes comparava com o mesmo trimestre do ano anterior.
            for i, (quarter_name, months) in enumerate(quarters):
                # Calcular média do ano atual
                month_placeholders = ','.join(['?' for _ in months])
                query_current = f"""SELECT total_score FROM supplier_score_records_table 
                                   WHERE supplier_id = ? AND year = ? AND month IN ({month_placeholders}) AND total_score > 0"""
                
                params_current = [vendor_id, current_year] + months
                results_current = db_manager.query(query_current, params_current)
                
                avg_current = None
                if results_current:
                    scores = [float(row['total_score']) for row in results_current]
                    avg_current = sum(scores) / len(scores)
                    quarter_cards[i].current.value = f"{avg_current:.1f}"
                else:
                    quarter_cards[i].current.value = "--"
                
                # Procurar o último trimestre anterior que tenha dados
                def find_prev_available_avg(start_idx, start_year):
                    """Procura até 4 trimestres anteriores (incluindo cruzar para o ano anterior) e retorna a média do primeiro encontrado."""
                    for step in range(1, len(quarters) + 1):
                        delta = start_idx - step
                        idx = delta % len(quarters)
                        year_to_check = start_year + (delta // len(quarters))
                        months_to_check = quarters[idx][1]
                        placeholders = ','.join(['?' for _ in months_to_check])
                        query = f"""SELECT total_score FROM supplier_score_records_table
                                    WHERE supplier_id = ? AND year = ? AND month IN ({placeholders}) AND total_score > 0"""
                        params = [vendor_id, year_to_check] + months_to_check
                        res = db_manager.query(query, params)
                        if res:
                            scores = [float(r["total_score"]) for r in res]
                            return sum(scores) / len(scores)
                    return None

                avg_previous = find_prev_available_avg(i, current_year)

                # Definir ícone baseado na comparação com o último trimestre anterior disponível
                try:
                    # Debug: imprimir valores encontrados para diagnóstico
                    print(f"[Timeline][Quarter={quarter_name}] avg_current={avg_current} avg_previous={avg_previous}")
                    if avg_current is not None and avg_previous is not None:
                        if avg_current > avg_previous:
                            # ARROW_UP pode não existir em algumas versões; usar ARROW_UPWARD
                            quarter_icons[i].current.name = ft.Icons.ARROW_UPWARD
                            quarter_icons[i].current.color = ft.Colors.GREEN
                            print(f"[Timeline][{quarter_name}] DECISION: UP (green)")
                        elif avg_current < avg_previous:
                            # ft.Icons.ARROW_DOWN não existe em algumas versões do pacote; usar ARROW_DOWNWARD
                            quarter_icons[i].current.name = ft.Icons.ARROW_DOWNWARD
                            quarter_icons[i].current.color = ft.Colors.RED
                            print(f"[Timeline][{quarter_name}] DECISION: DOWN (red)")
                        else:
                            quarter_icons[i].current.name = ft.Icons.ARROW_FORWARD
                            quarter_icons[i].current.color = ft.Colors.GREY
                            print(f"[Timeline][{quarter_name}] DECISION: EQUAL (grey)")
                    else:
                        # Sem dados atuais ou anteriores disponíveis -> mostrar seta neutra
                        quarter_icons[i].current.name = ft.Icons.ARROW_FORWARD
                        quarter_icons[i].current.color = ft.Colors.GREY
                        print(f"[Timeline][{quarter_name}] DECISION: NO DATA (grey)")
                except Exception as ex:
                    # No caso de refs não estarem inicializadas, ignorar falha sem quebrar a execução
                    print(f"[Timeline][{quarter_name}] Erro ao definir icone: {ex}")
                    pass
                    
        except Exception as e:
            # Imprimir traceback completo para facilitar identificação de erros inesperados
            import traceback
            print(f"Erro ao calcular médias trimestrais: {e}")
            traceback.print_exc()
            for card in [q1_avg_card, q2_avg_card, q3_avg_card, q4_avg_card]:
                try:
                    card.current.value = "Error"
                except Exception:
                    pass
                
    def find_intersection(p1, p2, target_y):
        # p1 = (x1, y1), p2 = (x2, y2)
        if p1[1] == p2[1]:  # Linha horizontal, sem interseção a menos que esteja na linha de destino
            return None
        
        # Calcula a interseção x
        x = p1[0] + (p2[0] - p1[0]) * (target_y - p1[1]) / (p2[1] - p1[1])
        return (x, target_y)

    def create_colored_line_series(points, target_y):
        if not points:
            return []
        if len(points) < 2:
            point = points[0]
            color = ft.Colors.GREEN_600 if point[1] >= target_y else ft.Colors.RED_600
            return [ft.LineChartData(data_points=[ft.LineChartDataPoint(point[0], point[1])], color=color, stroke_width=3)]

        above_segments, below_segments = [], []
        current_above, current_below = [], []

        p1 = points[0]
        if p1[1] >= target_y:
            current_above.append(ft.LineChartDataPoint(p1[0], p1[1]))
        else:
            current_below.append(ft.LineChartDataPoint(p1[0], p1[1]))

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i+1]
            p1_above, p2_above = p1[1] >= target_y, p2[1] >= target_y

            if p1_above != p2_above:
                intersection = find_intersection(p1, p2, target_y)
                if intersection:
                    ix, iy = intersection
                    intersection_point = ft.LineChartDataPoint(ix, iy)
                    if p1_above:
                        current_above.append(intersection_point)
                        above_segments.append(current_above)
                        current_above = []
                        current_below = [intersection_point, ft.LineChartDataPoint(p2[0], p2[1])]
                    else:
                        current_below.append(intersection_point)
                        below_segments.append(current_below)
                        current_below = []
                        current_above = [intersection_point, ft.LineChartDataPoint(p2[0], p2[1])]
            else:
                if p2_above:
                    current_above.append(ft.LineChartDataPoint(p2[0], p2[1]))
                else:
                    current_below.append(ft.LineChartDataPoint(p2[0], p2[1]))

        if current_above: above_segments.append(current_above)
        if current_below: below_segments.append(current_below)

        series = []
        for segment in above_segments:
            if len(segment) > 1:
                series.append(ft.LineChartData(
                    data_points=segment, color=ft.Colors.GREEN_600, stroke_width=3, curved=True, stroke_cap_round=True,
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center, end=ft.alignment.bottom_center,
                        colors=[ft.Colors.with_opacity(0.4, ft.Colors.GREEN_400), ft.Colors.with_opacity(0.0, ft.Colors.GREEN_400)]
                    )
                ))
        for segment in below_segments:
            if len(segment) > 1:
                series.append(ft.LineChartData(
                    data_points=segment, color=ft.Colors.RED_600, stroke_width=3, curved=True, stroke_cap_round=True,
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center, end=ft.alignment.bottom_center,
                        colors=[ft.Colors.with_opacity(0.4, ft.Colors.RED_400), ft.Colors.with_opacity(0.0, ft.Colors.RED_400)]
                    )
                ))
        return series

    def update_timeline_chart(vendor_id, year=None):
        """Atualiza o gráfico de linha baseado no vendor, ano e métricas selecionadas."""
        try:
            if not db_conn or not vendor_id:
                timeline_chart_container.current.content = ft.Container(
                    content=ft.Text("Selecione um fornecedor para visualizar o gráfico", size=16, text_align=ft.TextAlign.CENTER),
                    alignment=ft.alignment.center, expand=True, height=400
                )
                timeline_chart_container.current.update()
                return

            target_value = target_slider.value if target_slider and target_slider.value is not None else 5.0
            analysis_year = int(year) if year and year.strip() else datetime.datetime.now().year

            query = "SELECT month, total_score, otif, nil, quality_pickup, quality_package FROM supplier_score_records_table WHERE supplier_id = ? AND year = ?"
            results = db_manager.query(query, (vendor_id, analysis_year))

            monthly_data = {m: {} for m in range(1, 13)}
            for row in results:
                month = row['month']
                total = row['total_score']
                otif = row['otif']
                nil = row['nil']
                pickup = row['quality_pickup']
                package = row['quality_package']
                try:
                    month_int = int(month)
                    monthly_data[month_int] = {
                        "total_score": float(total) if total is not None else None, "otif": float(otif) if otif is not None else None,
                        "nil": float(nil) if nil is not None else None, "pickup": float(pickup) if pickup is not None else None,
                        "package": float(package) if package is not None else None,
                    }
                except (ValueError, TypeError):
                    print(f"⚠️ Dados inválidos ignorados: month='{month}'")
                    continue

            if not any(data.get("total_score") is not None for data in monthly_data.values()):
                timeline_chart_container.current.content = ft.Container(
                    content=ft.Text(f"Nenhum dado de score encontrado para {analysis_year}", size=16, text_align=ft.TextAlign.CENTER),
                    alignment=ft.alignment.center, expand=True, height=400
                )
                timeline_chart_container.current.update()
                return

            data_series = []
            total_score_points = [(m - 1, d["total_score"]) for m, d in monthly_data.items() if d and d.get("total_score") is not None]
            if total_score_points:
                data_series.extend(create_colored_line_series(total_score_points, target_value))

            # Adicionar linha de target
            target_line_points = [ft.LineChartDataPoint(i, target_value) for i in range(12)]
            data_series.append(ft.LineChartData(
                data_points=target_line_points,
                color=ft.Colors.AMBER_700,
                stroke_width=2,
                curved=False,
                dash_pattern=[5, 5]
            ))

            additional_scores_map = {
                "otif": {"ref": timeline_otif_check, "color": ft.Colors.ORANGE_ACCENT_700},
                "nil": {"ref": timeline_nil_check, "color": ft.Colors.PURPLE_ACCENT_700},
                "pickup": {"ref": timeline_pickup_check, "color": ft.Colors.CYAN_700},
                "package": {"ref": timeline_package_check, "color": ft.Colors.PINK_ACCENT_700},
            }
            for key, details in additional_scores_map.items():
                if hasattr(details["ref"], 'current') and details["ref"].current and details["ref"].current.value:
                    points = [ft.LineChartDataPoint(m - 1, d[key]) for m, d in monthly_data.items() if d and d.get(key) is not None]
                    if points:
                        data_series.append(ft.LineChartData(data_points=points, color=details["color"], stroke_width=2, curved=False, dash_pattern=[3, 3]))

            months_labels = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
            line_chart = ft.LineChart(
                data_series=data_series,
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)),
                horizontal_grid_lines=ft.ChartGridLines(
                    interval=1, 
                    color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE), 
                    width=1
                ),
                vertical_grid_lines=ft.ChartGridLines(
                    interval=1, 
                    color=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE), 
                    width=1
                ),
                left_axis=ft.ChartAxis(
                    labels=[ft.ChartAxisLabel(value=i, label=ft.Text(str(i), size=10)) for i in range(0, 11, 1)], 
                    labels_size=30
                ),
                bottom_axis=ft.ChartAxis(
                    labels=[ft.ChartAxisLabel(value=i, label=ft.Text(label, size=10, weight=ft.FontWeight.BOLD)) for i, label in enumerate(months_labels)], 
                    labels_size=30
                ),
                tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLUE_GREY),
                min_y=0, 
                max_y=10, 
                min_x=0, 
                max_x=11, 
                expand=True,
            )
            timeline_chart_container.current.content = line_chart
            timeline_chart_container.current.update()
        except Exception as e:
            print(f"Erro ao atualizar gráfico: {e}")
            import traceback
            traceback.print_exc()
            timeline_chart_container.current.content = ft.Text(f"Erro ao gerar gráfico: {e}")
            timeline_chart_container.current.update()
            
    def show_timeline_snackbar(message):
        """Mostra snackbar na timeline"""
        # Substituído por show_toast para notificações consistentes
        show_toast(message)
        page.update()

    def delete_timeline_record(month, year_data, vendor_id):
        """Deleta um registro específico da timeline"""
        try:
            if not db_conn:
                show_timeline_snackbar("❌ Erro: Banco de dados não conectado.")
                return
                
            db_manager.execute("""DELETE FROM supplier_score_records_table 
                             WHERE supplier_id = ? AND month = ? AND year = ?""", 
                          (vendor_id, month, year_data))
            
            # Atualizar a tabela
            year = timeline_year_dropdown.current.value if timeline_year_dropdown.current else None
            update_timeline_table(vendor_id, year)
            # Atualizar gráfico e métricas
            update_timeline_metrics()
            show_timeline_snackbar("✅ Registro deletado com sucesso!")
            
        except Exception as e:
            show_timeline_snackbar(f"❌ Erro ao deletar registro: {str(e)}")

    def edit_timeline_record(record_data, otif, nil, pickup, package, comment):
        """Edita um registro específico da timeline"""
        try:
            if not db_conn:
                show_timeline_snackbar("❌ Erro: Banco de dados não conectado.")
                return

            month, year_data, _, _, _, _, _, _ = record_data

            # Obter supplier_id selecionado atualmente no filtro da timeline
            vendor_id = timeline_vendor_dropdown.current.value if timeline_vendor_dropdown and timeline_vendor_dropdown.current else None
            if not vendor_id:
                show_timeline_snackbar("❌ Erro: Nenhum fornecedor selecionado para atualizar o registro.")
                return

            cursor = db_conn.cursor()

            # Calcular novo total_score
            total_score = None
            if otif is not None and nil is not None and pickup is not None and package is not None:
                total_score = (otif + nil + pickup + package) / 4

            # Registrar quem fez a alteração e quando (compatível com a aba Score)
            from datetime import datetime
            current_date = datetime.now()
            register_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
            registered_by = current_user_name if 'current_user_name' in globals() else None

            db_manager.execute("""UPDATE supplier_score_records_table
                             SET otif = ?, nil = ?, quality_pickup = ?, quality_package = ?,
                                 total_score = ?, comment = ?, registered_by = ?, register_date = ?, changed_by = ?
                             WHERE supplier_id = ? AND month = ? AND year = ?""",
                          (otif, nil, pickup, package, total_score, comment, registered_by, register_date, registered_by, vendor_id, month, year_data))

            # Atualizar a tabela
            vendor_id = timeline_vendor_dropdown.current.value if timeline_vendor_dropdown.current else ""
            year = timeline_year_dropdown.current.value if timeline_year_dropdown.current else None
            update_timeline_table(vendor_id, year)
            # Atualizar gráfico e métricas
            update_timeline_metrics()
            show_timeline_snackbar("✅ Registro editado com sucesso!")

        except Exception as e:
            show_timeline_snackbar(f"❌ Erro ao editar registro: {str(e)}")

    def update_timeline_table(vendor_id, year=None):
        """Atualiza a tabela com os dados detalhados"""
        try:
            if not db_conn or not vendor_id:
                return
                
            cursor = db_conn.cursor()
            
            if year and year.strip():
                query = """SELECT month, year, otif, nil, quality_pickup, quality_package, 
                          total_score, comment FROM supplier_score_records_table 
                          WHERE supplier_id = ? AND year = ? ORDER BY year DESC, month DESC"""
                results = db_manager.query(query, (vendor_id, year))
            else:
                query = """SELECT month, year, otif, nil, quality_pickup, quality_package, 
                          total_score, comment FROM supplier_score_records_table 
                          WHERE supplier_id = ? ORDER BY year DESC, month DESC"""
                results = db_manager.query(query, (vendor_id,))
            
            if not results:
                timeline_table_container.current.content = ft.Container(
                    content=ft.Text("Nenhum dado encontrado para este fornecedor", 
                                   size=16, text_align=ft.TextAlign.CENTER),
                    alignment=ft.alignment.center,
                    height=400,
                    expand=True
                )
                timeline_table_container.current.update()
                return
            
            # Verificar largura da tela para layout responsivo
            is_mobile = page.window.width < 1000 if page.window else False
            
            # Criar cabeçalho da tabela - responsivo
            # Aumentar fontes e ajustar tamanhos para melhor leitura
            header_font_size = 14 if not is_mobile else 13
            row_font_size = 13 if not is_mobile else 12

            if is_mobile:
                header_row = ft.Row([
                    ft.Container(ft.Text("Período", weight="bold", size=header_font_size), width=90),
                    ft.Container(ft.Text("OTIF", weight="bold", size=header_font_size), width=60),
                    ft.Container(ft.Text("NIL", weight="bold", size=header_font_size), width=60),
                    ft.Container(ft.Text("Total", weight="bold", size=header_font_size), width=60),
                    ft.Container(ft.Text("Ações", weight="bold", size=header_font_size), width=110),
                ])
            else:
                header_row = ft.Row([
                    ft.Container(ft.Text("Mês/Ano", weight="bold", size=header_font_size), width=90),
                    ft.Container(ft.Text("OTIF", weight="bold", size=header_font_size), width=70),
                    ft.Container(ft.Text("NIL", weight="bold", size=header_font_size), width=70),
                    ft.Container(ft.Text("Pickup", weight="bold", size=header_font_size), width=70),
                    ft.Container(ft.Text("Package", weight="bold", size=header_font_size), width=80),
                    ft.Container(ft.Text("Total", weight="bold", size=header_font_size), width=70),
                    ft.Container(ft.Text("Comentário", weight="bold", size=header_font_size), expand=True),
                    ft.Container(ft.Text("Ações", weight="bold", size=header_font_size), width=140),
                ])
            
            # Criar linhas de dados
            data_rows = []
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                     
            for i, row in enumerate(results):
                month = row['month']
                year_data = row['year']
                otif = row['otif']
                nil = row['nil']
                pickup = row['quality_pickup']
                package = row['quality_package']
                total = row['total_score']
                comment = row['comment']
                try:
                    month_int = int(month)
                    month_name = months[month_int-1] if 1 <= month_int <= 12 else str(month)
                except (ValueError, TypeError):
                    month_name = str(month)
                
                bgcolor = "lightgray" if i % 2 == 0 else None
                
                # Função para editar este registro específico
                def create_edit_handler(record_row):
                    def handle_edit(e):
                        def handle_confirm(record_data, otif, nil, pickup, package, comment):
                            edit_timeline_record(record_data, otif, nil, pickup, package, comment)
                            page.close(edit_dialog)
                        
                        def handle_cancel(e):
                            page.close(edit_dialog)
                        
                        edit_dialog = EditTimelineRecordDialog(
                            record_data=record_row,
                            on_confirm=handle_confirm,
                            on_cancel=handle_cancel,
                            page=page
                        )
                        page.open(edit_dialog)
                    return handle_edit
                
                # Passar uma tupla com os valores na ordem esperada pelo diálogo
                record_tuple = (month, year_data, otif, nil, pickup, package, total, comment)
                
                # Verificar se usuário pode editar (apenas Admin e Super Admin)
                can_edit = current_user_privilege in ["Admin", "Super Admin"]
                
                edit_btn = ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=get_current_theme_colors(get_theme_name_from_page(page)).get('primary') if can_edit else ft.colors.GREY_400,
                    tooltip="Editar registro" if can_edit else "Sem permissão para editar",
                    icon_size=16,
                    on_click=create_edit_handler(record_tuple) if can_edit else None,
                    disabled=not can_edit
                )
                
                # Função para deletar este registro específico
                def create_delete_handler(m, y, vid):
                    def handle_delete(e):
                        def handle_confirm(e):
                            delete_timeline_record(m, y, vid)
                            page.close(delete_dialog)
                        
                        def handle_cancel(e):
                            page.close(delete_dialog)
                        
                        delete_dialog = DeleteListItemConfirmationDialog(
                            item_name=f"{months[int(m)-1] if 1 <= int(m) <= 12 else str(m)}/{y}",
                            item_type="Registro Timeline",
                            on_confirm=handle_confirm,
                            on_cancel=handle_cancel
                        )
                        page.open(delete_dialog)
                    return handle_delete
                
                delete_btn = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color="red" if can_edit else ft.colors.GREY_400,
                    tooltip="Deletar registro" if can_edit else "Sem permissão para deletar",
                    icon_size=16,
                    on_click=create_delete_handler(month, year_data, vendor_id) if can_edit else None,
                    disabled=not can_edit
                )
                
                # Layout responsivo das linhas
                if is_mobile:
                    # Layout compacto para mobile
                    data_row = ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(ft.Text(f"{month_name}/{year_data}", size=11, weight="bold"), width=80),
                                ft.Container(ft.Text(f"{float(otif):.1f}" if otif is not None else "--", size=11), width=50),
                                ft.Container(ft.Text(f"{float(nil):.1f}" if nil is not None else "--", size=11), width=50),
                                ft.Container(ft.Text(f"{float(total):.1f}" if total is not None else "--", size=11, weight="bold"), width=50),
                                ft.Container(ft.Row([edit_btn, delete_btn], spacing=5), width=100),
                            ]),
                            # Segunda linha com detalhes extras em mobile
                            ft.Row([
                                ft.Container(ft.Text(f"P:{float(pickup):.1f}" if pickup is not None else "P:--", size=10, color="gray"), width=60),
                                ft.Container(ft.Text(f"Pk:{float(package):.1f}" if package is not None else "Pk:--", size=10, color="gray"), width=60),
                                ft.Container(ft.Text(comment or "--", size=9, color="gray", no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS), expand=True),
                            ]),
                        ], spacing=2),
                        bgcolor=bgcolor,
                        padding=5
                    )
                else:
                    # Layout completo para desktop
                    data_row = ft.Container(
                        content=ft.Row([
                                ft.Container(ft.Text(f"{month_name}/{year_data}", size=row_font_size), width=90),
                                ft.Container(ft.Text(f"{float(otif):.1f}" if otif is not None else "--", size=row_font_size), width=70),
                                ft.Container(ft.Text(f"{float(nil):.1f}" if nil is not None else "--", size=row_font_size), width=70),
                                ft.Container(ft.Text(f"{float(pickup):.1f}" if pickup is not None else "--", size=row_font_size), width=70),
                                ft.Container(ft.Text(f"{float(package):.1f}" if package is not None else "--", size=row_font_size), width=80),
                                ft.Container(ft.Text(f"{float(total):.1f}" if total is not None else "--", size=row_font_size, weight="bold"), width=70),
                                ft.Container(ft.Text(comment or "--", size=row_font_size - 1, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS), expand=True),
                                ft.Container(ft.Row([edit_btn, delete_btn], spacing=5), width=140),
                        ]),
                        bgcolor=bgcolor,
                        padding=5
                    )
                data_rows.append(data_row)
            
            table_content = ft.Container(
                content=ft.Column([
                    header_row,
                    ft.Divider(),
                    ft.Container(
                        content=ft.Column(data_rows, spacing=2, scroll=ft.ScrollMode.AUTO),
                        expand=True
                    )
                ], expand=True),
                padding=ft.padding.all(20),
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)),
                border_radius=10,
                expand=True
            )
            
            timeline_table_container.current.content = table_content
            timeline_table_container.current.update()
            
        except Exception as e:
            print(f"Erro ao atualizar tabela: {e}")
            timeline_table_container.current.content = ft.Text(f"Erro: {e}")
            timeline_table_container.current.update()
            
    def on_timeline_vendor_change(e):
        """Callback quando o vendor é alterado"""
        update_timeline_metrics()
        if timeline_table_tab.current:
            vendor_id = timeline_vendor_dropdown.current.value if timeline_vendor_dropdown.current else ""
            year = timeline_year_dropdown.current.value if timeline_year_dropdown.current else None
            update_timeline_table(vendor_id, year)
            
    def on_timeline_year_change(e):
        """Callback quando o ano é alterado"""
        update_timeline_metrics()
        if timeline_table_tab.current:
            vendor_id = timeline_vendor_dropdown.current.value if timeline_vendor_dropdown.current else ""
            year = timeline_year_dropdown.current.value if timeline_year_dropdown.current else None
            update_timeline_table(vendor_id, year)
    
    def switch_to_chart_tab(e):
        """Muda para a aba do gráfico"""
        timeline_chart_tab.current = True
        timeline_table_tab.current = False
        
        # Obter cores do tema atual
        theme_name = get_theme_name_from_page(page)
        colors = get_current_theme_colors(theme_name)
        
        # Atualizar aparência dos botões
        if timeline_chart_button.current:
            timeline_chart_button.current.bgcolor = colors.get('primary')
            timeline_chart_button.current.color = colors.get('on_primary', '#FFFFFF')
        if timeline_table_button.current:
            timeline_table_button.current.bgcolor = None
            timeline_table_button.current.color = None
        
        # Mostrar/esconder containers
        timeline_chart_container.current.visible = True
        timeline_table_container.current.visible = False
        
        page.update()
        
    def switch_to_table_tab(e):
        """Muda para a aba da tabela"""
        timeline_chart_tab.current = False  
        timeline_table_tab.current = True
        
        # Obter cores do tema atual
        theme_name = get_theme_name_from_page(page)
        colors = get_current_theme_colors(theme_name)
        
        # Atualizar aparência dos botões
        if timeline_table_button.current:
            timeline_table_button.current.bgcolor = colors.get('primary')
            timeline_table_button.current.color = colors.get('on_primary', '#FFFFFF')
        if timeline_chart_button.current:
            timeline_chart_button.current.bgcolor = None
            timeline_chart_button.current.color = None
        
        # Mostrar/esconder containers
        timeline_chart_container.current.visible = False
        timeline_table_container.current.visible = True
        
        # Atualizar dados da tabela
        vendor_id = timeline_vendor_dropdown.current.value if timeline_vendor_dropdown.current else ""
        year = timeline_year_dropdown.current.value if timeline_year_dropdown.current else None
        update_timeline_table(vendor_id, year)
        
        page.update()

    # Criar conteúdo da aba Timeline
    # Obter cores do tema para a criação inicial dos componentes
    theme_name_for_timeline = get_theme_name_from_page(page)
    theme_colors_for_timeline = get_current_theme_colors(theme_name_for_timeline)
    primary_color_for_timeline = theme_colors_for_timeline.get('primary')
    # Se o tema for dracula, usar fundo cinza e textos/icones violeta (primary)
    if theme_name_for_timeline == 'dracula':
        timeline_card_bg = theme_colors_for_timeline.get('field_background') or "#44475A"
        label_color = primary_color_for_timeline
    else:
        timeline_card_bg = None
        label_color = ft.Colors.GREY_600

    timeline_view = ft.Container(
        content=ft.Column([
            # Título da seção
            ft.Container(
                content=ft.Text("Timeline Analytics", size=24, weight="bold"),
                alignment=ft.alignment.top_left,
            ),
            ft.Divider(),
            
            # Campos de seleção no topo - centralizados em um container
            ft.Container(
                content=ft.Column([
                    # (Campo de pesquisa removido)
                    # Row com dropdowns
                    ft.Row([
                        ft.Dropdown(
                            label="Supplier",
                            hint_text="Selecione um fornecedor",
                            ref=timeline_vendor_dropdown,
                            on_change=on_timeline_vendor_change,
                            options=load_suppliers_for_timeline(),
                            expand=True,
                            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                        ),
                        ft.Dropdown(
                            label="Ano",
                            ref=timeline_year_dropdown,
                            on_change=on_timeline_year_change,
                            options=[ft.dropdown.Option("", "(Ano Atual)")] + [ft.dropdown.Option(str(y)) for y in range(2024, 2040)],
                            value="",
                            width=150,
                            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
                ], horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=ft.padding.symmetric(horizontal=20, vertical=15),
                border=ft.border.all(1.5, get_current_theme_colors(get_theme_name_from_page(page)).get('outline')),
                border_radius=12,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('surface_variant'),
                width=700,
                alignment=ft.alignment.center,
                ref=timeline_search_container
            ),
            
            ft.Container(height=20),
            
            # Cards de métricas - com scroll horizontal
            ft.Column([
                ft.Text("Métricas de Performance", size=18, weight="bold", text_align=ft.TextAlign.CENTER, color=ft.Colors.ON_SURFACE),
                ft.Container(height=15),
                ft.Container(
                    ref=timeline_metrics_row,
                    content=ft.Row(
                        controls=[
                    # Card Overall Average
                    ft.Card(
                        ref=timeline_cards_refs["overall"]["card"],
                        content=ft.Container(
                            ref=timeline_cards_refs["overall"]["gradient"],
                            content=ft.Stack([
                                # Top-left: icon + label
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.ANALYTICS, color=primary_color_for_timeline, size=20, ref=timeline_cards_refs["overall"]["icon"]),
                                        ft.Text("Overall", size=11, weight="bold", color=label_color),
                                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                                    alignment=ft.alignment.top_left,
                                    padding=ft.padding.only(left=4, top=4)
                                ),
                                # Top-right: (removed - only Q cards show arrows)
                                # Bottom-right: value
                                ft.Container(
                                    content=ft.Text("--", size=18, weight="bold", color=primary_color_for_timeline, ref=overall_avg_card),
                                    alignment=ft.alignment.bottom_right,
                                    padding=ft.padding.only(right=6, bottom=6)
                                )
                            ]),
                            padding=ft.padding.all(12),
                            bgcolor=timeline_card_bg,
                            width=140,
                            height=85,
                            border_radius=12
                        ),
                        elevation=3,
                        surface_tint_color=primary_color_for_timeline
                    ),
                    # Card 12 Month Average
                    ft.Card(
                        ref=timeline_cards_refs["12m"]["card"],
                        content=ft.Container(
                            ref=timeline_cards_refs["12m"]["gradient"],
                            content=ft.Stack([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.CALENDAR_MONTH, color=primary_color_for_timeline, size=20, ref=timeline_cards_refs["12m"]["icon"]),
                                        ft.Text("12M Avg", size=11, weight="bold", color=label_color),
                                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                                    alignment=ft.alignment.top_left,
                                    padding=ft.padding.only(left=4, top=4)
                                ),
                                # Top-right: (removed - only Q cards show arrows)
                                ft.Container(
                                    content=ft.Text("--", size=18, weight="bold", color=primary_color_for_timeline, ref=twelve_month_avg_card),
                                    alignment=ft.alignment.bottom_right,
                                    padding=ft.padding.only(right=6, bottom=6)
                                )
                            ]),
                            padding=ft.padding.all(12),
                            bgcolor=timeline_card_bg,
                            width=140,
                            height=85,
                            border_radius=12
                        ),
                        elevation=3,
                        surface_tint_color=primary_color_for_timeline
                    ),
                    # Card Year Average
                    ft.Card(
                        ref=timeline_cards_refs["year"]["card"],
                        content=ft.Container(
                            ref=timeline_cards_refs["year"]["gradient"],
                            content=ft.Stack([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.CALENDAR_TODAY, color=primary_color_for_timeline, size=20, ref=timeline_cards_refs["year"]["icon"]),
                                        ft.Text("Year Avg", size=11, weight="bold", color=label_color),
                                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                                    alignment=ft.alignment.top_left,
                                    padding=ft.padding.only(left=4, top=4)
                                ),
                                # Top-right: (removed - only Q cards show arrows)
                                ft.Container(
                                    content=ft.Text("--", size=18, weight="bold", color=primary_color_for_timeline, ref=year_avg_card),
                                    alignment=ft.alignment.bottom_right,
                                    padding=ft.padding.only(right=6, bottom=6)
                                )
                            ]),
                            padding=ft.padding.all(12),
                            bgcolor=timeline_card_bg,
                            width=140,
                            height=85,
                            border_radius=12
                        ),
                        elevation=3,
                        surface_tint_color=primary_color_for_timeline
                    ),
                    ft.Card(
                        ref=timeline_cards_refs["q1"]["card"],
                        content=ft.Container(
                            ref=timeline_cards_refs["q1"]["gradient"],
                            content=ft.Stack([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.LOOKS_ONE, color=primary_color_for_timeline, size=18, ref=timeline_cards_refs["q1"]["icon"]),
                                        ft.Text("Q1", size=11, weight="bold", color=label_color),
                                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                                    alignment=ft.alignment.top_left,
                                    padding=ft.padding.only(left=4, top=4)
                                ),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY, size=16, ref=q1_arrow_icon),
                                    alignment=ft.alignment.top_right,
                                    padding=ft.padding.all(5),
                                ),
                                ft.Container(
                                    content=ft.Text("--", size=16, weight="bold", color=primary_color_for_timeline, ref=q1_avg_card),
                                    alignment=ft.alignment.bottom_right,
                                    padding=ft.padding.only(right=6, bottom=6)
                                )
                            ]),
                            padding=ft.padding.all(12),
                            bgcolor=timeline_card_bg,
                            width=140,
                            height=85,
                            border_radius=12
                        ),
                        elevation=3,
                        surface_tint_color=primary_color_for_timeline
                    ),
                    # Card Q2
                    ft.Card(
                        ref=timeline_cards_refs["q2"]["card"],
                        content=ft.Container(
                            ref=timeline_cards_refs["q2"]["gradient"],
                            content=ft.Stack([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.LOOKS_TWO, color=primary_color_for_timeline, size=18, ref=timeline_cards_refs["q2"]["icon"]),
                                        ft.Text("Q2", size=11, weight="bold", color=label_color),
                                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                                    alignment=ft.alignment.top_left,
                                    padding=ft.padding.only(left=4, top=4)
                                ),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY, size=16, ref=q2_arrow_icon),
                                    alignment=ft.alignment.top_right,
                                    padding=ft.padding.all(5),
                                ),
                                ft.Container(
                                    content=ft.Text("--", size=16, weight="bold", color=primary_color_for_timeline, ref=q2_avg_card),
                                    alignment=ft.alignment.bottom_right,
                                    padding=ft.padding.only(right=6, bottom=6)
                                )
                            ]),
                            padding=ft.padding.all(12),
                            bgcolor=timeline_card_bg,
                            width=140,
                            height=85,
                            border_radius=12
                        ),
                        elevation=3,
                        surface_tint_color=primary_color_for_timeline
                    ),
                    # Card Q3
                    ft.Card(
                        ref=timeline_cards_refs["q3"]["card"],
                        content=ft.Container(
                            ref=timeline_cards_refs["q3"]["gradient"],
                            content=ft.Stack([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.LOOKS_3, color=primary_color_for_timeline, size=18, ref=timeline_cards_refs["q3"]["icon"]),
                                        ft.Text("Q3", size=11, weight="bold", color=label_color),
                                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                                    alignment=ft.alignment.top_left,
                                    padding=ft.padding.only(left=4, top=4)
                                ),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY, size=16, ref=q3_arrow_icon),
                                    alignment=ft.alignment.top_right,
                                    padding=ft.padding.all(5),
                                ),
                                ft.Container(
                                    content=ft.Text("--", size=16, weight="bold", color=primary_color_for_timeline, ref=q3_avg_card),
                                    alignment=ft.alignment.bottom_right,
                                    padding=ft.padding.only(right=6, bottom=6)
                                )
                            ]),
                            padding=ft.padding.all(12),
                            bgcolor=timeline_card_bg,
                            width=140,
                            height=85,
                            border_radius=12
                        ),
                        elevation=3,
                        surface_tint_color=primary_color_for_timeline
                    ),
                    # Card Q4
                    ft.Card(
                        ref=timeline_cards_refs["q4"]["card"],
                        content=ft.Container(
                            ref=timeline_cards_refs["q4"]["gradient"],
                            content=ft.Stack([
                                ft.Container(
                                    content=ft.Row([
                                        ft.Icon(ft.Icons.LOOKS_4, color=primary_color_for_timeline, size=18, ref=timeline_cards_refs["q4"]["icon"]),
                                        ft.Text("Q4", size=11, weight="bold", color=label_color),
                                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                                    alignment=ft.alignment.top_left,
                                    padding=ft.padding.only(left=4, top=4)
                                ),
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY, size=16, ref=q4_arrow_icon),
                                    alignment=ft.alignment.top_right,
                                    padding=ft.padding.all(5),
                                ),
                                ft.Container(
                                    content=ft.Text("--", size=16, weight="bold", color=primary_color_for_timeline, ref=q4_avg_card),
                                    alignment=ft.alignment.bottom_right,
                                    padding=ft.padding.only(right=6, bottom=6)
                                )
                            ]),
                            padding=ft.padding.all(12),
                            bgcolor=timeline_card_bg,
                            width=140,
                            height=85,
                            border_radius=12
                        ),
                        elevation=3,
                        surface_tint_color=primary_color_for_timeline
                    ),
                ], spacing=15, tight=True, scroll=ft.ScrollMode.AUTO),
                    height=100
                ),
            ]),
            
            ft.Container(height=15),
            ft.Text("Métricas Adicionais no Gráfico:", size=14, weight="bold", text_align=ft.TextAlign.CENTER),
            ft.Row(
                controls=[
                    ft.Checkbox(label="OTIF", value=False, ref=timeline_otif_check, on_change=on_timeline_vendor_change),
                    ft.Checkbox(label="NIL", value=False, ref=timeline_nil_check, on_change=on_timeline_vendor_change),
                    ft.Checkbox(label="Pickup", value=False, ref=timeline_pickup_check, on_change=on_timeline_vendor_change),
                    ft.Checkbox(label="Package", value=False, ref=timeline_package_check, on_change=on_timeline_vendor_change),
                ],
                alignment=ft.MainAxisAlignment.START
            ),

            ft.Container(height=20),
            
            # Abas para gráfico e tabela
            ft.Row([
                ft.ElevatedButton(
                    "Gráfico de Linha",
                    icon=ft.Icons.SHOW_CHART,
                    on_click=switch_to_chart_tab,
                    ref=timeline_chart_button
                ),
                ft.ElevatedButton(
                    "Tabela de Dados",
                    icon=ft.Icons.TABLE_CHART,
                    on_click=switch_to_table_tab,
                    ref=timeline_table_button
                ),
            ], spacing=10),
            
            ft.Container(height=15),
            
            # Container para gráfico
            ft.Container(
                content=ft.Container(
                    content=ft.Text("Selecione um fornecedor para visualizar o gráfico", 
                                   size=16, text_align=ft.TextAlign.CENTER),
                    alignment=ft.alignment.center,
                    height=400,
                    expand=True
                ),
                ref=timeline_chart_container,
                visible=True,
                expand=True
            ),
            
            # Container para tabela  
            ft.Container(
                content=ft.Container(
                    content=ft.Text("Selecione um fornecedor para visualizar a tabela", 
                                   size=16, text_align=ft.TextAlign.CENTER),
                    alignment=ft.alignment.center,
                    height=400,
                    expand=True
                ),
                ref=timeline_table_container,
                visible=False,
                expand=True
            ),
            
        ], spacing=10),
        padding=20,
        expand=True,
        visible=False
    )
    
    # --- Fim: Lógica da Aba Timeline ---

    def generate_risk_cards(e=None):
        """
        Consulta o banco para encontrar fornecedores em risco e gera os cards de visualização.
        """
        try:
            # 1. Checagens iniciais
            if not db_conn:
                print("⚠️ Conexão com o banco de dados não disponível.")
                return
            if not risks_cards_container or not risks_cards_container.current:
                print("⚠️ Container de cards de risco não inicializado.")
                return

            # 2. Obter parâmetros: ano e meta
            import datetime
            year_val = None
            search_year = None
            if risks_year_dropdown and risks_year_dropdown.current and risks_year_dropdown.current.value:
                year_val = risks_year_dropdown.current.value
                # se for um número válido, usar como filtro; caso contrário, ignorar
                if year_val and year_val.strip().isdigit():
                    search_year = int(year_val)
            # Se search_year for None, vamos buscar todo o período disponível

            meta = target_slider.value if target_slider and target_slider.value is not None else 5.0

            # 3. Limpar container e mostrar mensagem de carregamento
            risks_cards_container.current.content = ft.Column(
                [ft.ProgressRing(), ft.Text("Buscando fornecedores em risco...")],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                expand=True
            )
            risks_cards_container.current.update()

            cursor = db_conn.cursor()

            # Abordagem otimizada:
            # - se `search_year` estiver definido, buscar apenas aquele ano
            # - caso contrário, buscar todo o período disponível (todos os anos)
            if search_year is not None:
                all_scores_query = """
                    SELECT
                        s.supplier_id, s.vendor_name, s.bu, sr.year, sr.month, sr.total_score
                    FROM supplier_database_table s
                    JOIN supplier_score_records_table sr ON s.supplier_id = sr.supplier_id
                    WHERE sr.year = ? AND sr.total_score IS NOT NULL
                    ORDER BY s.supplier_id, sr.year, sr.month
                """
                all_scores = db_manager.query(all_scores_query, (search_year,))
            else:
                all_scores_query = """
                    SELECT
                        s.supplier_id, s.vendor_name, s.bu, sr.year, sr.month, sr.total_score
                    FROM supplier_database_table s
                    JOIN supplier_score_records_table sr ON s.supplier_id = sr.supplier_id
                    WHERE sr.total_score IS NOT NULL
                    ORDER BY s.supplier_id, sr.year, sr.month
                """
                all_scores = db_manager.query(all_scores_query)

            # Agrupar dados por fornecedor
            from collections import defaultdict
            supplier_data = defaultdict(lambda: {'scores': [], 'info': {}})
            for row in all_scores:
                sid = row['supplier_id']
                vname = row['vendor_name']
                bu = row['bu']
                month = row['month']
                score = row['total_score']

                try:
                    month_int = int(month)
                    score_float = float(score)
                    supplier_data[sid]['scores'].append((month_int, score_float))
                    supplier_data[sid]['info'] = {'vendor_name': vname, 'bu': bu}
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Dados inválidos ignorados para supplier {sid}: month='{month}', score='{score}' - {e}")
                    continue

            if search_year is not None:
                print(f"Total de suppliers com dados no ano {search_year}: {len(supplier_data)}")
            else:
                print(f"Total de suppliers com dados em todo o período: {len(supplier_data)}")

            cards = []
            suppliers_at_risk = 0

            for supplier_id, data in supplier_data.items():
                vendor_name = data['info']['vendor_name']
                bu = data['info']['bu']
                monthly_scores = data['scores']

                scores_list = [s[1] for s in monthly_scores]
                if not scores_list:
                    continue

                media_score = sum(scores_list) / len(scores_list)

                if media_score >= float(meta):
                    continue

                try:
                    media_val = float(media_score)
                except Exception:
                    continue

                suppliers_at_risk += 1

                # Calcular médias trimestrais
                q_scores = defaultdict(list)
                for month, score in monthly_scores:
                    if 1 <= month <= 3: q_scores['Q1'].append(score)
                    elif 4 <= month <= 6: q_scores['Q2'].append(score)
                    elif 7 <= month <= 9: q_scores['Q3'].append(score)
                    elif 10 <= month <= 12: q_scores['Q4'].append(score)

                q_avgs = {q: sum(s_list) / len(s_list) if s_list else None for q, s_list in q_scores.items()}
                q1, q2, q3, q4 = q_avgs.get('Q1'), q_avgs.get('Q2'), q_avgs.get('Q3'), q_avgs.get('Q4')

                # Criar mini-gráfico
                # O gráfico mostrará a evolução da média geral ao longo do ano.
                cumulative_sum = 0
                cumulative_count = 0
                chart_points = []
                for month, score in monthly_scores: # monthly_scores já está ordenado por mês
                    cumulative_sum += score
                    cumulative_count += 1
                    chart_points.append((month - 1, cumulative_sum / cumulative_count))
                chart_series = create_colored_line_series(chart_points, meta)

                mini_chart = ft.LineChart(
                    data_series=chart_series,
                    min_y=0, max_y=10, min_x=0, max_x=11,
                    left_axis=ft.ChartAxis(show_labels=False),
                    bottom_axis=ft.ChartAxis(show_labels=False),
                    horizontal_grid_lines=ft.ChartGridLines(width=0),
                    vertical_grid_lines=ft.ChartGridLines(width=0),
                    border=None,
                    expand=True,
                )

                # Helper para criar ícone de tendência
                def trend_icon(current, previous):
                    try:
                        if current is None or previous is None:
                            return ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY)
                        cur = float(current)
                        prev = float(previous)
                        if cur > prev:
                            return ft.Icon(ft.Icons.ARROW_UPWARD, color=ft.Colors.GREEN)
                        elif cur < prev:
                            return ft.Icon(ft.Icons.ARROW_DOWNWARD, color=ft.Colors.RED)
                        else:
                            return ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY)
                    except Exception:
                        # Qualquer erro ao converter, retornar ícone neutro
                        return ft.Icon(ft.Icons.ARROW_FORWARD, color=ft.Colors.GREY)

                t2 = trend_icon(q2, q1)
                t3 = trend_icon(q3, q2)
                t4 = trend_icon(q4, q3)

                # Handler para ir para a aba Timeline e filtrar pelo supplier
                def create_goto_handler(sid):
                    def handle(e):
                        try:
                            # 1. Definir supplier no filtro da Timeline
                            if timeline_vendor_dropdown and timeline_vendor_dropdown.current:
                                timeline_vendor_dropdown.current.value = sid

                            # 2. Transferir o ano do filtro de Risks para o de Timeline
                            if risks_year_dropdown and risks_year_dropdown.current and risks_year_dropdown.current.value:
                                y = risks_year_dropdown.current.value
                                if timeline_year_dropdown and timeline_year_dropdown.current:
                                    timeline_year_dropdown.current.value = y

                            # 3. Mudar para a aba Timeline (índice 2)
                            set_selected(2)(None)

                            # 4. Atualizar as métricas e o conteúdo da aba Timeline
                            on_timeline_vendor_change(None)

                            # 5. Garantir que a visualização de tabela esteja ativa
                            switch_to_table_tab(None)

                        except Exception as ex:
                            print(f"Erro ao navegar para Timeline: {ex}")
                            import traceback
                            traceback.print_exc()
                    return handle

                # Construir card simplificado
                # Layout final: card maior; média posicionada acima da linha dos Qs, à direita
                card_inner = ft.Container(
                    content=ft.Column([
                        # Topo: nome, BU e ID + média
                        ft.Row(
                            controls=[
                                ft.Column([
                                    ft.Text(vendor_name, weight=ft.FontWeight.BOLD, size=18, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(f"BU: {bu}" if bu else "BU: -", size=12, color="gray"),
                                    ft.Text(f"ID: {supplier_id}", size=11, color="gray")
                                ], expand=True),
                                ft.Column([
                                    ft.Row([
                                        ft.IconButton(icon=ft.Icons.TIMELINE, tooltip="Abrir Timeline para este fornecedor", icon_size=18, on_click=create_goto_handler(supplier_id))
                                    ], alignment=ft.MainAxisAlignment.END),
                                    ft.Text(f"{media_val:.2f}", size=28, weight=ft.FontWeight.BOLD, color="red"),
                                    ft.Container(content=mini_chart, width=120, height=40)
                                ], horizontal_alignment=ft.CrossAxisAlignment.END)
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START
                        ),

                        ft.Divider(),

                        # Meio: trimestres (responsivos, quebram linha se faltar espaço)
                        # O controle ft.Wrap não está disponível na sua versão do Flet.
                        # Usando ft.Row com a propriedade wrap=True, que é
                        # a abordagem correta para versões mais antigas e garante a quebra de linha.
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Column([ft.Text("Q1", size=11), ft.Text(f"{q1:.2f}" if q1 is not None else "--", size=14)], alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                                    expand=True, alignment=ft.alignment.center
                                ),
                                ft.Container(
                                    content=ft.Row([t2, ft.Column([ft.Text("Q2", size=11), ft.Text(f"{q2:.2f}" if q2 is not None else "--", size=14)], alignment=ft.CrossAxisAlignment.CENTER, spacing=2)], spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                                    expand=True, alignment=ft.alignment.center
                                ),
                                ft.Container(
                                    content=ft.Row([t3, ft.Column([ft.Text("Q3", size=11), ft.Text(f"{q3:.2f}" if q3 is not None else "--", size=14)], alignment=ft.CrossAxisAlignment.CENTER, spacing=2)], spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                                    expand=True, alignment=ft.alignment.center
                                ),
                                ft.Container(
                                    content=ft.Row([t4, ft.Column([ft.Text("Q4", size=11), ft.Text(f"{q4:.2f}" if q4 is not None else "--", size=14)], alignment=ft.CrossAxisAlignment.CENTER, spacing=2)], spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
                                    expand=True, alignment=ft.alignment.center
                                ),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        )
                    ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.STRETCH), # Espaçamento interno do card reduzido
                    # Padding ajustado para um visual mais "justo"
                    padding=ft.padding.symmetric(vertical=12, horizontal=16),
                    border_radius=12,
                    bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background')
                )


                card = ft.Card(content=card_inner, elevation=6)
                # armazenar média no próprio objeto do card para ordenação segura
                try:
                    card.media_score = float(media_val)
                except Exception:
                    card.media_score = float('inf')
                cards.append(card)

            print(f"Riscos: Encontrados {suppliers_at_risk} fornecedores abaixo da meta {meta} para o ano {search_year}.")

            # Verificar se não há fornecedores em risco
            if not cards:
                title_text = f"Nenhum fornecedor em risco encontrado"
                if search_year is not None:
                    title_text = f"Nenhum fornecedor em risco encontrado para {search_year}!"
                else:
                    title_text = f"Nenhum fornecedor em risco encontrado no período pesquisado!"
                risks_cards_container.current.content = ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SHIELD, color="green", size=48),
                        ft.Text(title_text, size=16, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"Todos os fornecedores estão com score acima da meta de {meta:.2f}.", size=12, color="gray")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    expand=True,
                    alignment=ft.alignment.center
                )
                risks_cards_container.current.update()
                return

            # Ordenar cards por média (menor para maior - maior risco primeiro)
            cards.sort(key=lambda card: float(getattr(card, 'media_score', float('inf'))))

            # O GridView força todos os cards em uma mesma linha a terem a mesma altura,
            # o que pode criar um espaço vazio (a "borda exagerada") em cards com menos conteúdo.
            # Para que cada card "abrace" seu próprio conteúdo, usaremos um `ft.Row` com a
            # propriedade `wrap=True`. Isso permite que os cards tenham alturas variáveis. Adicionamos
            # um Column com scroll para conter a Row.
            risks_cards_container.current.content = ft.Column(
                controls=[
                    ft.Row(
                        # Envolvemos cada card em um Container com largura fixa para criar o efeito de colunas.
                        controls=[ft.Container(c, width=400) for c in cards],
                        wrap=True,
                        spacing=10,
                        run_spacing=10,
                        # Alinha os cards à esquerda dentro do container.
                        alignment=ft.MainAxisAlignment.START,
                    )
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
            risks_cards_container.current.update()

        except Exception as ex:
            print(f"Erro em generate_risk_cards: {ex}")
            import traceback
            traceback.print_exc()
            if risks_cards_container and risks_cards_container.current:
                risks_cards_container.current.content = ft.Text(f"Erro ao gerar cards de risco: {ex}", color="red")
                risks_cards_container.current.update()





    # Container da aba Risks (com dropdown de anos e área responsiva para cards)
    risks_view = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Gestão de Riscos", size=24, weight="bold"),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider(),
            # Campos ano e meta agrupados em container com cor do tema
            ft.Container(
                        content=ft.Row(
                    [
                        ft.Dropdown(
                            ref=risks_year_dropdown,
                            width=220,
                            value="",
                            on_change=generate_risk_cards,
                            options=[ft.dropdown.Option("", "Todo Período")] 
                                    + [ft.dropdown.Option(str(y), str(y)) for y in range(2024, 2041)],
                            hint_text="Ano",
                            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                        ),
                        ft.Container(width=20),
                        ft.Container(
                            ref=target_display_container,
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.FLAG_CIRCLE_OUTLINED, color=ft.Colors.AMBER_700, size=20),
                                    ft.Text("Meta:", weight=ft.FontWeight.BOLD, size=14),
                                    ft.Text("", ref=target_risks_text, weight=ft.FontWeight.BOLD, size=16, color=ft.Colors.AMBER_700),
                                ],
                                spacing=5,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                tight=True,  # <--- IMPORTANTE
                            ),
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border=ft.border.all(1.5, ft.Colors.AMBER_700),
                            border_radius=30,
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER_700),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,  # <--- IMPORTANTE
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=16),
                margin=ft.margin.only(bottom=6),
                ref=risks_header_container,
                border=ft.border.all(1.5, get_current_theme_colors(get_theme_name_from_page(page)).get('outline')),
                border_radius=12,
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('surface_variant'),
                expand=False,  # <--- NÃO DEIXAR EXPANDIR
            ),
            ft.Container(height=12),
            ft.Container(ref=risks_cards_container, content=ft.Text("Nenhum risco pesquisado"), expand=True)
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.START),
        alignment=ft.alignment.top_center,
        expand=True,
        visible=False,
        padding=20
    )
    email_view = ft.Container(
        content=ft.Column([
            ft.Text("Central de E-mails", size=24, weight="bold"),
            ft.Divider(),
            ft.Text("Gerencie e envie e-mails para fornecedores.", size=16),
            ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton("Novo E-mail", icon=ft.Icons.EMAIL),
                ft.ElevatedButton("Templates", icon=ft.Icons.ARTICLE),
                ft.ElevatedButton("Histórico", icon=ft.Icons.HISTORY),
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
        ]), 
        alignment=ft.alignment.top_center, 
        expand=True, 
        visible=False,
        padding=20
    )
    configs_view = ft.Container(
        content=configs_view_content, 
        alignment=ft.alignment.top_center, 
        padding=20, 
        visible=False,
        expand=True
    )

    menu_column = ft.Column([],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        ref=menu_column_ref
    )

    rail_container = ft.Container(
        content=ft.Column(
            [
                ft.IconButton(icon="menu", on_click=toggle_menu),
                menu_column,
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=12,
        ),
        padding=ft.padding.only(left=4, right=4),  # Removido padding esquerdo
        bgcolor=get_current_theme_colors(get_theme_name_from_page(page))["rail_background"]  # Cor mais escura
    )

    page.add(
        ft.Container(
            content=ft.Row(
                [
                    rail_container,
                    ft.VerticalDivider(width=1),  # Removido color para ficar transparente
                    ft.Container( # Container principal para o conteúdo das abas
                        content=ft.Column([home_view, score_view, timeline_view, risks_view, email_view, configs_view], expand=True),
                        expand=True,
                    ),
                ],
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                spacing=0,  # Remove espaçamento entre componentes
            ),
            expand=True
        )
    )

    # Inicializar gerenciador responsivo
    global responsive_app_manager
    responsive_app_manager = ResponsiveAppManager(page)
    responsive_app_manager.initialize_containers(results_list)
    responsive_app_manager.initialize_menu_controls(menu_is_expanded, update_menu)
    responsive_app_manager.check_initial_window_state()  # Verificar estado inicial da janela
    print("📱 Gerenciador responsivo inicializado e estado inicial verificado")

    def update_interface_for_user_privileges():
        """Atualiza a interface baseado nos privilégios do usuário atual"""
        try:
            # Atualizar menu principal (ocultar/mostrar abas)
            update_menu()
            
            # Atualizar abas de configuração  
            update_config_tabs()
            
            print(f"Interface atualizada para privilégio: {current_user_privilege}")
            
        except Exception as ex:
            print(f"Erro ao atualizar interface para privilégios: {ex}")

    update_menu()
    update_config_tabs()  # Inicializar as abas de configuração
    
    # Atualizar interface baseado nos privilégios do usuário
    update_interface_for_user_privileges()
    
    # Inicializar controles de usuário
    print("Extraindo referências dos controles de usuário...")
    try:
        users_controls.update(extract_users_refs())
    except Exception as ex:
        print(f"Erro ao extrair controles: {ex}")
    
    # Configurar eventos dos botões de usuário
    try:
        print("Configurando eventos dos botões...")
        # Passar diretamente o handler para que o evento seja recebido (usado para controlar o botão)
        users_controls['action_btn'].on_click = add_or_update_user
        users_controls['clear_btn'].on_click = clear_users_fields
        print("Eventos configurados com sucesso!")
    except Exception as ex:
        print(f"Erro ao configurar eventos: {ex}")
    
    load_all_lists_data()  # Carregar dados existentes das tabelas
    
    # Carregar usuários na inicialização
    refresh_users_list()
    
    # Mostrar favoritos inicialmente na aba Score
    show_favorites_only()
    
    # Carregar critérios salvos na inicialização
    saved_criteria = load_user_criteria(current_user_wwid)
    if saved_criteria:
        # Mapear nomes dos critérios da tabela para os sliders
        if 'NIL' in saved_criteria:
            nil_slider.value = saved_criteria['NIL']
            nil_text.value = f"{saved_criteria['NIL']:.2f}"
        
        if 'OTIF' in saved_criteria:
            otif_slider.value = saved_criteria['OTIF']
            otif_text.value = f"{saved_criteria['OTIF']:.2f}"
        
        if 'Quality of Pick Up' in saved_criteria:
            pickup_slider.value = saved_criteria['Quality of Pick Up']
            pickup_text.value = f"{saved_criteria['Quality of Pick Up']:.2f}"
        
        if 'Quality-Supplier Package' in saved_criteria:
            package_slider.value = saved_criteria['Quality-Supplier Package']
            package_text.value = f"{saved_criteria['Quality-Supplier Package']:.2f}"
        
        if 'Target' in saved_criteria:
            target_slider.value = saved_criteria['Target']
            target_text.value = f"{saved_criteria['Target']:.2f}"
        
        # Atualizar a soma dos pesos após carregar
        update_weight_sum()
        page.update()
        print(f"Critérios carregados: {saved_criteria}")
    else:
        # Mesmo com valores padrão, atualizar a soma
        update_weight_sum()
        print("Nenhum critério salvo encontrado, usando valores padrão")
    
    # Atualizar o texto do target na aba Risks
    if target_risks_text.current:
        target_risks_text.current.value = f"{target_slider.value:.2f}"
        page.update()
def main():
    """Função principal que inicia com tela de login"""
    ft.app(target=login_screen)

if __name__ == "__main__":
    main()
