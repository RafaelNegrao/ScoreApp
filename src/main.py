import flet as ft
import datetime
import sqlite3
import random
import string

# ===== CLASSE DE GERENCIAMENTO RESPONSIVO =====
class ResponsiveAppManager:
    """Classe para gerenciar o comportamento responsivo da aplicação"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.results_container = None
        self.is_maximized = False
        self.current_layout = "single"  # "single" ou "double"
        
        # Configurar listener de redimensionamento
        self.page.on_resized = self.on_window_resize
        self.page.on_window_event = self.on_window_event
    
    def initialize_containers(self, results_container):
        """Inicializa as referências dos containers que serão gerenciados"""
        self.results_container = results_container
        # Layout será aplicado quando houver cards para mostrar
    
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
            
            # Acessar a estrutura da aba Users através da página
            # A estrutura é: page -> Container -> Row -> [rail, divider, content_container] -> content_container -> Column[views] -> configs_view -> Column -> Stack -> users_content
            users_content_found = None
            
            try:
                # Navegação mais robusta pela estrutura
                page_container = self.page.controls[0]  # Container principal da página
                main_row = page_container.content  # Row principal (rail + content)
                content_container = main_row.controls[2]  # Container do conteúdo (terceiro elemento: rail, divider, content)
                views_column = content_container.content  # Column com as views (score, timeline, risks, email, configs)
                configs_view = views_column.controls[4]  # configs_view (índice 4)
                configs_main_column = configs_view.content  # Column principal do configs
                configs_stack_container = configs_main_column.controls[2]  # Container que contém o Stack
                configs_stack = configs_stack_container.content  # Stack com as abas de configuração
                users_content_found = configs_stack.controls[3]  # users_content (índice 3)
                
                print(f"🔍 Debug: Acessando users_content...")
                
            except (IndexError, AttributeError) as e:
                print(f"❌ Navegação para users_content falhou: {e}")
                # Vamos tentar uma abordagem alternativa usando busca recursiva
                try:
                    users_content_found = self._find_users_content_recursive(self.page.controls[0])
                    if users_content_found:
                        print("✅ users_content encontrado através de busca recursiva")
                    else:
                        print("❌ users_content não encontrado mesmo com busca recursiva")
                        return
                except Exception as e2:
                    print(f"❌ Busca recursiva também falhou: {e2}")
                    return
            
            if not users_content_found:
                print("❌ users_content não encontrado")
                return
            
            # Navegar pela estrutura interna do users_content
            try:
                main_column = users_content_found.content  # Column principal do users_content
                scroll_container = main_column.controls[2]  # Container com scroll (terceiro elemento)
                listview_container = scroll_container.content  # ListView
                form_container_wrapper = listview_container.controls[1]  # Container do formulário (segundo elemento)
                # Em algumas versões o container interno já é o Column do formulário
                form_container = getattr(form_container_wrapper, 'content', form_container_wrapper)
                
                print(f"🔍 Debug: Estrutura interna acessada com sucesso")
                
            except (IndexError, AttributeError) as e:
                print(f"❌ Erro ao acessar estrutura interna: {e}")
                return
            
            # Verificar se os elementos existem
            if not hasattr(form_container, 'controls') or len(form_container.controls) < 2:
                print(f"❌ form_container não tem controls suficientes: {len(form_container.controls) if hasattr(form_container, 'controls') else 'sem controls'}")
                return
            
            # Encontrar as duas primeiras linhas relevantes (Row/Column)
            rows = [c for c in form_container.controls if isinstance(c, (ft.Row, ft.Column))]
            if len(rows) < 2:
                print(f"❌ Não foi possível detectar as duas linhas do formulário (encontradas: {len(rows)})")
                return
            
            # Pegar as rows/columns existentes (Linha 1: WWID/Nome, Linha 2: Senha/Privilégio)
            row1 = rows[0]
            row2 = rows[1]
            
            # Verificar se são Rows/Columns e têm os controles esperados
            if not isinstance(row1, (ft.Row, ft.Column)) or not isinstance(row2, (ft.Row, ft.Column)):
                print(f"❌ Tipos incorretos: row1={type(row1)}, row2={type(row2)}")
                return
                
            if len(row1.controls) < 2 or len(row2.controls) < 2:
                print(f"❌ Controles insuficientes: row1={len(row1.controls)}, row2={len(row2.controls)}")
                return
            
            # Pegar os containers dos campos
            wwid_container = row1.controls[0]
            name_container = row1.controls[1]
            password_container = row2.controls[0] 
            privilege_container = row2.controls[1]
            
            if should_use_vertical_layout:
                # Layout vertical - reorganizar em Column (apenas se ainda não estiver)
                if isinstance(row1, ft.Row):
                    print("📱 Aplicando layout VERTICAL na aba Users")
                    
                    # Ajustar largura dos containers para centralização
                    wwid_container.width = 400
                    wwid_container.alignment = ft.alignment.center
                    name_container.width = 400
                    name_container.alignment = ft.alignment.center
                    password_container.width = 400
                    password_container.alignment = ft.alignment.center
                    privilege_container.width = 400
                    privilege_container.alignment = ft.alignment.center
                    
                    # Recriar as linhas como Column centralizada
                    new_row1 = ft.Column([
                        wwid_container,
                        name_container
                    ], 
                    alignment=ft.MainAxisAlignment.CENTER, 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15)
                    
                    new_row2 = ft.Column([
                        password_container,
                        privilege_container
                    ], 
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                    spacing=15)
                    
                    # Substituir as rows existentes
                    # Substituir mantendo a posição original das linhas
                    idx1 = form_container.controls.index(row1)
                    idx2 = form_container.controls.index(row2)
                    form_container.controls[idx1] = new_row1
                    form_container.controls[idx2] = new_row2
                    
                    # Atualizar a interface
                    users_content_found.update()
                    print("✅ Layout vertical centralizado aplicado com sucesso")
                
            else:
                # Layout horizontal - manter como Row (apenas se ainda não estiver)
                if isinstance(row1, ft.Column):
                    print("📱 Aplicando layout HORIZONTAL na aba Users")
                    
                    # Restaurar largura original dos containers
                    wwid_container.width = 350
                    wwid_container.alignment = ft.alignment.center
                    name_container.width = 350
                    name_container.alignment = ft.alignment.center
                    password_container.width = 350
                    password_container.alignment = ft.alignment.center
                    privilege_container.width = 350
                    privilege_container.alignment = ft.alignment.center
                    
                    # Converter de volta para Rows
                    new_row1 = ft.Row([
                        wwid_container,
                        name_container,
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    
                    new_row2 = ft.Row([
                        password_container,
                        privilege_container,
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
                    
                    idx1 = form_container.controls.index(row1)
                    idx2 = form_container.controls.index(row2)
                    form_container.controls[idx1] = new_row1
                    form_container.controls[idx2] = new_row2
                    
                    # Atualizar a interface
                    users_content_found.update()
                    print("✅ Layout horizontal aplicado com sucesso")
            
            print(f"📱 Layout da aba Users atualizado: {'vertical' if should_use_vertical_layout else 'horizontal'}")
            
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

# ===== DEFINIÇÕES SIMPLES DE TEMAS =====

def get_current_theme_colors(theme_name="white"):
    """Retorna as cores básicas do tema especificado"""
    if theme_name == "dark":
        return {
            "field_background": "#2C2C2C",
            "on_surface": "#E0E0E0", 
            "outline": "#555555",
            "card_background": "#1E1E1E",
            "primary": "#4EA1FF",
            "primary_container": "#3B3B3B",
            "surface_variant": "#181818",
            "rail_background": "#121212"
        }
    elif theme_name == "dracula":
        return {
            "field_background": "#44475A",
            "on_surface": "#F8F8F2",
            "outline": "#6272A4",
            "card_background": "#343746",
            "primary": "#BD93F9",
            "primary_container": "#6272A4",
            "surface_variant": "#2E303E",
            "rail_background": "#282A36"
        }
    else:  # white
        return {
            "field_background": "#FFFFFF",
            "on_surface": "#1C1C1C",
            "outline": "#CCCCCC",
            "card_background": "#F7F7F7",
            "primary": "#0066CC",
            "primary_container": "#E6F0FF",
            "surface_variant": "#FAFAFA",
            "rail_background": "#FFFFFF"
        }

def get_theme_name_from_page(page_ref=None):
    """Obtém o nome do tema atual da página"""
    if page_ref and hasattr(page_ref, 'data') and page_ref.data:
        return page_ref.data.get("theme_name", "white")
    return "white"

# ===== FIM DAS DEFINIÇÕES DE TEMAS =====

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
    colors = {
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
        border_color=colors['outline'],
        prefix_icon=ft.Icons.PERSON,
        value=saved_wwid  # Preencher com valor salvo
    )
    
    password_field = ft.TextField(
        label="Password", 
        password=True,
        can_reveal_password=True,
        width=320,
        border_radius=8,
        border_color=colors['outline'],
        prefix_icon=ft.Icons.LOCK,
        value=saved_password  # Preencher com valor salvo
    )
    
    # Checkbox Remember Me
    remember_me_checkbox = ft.Checkbox(
        label="Lembrar de mim",
        value=bool(saved_wwid and saved_password),  # Marcar se há credenciais salvas
        check_color=colors['primary']
    )
    
    error_text = ft.Text(
        "",
        color=colors['error'],
        text_align=ft.TextAlign.CENTER,
        size=12
    )
    
    login_button = ft.ElevatedButton(
        "Entrar",
        width=320,
        height=45,
        style=ft.ButtonStyle(
            bgcolor=colors['primary'],
            color=colors['on_primary'],
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=2
        ),
        icon=ft.Icons.LOGIN
    )
    
    def authenticate_user(wwid, password):
        """Verifica credenciais na tabela users_table"""
        try:
            conn = sqlite3.connect('db.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_wwid, user_password, user_privilege, otif, nil, pickup, package 
                FROM users_table 
                WHERE user_wwid = ? AND user_password = ?
            """, (wwid, password))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'wwid': result[0],
                    'password': result[1],
                    'privilege': result[2],
                    'otif': result[3] == '1' or result[3] == 1,
                    'nil': result[4] == '1' or result[4] == 1,
                    'pickup': result[5] == '1' or result[5] == 1,
                    'package': result[6] == '1' or result[6] == 1
                }
            return None
            
        except Exception as e:
            print(f"Erro na autenticação: {e}")
            return None
    
    def get_user_theme(wwid):
        """Busca tema do usuário na tabela theme_settings"""
        try:
            conn = sqlite3.connect('db.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT theme_mode FROM theme_settings WHERE user_wwid = ?", (wwid,))
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else "white"
            
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
                    color=colors['primary']
                ),
                ft.Container(height=12),
                ft.Text(
                    "Score App",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER,
                    color=colors['on_surface']
                ),
                ft.Text(
                    "Sistema de Avaliação de Fornecedores",
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                    color=colors['on_surface_variant']
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
        bgcolor=colors['surface'],
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
                color=get_current_theme_colors(self.page).get('on_surface'),
                border_color=get_current_theme_colors(self.page).get('outline')
            ),
            "supplier_name": ft.TextField(
                label="Supplier Name", 
                width=250,
                bgcolor=get_current_theme_colors(self.page).get('field_background'),
                color=get_current_theme_colors(self.page).get('on_surface'),
                border_color=get_current_theme_colors(self.page).get('outline')
            ),
            "supplier_category": ft.Container(
                content=ft.Dropdown(
                    label="Supplier Category",
                    width=250,
                    color=get_current_theme_colors(self.page).get('on_surface'),
                    border_color=get_current_theme_colors(self.page).get('outline'),
                    options=[
                        ft.dropdown.Option(v)
                        for v in (self.list_options.get('category') or ["", "Raw Materials", "Components", "Services", "Equipment"])
                    ],
                ),
                bgcolor=get_current_theme_colors(self.page).get('field_background'),
            ),
            
            # Informações de Contato
            "supplier_email": ft.TextField(
                label="Email", 
                width=250,
                bgcolor=get_current_theme_colors(self.page).get('field_background'),
                color=get_current_theme_colors(self.page).get('on_surface'),
                border_color=get_current_theme_colors(self.page).get('outline')
            ),
            "supplier_number": ft.TextField(
                label="Número", 
                width=250,
                bgcolor=get_current_theme_colors(self.page).get('field_background'),
                color=get_current_theme_colors(self.page).get('on_surface'),
                border_color=get_current_theme_colors(self.page).get('outline')
            ),
            
            # Configurações Organizacionais
            "bu": ft.Container(
                content=ft.Dropdown(
                    label="BU (Business Unit)",
                    width=200,
                    color=get_current_theme_colors(self.page).get('on_surface'),
                    border_color=get_current_theme_colors(self.page).get('outline'),
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
                    color=get_current_theme_colors(self.page).get('on_surface'),
                    border_color=get_current_theme_colors(self.page).get('outline'),
                    options=[ft.dropdown.Option(v) for v in ([""] + (self.list_options.get('planner') or []))]
                ),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
            ),

            "continuity": ft.Container(
                content=ft.Dropdown(
                    label="Continuity", 
                    width=200,
                    color=get_current_theme_colors(self.page).get('on_surface'),
                    border_color=get_current_theme_colors(self.page).get('outline'),
                    options=[ft.dropdown.Option(v) for v in ([""] + (self.list_options.get('continuity') or []))]
                ),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
            ),

            "sourcing": ft.Container(
                content=ft.Dropdown(
                    label="Sourcing",
                    width=200,
                    color=get_current_theme_colors(self.page).get('on_surface'),
                    border_color=get_current_theme_colors(self.page).get('outline'),
                    options=[ft.dropdown.Option(v) for v in ([""] + (self.list_options.get('sourcing') or []))]
                ),
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background')
            ),

            "sqie": ft.Container(
                content=ft.Dropdown(
                    label="SQIE",
                    width=200,
                    color=get_current_theme_colors(self.page).get('on_surface'),
                    border_color=get_current_theme_colors(self.page).get('outline'),
                    options=[ft.dropdown.Option(v) for v in ([""] + (self.list_options.get('sqie') or []))]
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
                ft.Row([self.fields["vendor_name"], self.fields["supplier_name"]], spacing=15),
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

# Variável global para o usuário atual
# Variáveis globais de usuário definidas no início do arquivo

# Configurações globais do aplicativo
app_settings = {'toast_duration': 3}

def load_app_settings(user_wwid=None):
    """Carrega as configurações gerais do aplicativo."""
    try:
        conn = sqlite3.connect("db.db", check_same_thread=False)
        cur = conn.cursor()
        if user_wwid:
            cur.execute("SELECT toast_duration FROM app_settings WHERE user_wwid = ? ORDER BY last_updated DESC LIMIT 1", (user_wwid,))
        else:
            cur.execute("SELECT toast_duration FROM app_settings WHERE user_wwid = 'default' ORDER BY last_updated DESC LIMIT 1")
        result = cur.fetchone()
        conn.close()
        if result:
            return {'toast_duration': result[0]}
        return {'toast_duration': 3}  # Valor padrão
    except Exception as ex:
        print(f"Erro ao carregar configurações do app: {ex}")
        return {'toast_duration': 3}

def save_app_settings(settings, user_wwid=None):
    """Salva as configurações gerais do aplicativo."""
    try:
        conn = sqlite3.connect("db.db", check_same_thread=False)
        cur = conn.cursor()
        user_id = user_wwid or 'default'
        
        cur.execute("SELECT id FROM app_settings WHERE user_wwid = ?", (user_id,))
        existing = cur.fetchone()
        
        if existing:
            # Atualizar configuração existente
            cur.execute("UPDATE app_settings SET toast_duration = ?, last_updated = CURRENT_TIMESTAMP WHERE user_wwid = ?", 
                      (settings['toast_duration'], user_id))
        else:
            # Inserir nova configuração
            cur.execute("INSERT INTO app_settings (user_wwid, toast_duration) VALUES (?, ?)", 
                      (user_id, settings['toast_duration']))
        
        conn.commit()
        conn.close()
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
        colors = get_current_theme_colors(get_theme_name_from_page(page))
        
        def on_hover(e):
            e.control.bgcolor = colors['surface_variant'] if e.data == "true" else (colors['primary_container'] if is_selected else None)
            e.control.update()
        row_controls = [
            ft.Icon(icon, color=colors['primary'] if is_selected else colors['on_surface'])
        ]
        if show_text:
            row_controls.append(
                ft.Text(
                    text,
                    size=16,
                    weight="bold" if is_selected else "normal",
                    color=colors['primary'] if is_selected else colors['on_surface'],
                )
            )
        # Corrige: passa a função handler sem executar
        return ft.Container(
            content=ft.Row(row_controls, alignment=ft.MainAxisAlignment.CENTER if not show_text else ft.MainAxisAlignment.START, spacing=15),
            padding=ft.padding.symmetric(horizontal=0 if not show_text else 10, vertical=10),
            border_radius=8,
            bgcolor=colors['primary_container'] if is_selected else None,
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
        if not db_conn or not wwid or not wwid.strip():
            return False
        try:
            cur = db_conn.cursor()
            cur.execute("SELECT 1 FROM users_table WHERE UPPER(user_wwid) = ?", (wwid.upper().strip(),))
            return cur.fetchone() is not None
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
            cur = db_conn.cursor()
            cur.execute("""
                SELECT user_name, user_password, user_privilege,
                       otif, nil, pickup, package
                FROM users_table 
                WHERE UPPER(user_wwid) = ?
            """, (wwid.upper(),))
            
            row = cur.fetchone()
            if row:
                name, password, privilege, otif, nil, pickup, package = row
                
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
            if not db_conn:
                return "light"
            
            cur = db_conn.cursor()
            if user_wwid:
                cur.execute("SELECT theme_mode FROM theme_settings WHERE user_wwid = ? ORDER BY last_updated DESC LIMIT 1", (user_wwid,))
            else:
                # Se não há usuário logado, pegar o último tema usado
                cur.execute("SELECT theme_mode FROM theme_settings ORDER BY last_updated DESC LIMIT 1")
            
            result = cur.fetchone()
            return result[0] if result else "light"
            
        except Exception as e:
            print(f"Erro ao carregar tema: {e}")
            return "light"

    def save_user_theme(theme_mode, user_wwid=None):
        """Salva o tema do usuário no banco de dados."""
        try:
            if not db_conn:
                return
            
            cur = db_conn.cursor()
            
            # Inserir ou atualizar tema
            if user_wwid:
                # Verificar se já existe configuração para este usuário
                cur.execute("SELECT id FROM theme_settings WHERE user_wwid = ?", (user_wwid,))
                if cur.fetchone():
                    # Atualizar existente
                    cur.execute("UPDATE theme_settings SET theme_mode = ?, last_updated = CURRENT_TIMESTAMP WHERE user_wwid = ?", 
                              (theme_mode, user_wwid))
                else:
                    # Inserir novo
                    cur.execute("INSERT INTO theme_settings (user_wwid, theme_mode) VALUES (?, ?)", 
                              (user_wwid, theme_mode))
            else:
                # Sem usuário específico, inserir como configuração geral
                cur.execute("INSERT INTO theme_settings (theme_mode) VALUES (?)", (theme_mode,))
            
            db_conn.commit()
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
        """Aplica o tema especificado à página - versão simplificada"""
        # Configurar cores básicas para cada tema
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

        # Salvar tema atual
        page.data["theme_name"] = theme_mode
        page.update()

        # Atualizar controles se não for inicialização
        if not is_initialization:
            try:
                refresh_users_list()
                update_menu()
                for key in ['planner', 'continuity', 'sourcing', 'sqie']:
                    refresh_list_ui(key)
                update_control_colors(page, theme_mode)
            except Exception as e:
                print(f"Erro ao atualizar listas: {e}")

    def update_control_colors(control, theme_name, depth=0):
        """Atualiza cores de controles recursivamente"""
        if depth > 20:
            return
        
        # Obter cores do tema
        colors = get_current_theme_colors(theme_name)
            
        # Atualizar TextField
        if isinstance(control, ft.TextField):
            control.bgcolor = colors.get('field_background')
            control.color = colors.get('on_surface')
            control.border_color = colors.get('outline')
            
        # Atualizar Dropdown  
        elif isinstance(control, ft.Dropdown):
            control.bgcolor = colors.get('field_background')
            control.color = colors.get('on_surface')
            control.border_color = colors.get('outline')
        
        # Atualizar Card
        elif isinstance(control, ft.Card):
            control.color = colors.get('card_background')
        
        # Atualizar Container
        elif isinstance(control, ft.Container):
            # Se tem bgcolor definido, atualizar conforme o contexto
            if hasattr(control, 'bgcolor') and control.bgcolor:
                # Para containers que provavelmente são fundos de campos
                if control.bgcolor in ['#FFFFFF', '#2C2C2C', '#44475A', 'surface_variant', 'field_background']:
                    control.bgcolor = colors.get('field_background')
        
        # Atualizar Text (para casos especiais)
        elif isinstance(control, ft.Text):
            # Preservar cores especiais como primary, mas atualizar cores básicas
            if hasattr(control, 'color') and control.color in ['on_surface', 'black', 'white']:
                control.color = colors.get('on_surface')
        
        # Recursão nos filhos
        if hasattr(control, 'controls'):
            for child in control.controls:
                update_control_colors(child, theme_name, depth + 1)
        elif hasattr(control, 'content') and control.content:
            update_control_colors(control.content, theme_name, depth + 1)

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
                    temp_conn = sqlite3.connect(db_path)
                    cursor = temp_conn.cursor()
                    
                    # Criar tabela se não existir
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS user_themes (
                            user_wwid TEXT PRIMARY KEY,
                            theme TEXT NOT NULL
                        )
                    ''')
                    
                    # Buscar tema do usuário
                    cursor.execute("SELECT theme FROM user_themes WHERE user_wwid = ?", (current_user_wwid,))
                    result = cursor.fetchone()
                    saved_theme = result[0] if result else None
                    temp_conn.close()
                    
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

    def show_toast(message, color="green"):
        """Mostra um toast com duração configurável."""
        global app_settings
        
        page.overlay.append(
            ft.Container(
                content=ft.Text(message, color="white", weight="bold"),
                bgcolor=color,
                padding=10,
                border_radius=5,
                top=50,
                right=20,
                animate_opacity=300,
            )
        )
        page.update()
        
        # Remover toast após a duração configurada
        import threading
        def remove_toast():
            import time
            time.sleep(app_settings['toast_duration'])
            if page.overlay:
                page.overlay.pop()
                page.update()
        
        threading.Thread(target=remove_toast, daemon=True).start()

    def load_user_criteria(user_wwid=None):
        """Carrega os pesos dos critérios salvos no banco."""
        if not db_conn:
            return None
        try:
            cur = db_conn.cursor()
            
            # Primeiro tenta carregar da criteria_settings (configurações personalizadas)
            if user_wwid:
                cur.execute("SELECT nil_weight, otif_weight, pickup_weight, package_weight, target_weight FROM criteria_settings WHERE user_wwid = ? ORDER BY last_updated DESC LIMIT 1", (user_wwid,))
                result = cur.fetchone()
                if result:
                    return {
                        'NIL': result[0],
                        'OTIF': result[1], 
                        'Quality of Pick Up': result[2],
                        'Quality-Supplier Package': result[3],
                        'Target': result[4]
                    }
            
            # Se não encontrou configurações personalizadas, carrega da criteria_table original
            print("Carregando critérios da tabela criteria_table...")
            cur.execute("SELECT criteria_category, value FROM criteria_table")
            results = cur.fetchall()
            
            criteria_data = {}
            for row in results:
                criteria_name = row[0]
                value_str = row[1]
                
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
        if not db_conn:
            return False
        try:
            cur = db_conn.cursor()
            if user_wwid:
                # Verificar se já existe configuração para este usuário
                cur.execute("SELECT id FROM criteria_settings WHERE user_wwid = ?", (user_wwid,))
                existing = cur.fetchone()
                
                if existing:
                    # Atualizar configuração existente
                    cur.execute("""UPDATE criteria_settings SET 
                                   nil_weight = ?, otif_weight = ?, pickup_weight = ?, 
                                   package_weight = ?, target_weight = ?, 
                                   last_updated = CURRENT_TIMESTAMP 
                                   WHERE user_wwid = ?""", 
                              (criteria_weights['NIL'], criteria_weights['OTIF'], 
                               criteria_weights['Quality of Pick Up'], criteria_weights['Quality-Supplier Package'], 
                               criteria_weights['Target'], user_wwid))
                else:
                    # Inserir nova configuração
                    cur.execute("""INSERT INTO criteria_settings 
                                   (user_wwid, nil_weight, otif_weight, pickup_weight, package_weight, target_weight) 
                                   VALUES (?, ?, ?, ?, ?, ?)""", 
                              (user_wwid, criteria_weights['NIL'], criteria_weights['OTIF'], 
                               criteria_weights['Quality of Pick Up'], criteria_weights['Quality-Supplier Package'], 
                               criteria_weights['Target']))
                
                db_conn.commit()
                return True
            return False
        except Exception as ex:
            print(f"Erro ao salvar critérios: {ex}")
            return False

    def theme_changed(e):
        global current_user_wwid
        theme_mode = e.control.value

        # Aplicar tema
        apply_theme(theme_mode)

        # Salvar tema no banco
        save_user_theme(theme_mode, current_user_wwid)

        # Atualizar os menus para refletir as novas cores
        update_menu()
        update_config_tabs()

        # Atualizar as listas para refletir as novas cores
        load_all_lists_data()
        load_users_full()

        # Atualizar cor do container dos campos de busca da aba score
        theme_colors = get_current_theme_colors(get_theme_name_from_page(page))
        score_form_container.bgcolor = theme_colors.get('field_background')
        score_form_container.update()

        # Atualizar cor do container do formulário de usuário
        users_form_container.bgcolor = theme_colors.get('field_background')
        users_form_container.border = ft.border.all(1, theme_colors.get('outline'))
        users_form_container.update()

        # Atualizar cor do menu lateral (rail_container)
        rail_container.bgcolor = theme_colors.get('rail_background')
        rail_container.update()

        # Atualizar cores dos dropdowns da aba score
        month_dropdown.bgcolor = theme_colors.get('field_background')
        month_dropdown.color = theme_colors.get('on_surface')
        month_dropdown.border_color = theme_colors.get('outline')
        month_dropdown.update()
        year_dropdown.bgcolor = theme_colors.get('field_background')
        year_dropdown.color = theme_colors.get('on_surface')
        year_dropdown.border_color = theme_colors.get('outline')
        year_dropdown.update()
        
        # Atualizar cores dos TextFields da aba score
        if search_field_ref.current:
            search_field_ref.current.bgcolor = theme_colors.get('field_background')
            search_field_ref.current.color = theme_colors.get('on_surface')
            search_field_ref.current.border_color = theme_colors.get('outline')
            search_field_ref.current.update()
        
        if selected_po.current:
            selected_po.current.bgcolor = theme_colors.get('field_background')
            selected_po.current.color = theme_colors.get('on_surface')
            selected_po.current.border_color = theme_colors.get('outline')
            selected_po.current.update()
        
        if selected_bu.current:
            selected_bu.current.bgcolor = theme_colors.get('field_background')
            selected_bu.current.color = theme_colors.get('on_surface')
            selected_bu.current.border_color = theme_colors.get('outline')
            selected_bu.current.update()
        
        # Atualizar cores dos TextFields das abas de configuração
        try:
            for config_type in ['sqie', 'continuity', 'planner', 'sourcing', 'bu', 'category']:
                if config_type in lists_controls:
                    # Atualizar campo 'input' (todos têm)
                    if 'input' in lists_controls[config_type]:
                        lists_controls[config_type]['input'].bgcolor = theme_colors.get('field_background')
                        lists_controls[config_type]['input'].color = theme_colors.get('on_surface')
                        lists_controls[config_type]['input'].border_color = theme_colors.get('outline')
                        lists_controls[config_type]['input'].update()
                    
                    # Atualizar campo 'alias' (se existir)
                    if 'alias' in lists_controls[config_type]:
                        lists_controls[config_type]['alias'].bgcolor = theme_colors.get('field_background')
                        lists_controls[config_type]['alias'].color = theme_colors.get('on_surface')
                        lists_controls[config_type]['alias'].border_color = theme_colors.get('outline')
                        lists_controls[config_type]['alias'].update()
                    
                    # Atualizar campo 'email' (se existir)
                    if 'email' in lists_controls[config_type]:
                        lists_controls[config_type]['email'].bgcolor = theme_colors.get('field_background')
                        lists_controls[config_type]['email'].color = theme_colors.get('on_surface')
                        lists_controls[config_type]['email'].border_color = theme_colors.get('outline')
                        lists_controls[config_type]['email'].update()
        except Exception as e:
            print(f"Erro ao atualizar cores dos campos de configuração: {e}")
        
        # Atualizar cores dos campos da aba Users 
        try:
            # Atualizar campos usando as refs específicas (manter transparentes)
            if wwid_field_ref.current:
                wwid_field_ref.current.filled = False  # Fundo transparente
                wwid_field_ref.current.color = theme_colors.get('on_surface')
                wwid_field_ref.current.border_color = theme_colors.get('outline')
                wwid_field_ref.current.update()
                
            if name_field_ref.current:
                name_field_ref.current.filled = False  # Fundo transparente
                name_field_ref.current.color = theme_colors.get('on_surface')
                name_field_ref.current.border_color = theme_colors.get('outline')
                name_field_ref.current.update()
                
            if password_field_ref.current:
                password_field_ref.current.filled = False  # Fundo transparente
                password_field_ref.current.color = theme_colors.get('on_surface')
                password_field_ref.current.border_color = theme_colors.get('outline')
                password_field_ref.current.update()
                
            if privilege_dropdown_ref.current:
                privilege_dropdown_ref.current.bgcolor = None  # Fundo transparente
                privilege_dropdown_ref.current.color = theme_colors.get('on_surface')
                privilege_dropdown_ref.current.border_color = theme_colors.get('outline')
                privilege_dropdown_ref.current.update()
                
        except Exception as e:
            print(f"Erro ao atualizar cores dos campos de usuário: {e}")

        # Atualizar cores dos campos da aba Log (suporta tanto Ref quanto controle direto)
        try:
            if 'log_controls' in globals() and log_controls:
                print("Debug: Atualizando cores dos controles de log.")
                for ctrl in log_controls.values():
                    control = resolve_control(ctrl)
                    if control is not None:
                        control.bgcolor = theme_colors.get('field_background')
                        control.color = theme_colors.get('on_surface')
                        control.border_color = theme_colors.get('outline')
                        if hasattr(control, 'update'):
                            control.update()
        except Exception as e:
            print(f"Erro ao atualizar cores dos campos de log: {e}")
        
        # Atualizar cor do campo de pesquisa de Suppliers
        try:
            if suppliers_search_field_ref.current:
                suppliers_search_field_ref.current.bgcolor = theme_colors.get('field_background')
                suppliers_search_field_ref.current.color = theme_colors.get('on_surface')
                suppliers_search_field_ref.current.border_color = theme_colors.get('outline')
                suppliers_search_field_ref.current.update()
        except Exception as e:
            print(f"Erro ao atualizar campo de pesquisa de suppliers: {e}")
        
        # Atualizar cores dos cards de Score existentes
        try:
            if responsive_app_manager and responsive_app_manager.results_container:
                print("🎨 Atualizando cores dos cards de Score...")
                update_control_colors(responsive_app_manager.results_container, theme_mode, 0)
                responsive_app_manager.results_container.update()
        except Exception as e:
            print(f"Erro ao atualizar cores dos cards de Score: {e}")
        
        # Atualizar cores dos cards de Suppliers existentes
        try:
            if 'suppliers_results_list' in globals() and suppliers_results_list and suppliers_results_list.controls:
                print("🎨 Atualizando cores dos cards de Suppliers...")
                for card in suppliers_results_list.controls:
                    update_control_colors(card, theme_mode, 0)
                suppliers_results_list.update()
        except Exception as e:
            print(f"Erro ao atualizar cores dos cards de Suppliers: {e}")
        
        # Mostrar confirmação
        page.snack_bar = ft.SnackBar(ft.Text(f"✅ Tema '{theme_mode}' aplicado e salvo!"))
        page.snack_bar.open = True
        page.update()

    def set_selected(idx):
        def handler(e):
            selected_index.current = idx
            score_view.visible = idx == 0
            timeline_view.visible = idx == 1
            risks_view.visible = idx == 2
            email_view.visible = idx == 3
            configs_view.visible = idx == 4
            update_menu()
            page.update()
        return handler

    # Dropdowns de mês e ano
    month_options = [ft.dropdown.Option(str(i).zfill(2), text=str(i)) for i in range(1, 13)]
    year_options = [ft.dropdown.Option(str(y)) for y in range(2025, 2036)]
    selected_month = ft.Ref()
    selected_year = ft.Ref()
    selected_bu = ft.Ref()
    selected_po = ft.Ref()

    def on_month_year_change(e):
        # A busca é chamada sempre que um dropdown muda. A função de busca verificará os valores.
        load_scores()

    def update_menu():
        if menu_column_ref.current:
            show_text = menu_is_expanded.current
            menu_column_ref.current.controls = [
                menu_item("score_outlined", "Score", 0, show_text),
                menu_item("timeline_outlined", "Timeline", 1, show_text),
                menu_item("warning_outlined", "Risks", 2, show_text),
                menu_item("email_outlined", "Email", 3, show_text),
                menu_item("settings_outlined", "Configs", 4, show_text),
            ]
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
        cursor = db_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wwid TEXT NOT NULL,
                supplier_id TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_wwid, supplier_id)
            )
        ''')
        db_conn.commit()
        print("Tabela de favoritos verificada/criada com sucesso!")

        # Criar tabelas de listas usadas em comboboxes (se não existirem)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sqie_table (
                sqie_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                alias TEXT UNIQUE,
                email TEXT,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS continuity_table (
                continuity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                alias TEXT UNIQUE,
                email TEXT,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planner_table (
                planner_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                alias TEXT UNIQUE,
                email TEXT,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sourcing_table (
                sourcing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                alias TEXT UNIQUE,
                email TEXT,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS business_unit_table (
                business_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bu TEXT UNIQUE,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories_table (
                categories_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT UNIQUE,
                register_date TIMESTAMP,
                registered_by TEXT
            )
        ''')
        
        # Criar tabela de usuários
        cursor.execute('''
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
                registered_by TEXT
            )
        ''')
        
        # Verificar se a coluna user_name existe, se não, adicionar
        try:
            cursor.execute("ALTER TABLE users_table ADD COLUMN user_name TEXT")
            print("Coluna user_name adicionada à tabela users_table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass  # Coluna já existe
            else:
                print(f"Erro ao adicionar coluna user_name: {e}")
        
        # Criar tabela de configurações de tema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS theme_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wwid TEXT,
                theme_mode TEXT NOT NULL DEFAULT 'light',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Criar tabela de configurações de critérios
        cursor.execute('''
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_wwid TEXT,
                toast_duration INTEGER DEFAULT 3,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Adicionar coluna target_weight se não existir (para bancos existentes)
        try:
            cursor.execute("ALTER TABLE criteria_settings ADD COLUMN target_weight REAL DEFAULT 0.2")
            print("Coluna target_weight adicionada à tabela criteria_settings")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                print(f"Erro ao adicionar coluna target_weight: {e}")
        
        db_conn.commit()
        
    except sqlite3.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        db_conn = None # Garante que o app não quebre se a conexão falhar

    def create_spinbox():
        """Cria um widget de spinbox customizado para notas."""
        score_field = ft.TextField(
            value="0.0", 
            text_align=ft.TextAlign.CENTER, 
            width=70, 
            border_radius=8,
            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
        )

        def adjust_score(e):
            try:
                current_value = float(score_field.value)
                if e.control.data == "+":
                    current_value += 0.5
                elif e.control.data == "-":
                    current_value -= 0.5
                score_field.value = str(round(max(0, current_value), 2)) # Impede notas negativas
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
            cursor = db_conn.cursor()
            
            # Carregar dados das tabelas com name, alias, email
            tables_with_email = {
                'sqie': ('sqie_table', 'name, alias, email'),
                'continuity': ('continuity_table', 'name, alias, email'), 
                'planner': ('planner_table', 'name, alias, email'),
                'sourcing': ('sourcing_table', 'name, alias, email')
            }
            
            for key, (table_name, columns) in tables_with_email.items():
                cursor.execute(f"SELECT {columns} FROM {table_name} ORDER BY alias")
                rows = cursor.fetchall()
                
                col = lists_controls[key]['list']
                col.controls.clear()
                
                if not rows:
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
                    for row in rows:
                        name, alias, email = row
                        is_selected = lists_controls[key]['selected_item'] == alias
                        colors = get_current_theme_colors(get_theme_name_from_page(page))
                        col.controls.append(
                            ft.Container(
                                content=ft.ListTile(
                                    title=ft.Text(f"{alias} - {name}", size=14, weight="bold", color=colors['primary'] if is_selected else colors['on_surface']),
                                    subtitle=ft.Text(email or "Email não informado", size=12, color="outline") if email else ft.Text("Email não informado", size=12, color="outline"),
                                    content_padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                    dense=True,
                                    on_click=lambda e, k=key, v=alias: select_list_item(k, v),
                                ),
                                bgcolor=colors['primary_container'] if is_selected else None,
                                border_radius=4,
                                padding=ft.padding.all(2)
                            )
                        )
            
            # Carregar Business Units
            cursor.execute("SELECT bu FROM business_unit_table ORDER BY bu")
            bu_rows = cursor.fetchall()
            
            bu_col = lists_controls['bu']['list']
            bu_col.controls.clear()
            
            if not bu_rows:
                bu_col.controls.append(
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
                for row in bu_rows:
                    is_selected = lists_controls['bu']['selected_item'] == row[0]
                    colors = get_current_theme_colors(get_theme_name_from_page(page))
                    bu_col.controls.append(
                        ft.Container(
                            content=ft.ListTile(
                                title=ft.Text(row[0], size=14, weight="bold", color=colors['primary'] if is_selected else colors['on_surface']),
                                content_padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                dense=True,
                                on_click=lambda e, v=row[0]: select_list_item('bu', v),
                            ),
                            bgcolor=colors['primary_container'] if is_selected else None,
                            border_radius=4,
                            padding=ft.padding.all(2)
                        )
                    )
            
            # Carregar Categories
            cursor.execute("SELECT category FROM categories_table ORDER BY category")
            category_rows = cursor.fetchall()
            
            category_col = lists_controls['category']['list']
            category_col.controls.clear()
            
            if not category_rows:
                category_col.controls.append(
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
                for row in category_rows:
                    is_selected = lists_controls['category']['selected_item'] == row[0]
                    colors = get_current_theme_colors(get_theme_name_from_page(page))
                    category_col.controls.append(
                        ft.Container(
                            content=ft.ListTile(
                                title=ft.Text(row[0], size=14, weight="bold", color=colors['primary'] if is_selected else colors['on_surface']),
                                content_padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                dense=True,
                                on_click=lambda e, v=row[0]: select_list_item('category', v),
                            ),
                            bgcolor=colors['primary_container'] if is_selected else None,
                            border_radius=4,
                            padding=ft.padding.all(2)
                        )
                    )
                    
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
        if not db_conn:
            return
        
        try:
            cursor = db_conn.cursor()
            colors = get_current_theme_colors(get_theme_name_from_page(page))
            
            if key in ['sqie', 'continuity', 'planner', 'sourcing']:
                # Tabelas com name, alias, email
                table_name = f"{key}_table"
                cursor.execute(f"SELECT name, alias, email FROM {table_name} ORDER BY alias")
                rows = cursor.fetchall()
                
                col = lists_controls[key]['list']
                col.controls.clear()
                
                if not rows:
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
                    for row in rows:
                        name, alias, email = row
                        is_selected = lists_controls[key]['selected_item'] == alias
                        
                        # Usar Container para garantir que o bgcolor funcione
                        col.controls.append(
                            ft.Container(
                                content=ft.ListTile(
                                    title=ft.Text(f"{alias} - {name}", size=14, weight="bold", color=colors['primary'] if is_selected else colors['on_surface']),
                                    subtitle=ft.Text(email or "Email não informado", size=12, color="outline") if email else ft.Text("Email não informado", size=12, color="outline"),
                                    content_padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                    dense=True,
                                    on_click=lambda e, k=key, v=alias: select_list_item(k, v),
                                ),
                                bgcolor=colors['primary_container'] if is_selected else None,
                                border_radius=4,
                                padding=ft.padding.all(2)
                            )
                        )
                        
            elif key == 'bu':
                # Business Units
                cursor.execute("SELECT bu FROM business_unit_table ORDER BY bu")
                rows = cursor.fetchall()
                
                col = lists_controls[key]['list']
                col.controls.clear()
                
                if not rows:
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
                    for row in rows:
                        is_selected = lists_controls[key]['selected_item'] == row[0]
                        col.controls.append(
                            ft.Container(
                                content=ft.ListTile(
                                    title=ft.Text(row[0], size=14, weight="bold", color=colors['primary'] if is_selected else colors['on_surface']),
                                    content_padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                    dense=True,
                                    on_click=lambda e, v=row[0]: select_list_item('bu', v),
                                ),
                                bgcolor=colors['primary_container'] if is_selected else None,
                                border_radius=4,
                                padding=ft.padding.all(2)
                            )
                        )
                        
            elif key == 'category':
                # Categories
                cursor.execute("SELECT category FROM categories_table ORDER BY category")
                rows = cursor.fetchall()
                
                col = lists_controls[key]['list']
                col.controls.clear()
                
                if not rows:
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
                    for row in rows:
                        is_selected = lists_controls[key]['selected_item'] == row[0]
                        col.controls.append(
                            ft.Container(
                                content=ft.ListTile(
                                    title=ft.Text(row[0], size=14, weight="bold", color=colors['primary'] if is_selected else colors['on_surface']),
                                    content_padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                    dense=True,
                                    on_click=lambda e, v=row[0]: select_list_item('category', v),
                                ),
                                bgcolor=colors['primary_container'] if is_selected else None,
                                border_radius=4,
                                padding=ft.padding.all(2)
                            )
                        )
                        
        except Exception as e:
            print(f"Erro ao recarregar lista {key}: {e}")

    def load_list_options(table_name, column_name):
        """Retorna lista de tuplas (value, text) para popular Dropdowns."""
        if not db_conn:
            return []
        try:
            cur = db_conn.cursor()
            if table_name in ("business_unit_table", "categories_table"):
                # Tabelas que só têm uma coluna principal
                cur.execute(f"SELECT {column_name} FROM {table_name} ORDER BY {column_name}")
                rows = cur.fetchall()
                options = [r[0] for r in rows if r[0]]  # Filtrar valores nulos/vazios
                return options if options else []  # Não retorna lista vazia se não há dados
            else:
                # Para tabelas com name, alias, email (sqie, continuity, planner, sourcing)
                # Usar apenas o campo 'name' como solicitado
                cur.execute(f"SELECT name FROM {table_name} WHERE name IS NOT NULL AND name != '' ORDER BY name")
                rows = cur.fetchall()
                options = [r[0] for r in rows if r[0]]  # Filtrar valores nulos/vazios
                return options if options else []  # Não retorna lista vazia se não há dados
        except Exception as ex:
            print(f"Erro ao carregar opções de {table_name}: {ex}")
            return []

    def load_list_items_full(table_name):
        """Retorna dados completos dos itens da lista com name, alias, email."""
        if not db_conn:
            return []
        try:
            cur = db_conn.cursor()
            if table_name in ("business_unit_table",):
                cur.execute(f"SELECT bu FROM {table_name} ORDER BY bu")
                rows = cur.fetchall()
                return [{"display": r[0], "alias": r[0]} for r in rows]
            elif table_name == "categories_table":
                cur.execute(f"SELECT category FROM {table_name} ORDER BY category")
                rows = cur.fetchall()
                return [{"display": r[0], "alias": r[0]} for r in rows]
            else:
                # Para tabelas com name, alias, email
                cur.execute(f"SELECT name, alias, email FROM {table_name} ORDER BY alias")
                rows = cur.fetchall()
                items = []
                for row in rows:
                    name, alias, email = row
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
        if not db_conn:
            raise RuntimeError("DB não conectado")
        cur = db_conn.cursor()
        placeholders = ','.join(['?'] * len(values))
        cols = ','.join(columns)
        q = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        cur.execute(q, values)
        db_conn.commit()

    def delete_list_item_by_alias(table_name, alias_column, alias):
        if not db_conn:
            raise RuntimeError("DB não conectado")
        cur = db_conn.cursor()
        q = f"DELETE FROM {table_name} WHERE {alias_column} = ?"
        cur.execute(q, (alias,))
        db_conn.commit()
    
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
            score_sliders = card.data.get("score_sliders")
            score_texts = card.data.get("score_texts")
            
            if not score_sliders or not score_texts:
                continue
            
            try:
                cursor = db_conn.cursor()
                query = """
                    SELECT otif, quality_pickup, quality_package, nil, comment
                    FROM supplier_score_records_table
                    WHERE supplier_id = ? AND month = ? AND year = ?
                """
                cursor.execute(query, (supplier_id, int(month_val), int(year_val)))
                score_record = cursor.fetchone()

                if score_record:
                    # Mapeamento direto: OTIF, Pickup, Package, NIL, Comment
                    scores = {
                        "OTIF": score_record[0] if score_record[0] is not None else 0.0,
                        "Pickup": score_record[1] if score_record[1] is not None else 0.0,
                        "Package": score_record[2] if score_record[2] is not None else 0.0,
                        "NIL": score_record[3] if score_record[3] is not None else 0.0,
                    }
                    comment_value = score_record[4] if score_record[4] is not None else ""
                    
                    # Atualizar valores dos sliders e textos
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
        Tuple esperada: (supplier_id, vendor_name, BU, supplier_status, supplier_number)
        """
        supplier_id = record[0] if len(record) > 0 else "?"
        vendor_name = record[1] if len(record) > 1 else "?"
        bu = record[2] if len(record) > 2 else "?"
        status = record[3] if len(record) > 3 else "?"
        supplier_number = record[4] if len(record) > 4 else "?"

        print(f"Criando card para: {vendor_name} (ID: {supplier_id})")
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
            
            # Apenas criar o campo se o usuário tiver permissão
            if has_permission:
                print(f"    ✅ Criando campo {ui_name}")
                spinbox = create_spinbox()
                spinbox_field = spinbox.controls[1]  # O TextField é o segundo controle
                spinbox_refs[ui_name] = spinbox_field
                
                spinboxes_rows.append(
                    ft.Row(
                        [ft.Text(ui_name, weight="bold", width=80), spinbox], 
                        alignment=ft.MainAxisAlignment.START, 
                        spacing=10
                    )
                )
            else:
                print(f"    ❌ Ocultando campo {ui_name}")

        comment_field = ft.TextField(
            label="Comentário", 
            expand=True, 
            border_radius=8, 
            multiline=True, 
            min_lines=4, 
            max_lines=6,
            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
        )

        def save_score(e):
            if not db_conn:
                page.snack_bar = ft.SnackBar(ft.Text("Erro: Banco de dados não conectado."), open=True)
                page.update()
                return
                
            if not selected_month.current or not selected_year.current:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione mês e ano antes de salvar."), open=True)
                page.update()
                return
                
            month_val = selected_month.current.value
            year_val = selected_year.current.value
            
            if not month_val or not year_val:
                page.snack_bar = ft.SnackBar(ft.Text("Selecione mês e ano antes de salvar."), open=True)
                page.update()
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
                page.snack_bar = ft.SnackBar(ft.Text("Valores de mês e ano inválidos."), open=True)
                page.update()
                return
                
            # Prevenir salvamento de scores para meses futuros
            if (ano_int > ano_atual) or (ano_int == ano_atual and mes_int > mes_atual):
                page.snack_bar = ft.SnackBar(ft.Text("Não é possível salvar scores para meses futuros."), open=True)
                page.update()
                return

            try:
                cursor = db_conn.cursor()
                
                # Buscar critérios atuais da tabela criteria_table
                cursor.execute("SELECT criteria_category, value FROM criteria_table")
                criteria_results = cursor.fetchall()
                criteria_values = {}
                for row in criteria_results:
                    criteria_name = row[0]
                    criteria_value = float(row[1])
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
                    page.snack_bar = ft.SnackBar(ft.Text("Você não tem permissão para salvar nenhum campo."), open=True)
                    page.update()
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
                cursor.execute(check_query, (supplier_id, int(month_val), int(year_val)))
                result = cursor.fetchone()
                exists = result[0] > 0
                current_registered_by = result[1] if exists and result[1] else ""
                
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
                        cursor.execute(update_query, values)
                else:
                    # Inserir novo registro com campos zerados para campos sem permissão
                    insert_query = """
                        INSERT INTO supplier_score_records_table 
                        (supplier_id, month, year, otif, quality_pickup, quality_package, nil, total_score, registered_by, register_date, changed_by, supplier_name, comment)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, (
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
                
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"✅ Score salvo para {vendor_name} ({month_val}/{year_val}) - Total: {total_score:.1f}"), 
                    open=True
                )
                
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao salvar: {str(ex)}"), open=True)
                print(f"❌ Erro detalhado ao salvar dados:")
                print(f"   Fornecedor: {vendor_name} (ID: {supplier_id})")
                print(f"   Período: {month_val}/{year_val}")
                print(f"   Erro: {ex}")
                import traceback
                traceback.print_exc()
            
            page.update()

        def toggle_favorite(e):
            e.control.selected = not e.control.selected
            print(f"Favorito -> ID {supplier_id}: {e.control.selected}")
            e.control.update()

        notas_col = ft.Column(spinboxes_rows, spacing=8)

        info_col = ft.Column([
            ft.Text(vendor_name, weight="bold", size=16),
            ft.Text(f"BU: {bu}"),
            ft.Text(f"PO: {supplier_number}"),
            ft.Text(f"ID: {supplier_id}"),
            ft.Text(f"Status: {status}", color="green" if str(status).strip() == "Active" else "red" if str(status).strip() == "Inactive" else "gray"),
        ], width=210, spacing=4, alignment=ft.MainAxisAlignment.START)

        # Reorganizar a estrutura do card para posicionar os botões no canto inferior direito
        left_section = ft.Row([
            info_col, 
            ft.VerticalDivider(), 
            notas_col, 
            ft.VerticalDivider()
        ], alignment=ft.MainAxisAlignment.START)

        # Seção direita com comentário e botões alinhados
        right_section = ft.Column([
            comment_field,
            ft.Container(height=20),  # Espaçamento
            ft.Row([
                ft.Container(expand=True),  # Empurra os botões para a direita
                ft.IconButton(
                    icon=ft.Icons.FAVORITE_BORDER, 
                    selected_icon=ft.Icons.FAVORITE, 
                    on_click=toggle_favorite, 
                    tooltip="Favoritar"
                ),
                ft.ElevatedButton("Salvar", on_click=save_score, icon=ft.Icons.SAVE),
            ], alignment=ft.MainAxisAlignment.END, tight=True)
        ], expand=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        card = ft.Card(
            content=ft.Container(
                padding=15,
                content=ft.Row([
                    left_section,
                    right_section
                ], vertical_alignment=ft.CrossAxisAlignment.STRETCH, expand=True)
            ),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background')
        )
        
        # Anexar dados ao card
        card.data = {
            "supplier_id": supplier_id, 
            "spinbox_refs": spinbox_refs,
            "comment_field": comment_field
        }
        
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
        supplier_id = record[0] if len(record) > 0 else "?"
        vendor_name = record[1] if len(record) > 1 else "?"
        bu = record[2] if len(record) > 2 else "?"
        status = record[3] if len(record) > 3 else "?"
        supplier_number = record[4] if len(record) > 4 else "?"

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
            
            # Apenas criar o campo se o usuário tiver permissão
            if has_permission:
                print(f"    ✅ Criando slider {ui_name}")
                slider_row, slider_control, text_control = create_score_slider()
                
                score_sliders[ui_name] = slider_control
                score_texts[ui_name] = text_control
                
                row = ft.Row([
                    ft.Container(
                        content=ft.Text(ui_name, weight="bold", size=14),
                        alignment=ft.alignment.center_left,
                        expand=1
                    ),
                    slider_row
                ], 
                alignment=ft.MainAxisAlignment.START, 
                spacing=10,
                tight=True
                )
                slider_row.expand = 2
                score_rows.append(row)
            else:
                print(f"    ❌ Ocultando slider {ui_name}")

        # Campo de comentário mais simples
        comment_field = ft.TextField(
            label="Comentário",
            multiline=True,
            min_lines=2,
            max_lines=4,
            dense=True,
            border_radius=8,
            bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
            border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
        )

        # Estado do favorito
        is_favorite = ft.Ref[bool]()
        is_favorite.current = False

        # Verificar se já está nos favoritos ao criar o card
        def check_favorite_status():
            user_wwid = "default_user"  # TODO: Implementar sistema de usuários
            if not db_conn:
                return False
            try:
                cursor = db_conn.cursor()
                check_query = "SELECT COUNT(*) FROM favorites_table WHERE user_wwid=? AND supplier_id=?"
                cursor.execute(check_query, (user_wwid, supplier_id))
                return cursor.fetchone()[0] > 0
            except sqlite3.Error:
                return False

        # Definir estado inicial do favorito
        is_favorite.current = check_favorite_status()

        def save_score(e):
            if not db_conn:
                show_snackbar("Erro: Banco de dados não conectado.")
                return
                
            if not selected_month.current or not selected_year.current:
                show_snackbar("Selecione mês e ano antes de salvar.")
                return
                
            month_val = selected_month.current.value
            year_val = selected_year.current.value
            
            if not month_val or not year_val:
                show_snackbar("Selecione mês e ano antes de salvar.")
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
                show_snackbar("Valores de mês e ano inválidos.")
                return
                
            # Prevenir salvamento de scores para meses futuros
            if (ano_int > ano_atual) or (ano_int == ano_atual and mes_int > mes_atual):
                show_snackbar("Não é possível salvar scores para meses futuros.")
                return

            try:
                # Desabilitar botão temporariamente
                e.control.disabled = True
                e.control.text = "Salvando..."
                page.update()
                
                cursor = db_conn.cursor()
                
                # Buscar critérios atuais da tabela criteria_table
                cursor.execute("SELECT criteria_category, value FROM criteria_table")
                criteria_results = cursor.fetchall()
                criteria_values = {}
                for row in criteria_results:
                    criteria_name = row[0]
                    criteria_value = float(row[1])
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
                    show_snackbar("Você não tem permissão para salvar nenhum campo.")
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
                cursor.execute(check_query, (supplier_id, int(month_val), int(year_val)))
                result = cursor.fetchone()
                exists = result[0] > 0
                current_registered_by = result[1] if exists and result[1] else ""
                
                # Construir registered_by acumulativo - FUNÇÃO SLIDER
                saved_field_names = []
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
                        cursor.execute(update_query, update_values)
                else:
                    # Inserir novo registro com campos zerados para campos sem permissão
                    insert_query = """
                        INSERT INTO supplier_score_records_table 
                        (supplier_id, month, year, otif, quality_pickup, quality_package, nil, comment, total_score, registered_by, register_date, changed_by, supplier_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, (
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
                
                db_conn.commit()
                
                # Debug: mostrar informações detalhadas do salvamento
                print(f"✅ Score salvo com sucesso!")
                print(f"   Fornecedor: {vendor_name} (ID: {supplier_id})")
                print(f"   Período: {month_val}/{year_val}")
                print(f"   Total Score: {total_score}")
                print(f"   Registrado por: {current_user_wwid}")
                print(f"   Campos salvos: {list(values_to_save.keys())}")
                
                saved_fields = [k.replace('quality_', '').replace('_', ' ').title() for k in values_to_save.keys()]
                show_snackbar(f"✅ Score salvo para {vendor_name} ({month_val}/{year_val}) - Total: {total_score:.1f}")
                
            except Exception as ex:
                show_snackbar(f"❌ Erro ao salvar: {str(ex)}")
                print(f"❌ Erro detalhado ao salvar dados:")
                print(f"   Fornecedor: {vendor_name} (ID: {supplier_id})")
                print(f"   Período: {month_val}/{year_val}")
                print(f"   Erro: {ex}")
                import traceback
                traceback.print_exc()
            finally:
                # Reabilitar botão
                e.control.disabled = False
                e.control.text = "Salvar"
                page.update()

        def toggle_favorite(e):
            # Por enquanto, vou usar um usuário padrão. Em uma implementação real, 
            # isso viria de um sistema de login
            user_wwid = "default_user"  # TODO: Implementar sistema de usuários
            
            if not db_conn:
                show_snackbar("Erro: Banco de dados não conectado.")
                return
                
            try:
                cursor = db_conn.cursor()
                
                # Verificar se já está nos favoritos
                check_query = "SELECT COUNT(*) FROM favorites_table WHERE user_wwid=? AND supplier_id=?"
                cursor.execute(check_query, (user_wwid, supplier_id))
                is_favorited = cursor.fetchone()[0] > 0
                
                if is_favorited:
                    # Remover dos favoritos
                    delete_query = "DELETE FROM favorites_table WHERE user_wwid=? AND supplier_id=?"
                    cursor.execute(delete_query, (user_wwid, supplier_id))
                    is_favorite.current = False
                    e.control.selected = False
                    show_snackbar(f"{vendor_name} removido dos favoritos")
                    print(f"Favorito removido: {vendor_name} (ID: {supplier_id})")
                else:
                    # Adicionar aos favoritos
                    insert_query = "INSERT INTO favorites_table (user_wwid, supplier_id) VALUES (?, ?)"
                    cursor.execute(insert_query, (user_wwid, supplier_id))
                    is_favorite.current = True
                    e.control.selected = True
                    show_snackbar(f"{vendor_name} adicionado aos favoritos")
                    print(f"Favorito adicionado: {vendor_name} (ID: {supplier_id})")
                
                db_conn.commit()
                e.control.update()
                
            except sqlite3.Error as db_error:
                show_snackbar(f"Erro ao salvar favorito: {db_error}")
                print(f"Erro no banco de dados: {db_error}")
            except Exception as ex:
                show_snackbar(f"Erro inesperado: {ex}")
                print(f"Erro ao toggle favorite: {ex}")

        def show_snackbar(message):
            page.snack_bar = ft.SnackBar(ft.Text(message))
            page.snack_bar.open = True
            page.update()

        # Montagem do layout do card
        info_col = ft.Column([
            ft.Text(
                vendor_name, 
                weight="bold", 
                size=16, 
                width=200,  # Define largura para permitir quebra de linha
                text_align=ft.TextAlign.LEFT
            ),
            ft.Text(f"BU: {bu}", size=12),
            ft.Text(f"PO: {supplier_number}", size=12),
            ft.Text(f"ID: {supplier_id}", size=12),
            ft.Text(
                f"Status: {status}", 
                size=12,
                color="green" if str(status).lower().startswith("active") else "red"
            ),
        ], 
        spacing=4, 
        tight=True,
        expand=3
        )

        scores_col = ft.Column(
            score_rows, 
            spacing=8, 
            tight=True,
            expand=4
        )

        # Coluna de ações sem os botões (apenas comentário)
        actions_col = ft.Column([
            comment_field
        ], 
        expand=5,
        spacing=10
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
                        ft.ElevatedButton(
                            "Salvar",
                            on_click=save_score,
                            icon=ft.Icons.SAVE,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=8)
                            )
                        ),
                    ], 
                    alignment=ft.MainAxisAlignment.END,
                    tight=True
                    ),
                    right=0,
                    bottom=0,
                )
            ], expand=True),
            padding=15,
            border_radius=12
        )

        card = ft.Card(
            content=card_content,
            elevation=2,
            margin=ft.margin.symmetric(vertical=5, horizontal=0),
            color=get_current_theme_colors(get_theme_name_from_page(page)).get('card_background')
        )
        
        # Anexar dados necessários ao card
        card.data = {
            "supplier_id": supplier_id,
            "score_sliders": score_sliders,
            "score_texts": score_texts,
            "comment_field": comment_field
        }
        
        return card

    def search_suppliers():
        """Versão otimizada da busca de fornecedores."""
        if not search_field_ref.current:
            return
            
        search_term = search_field_ref.current.value.strip()
        bu_val = selected_bu.current.value if selected_bu.current else None

        print(f"Pesquisando por: '{search_term}', BU: {bu_val}")

        # Limpar resultados anteriores
        if responsive_app_manager:
            responsive_app_manager.clear_results()
        else:
            results_list.controls.clear()
            results_list.update()

        if not search_term and (not bu_val or not bu_val.strip()):
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
                SELECT supplier_id, vendor_name, BU, supplier_status, supplier_number
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

            query = f"{base_query} WHERE {' AND '.join(where_clauses)} ORDER BY vendor_name LIMIT 10"
            
            print(f"Executando query: {query}")
            print(f"Parâmetros: {params}")

            cursor = db_conn.cursor()
            cursor.execute(query, params)
            records = cursor.fetchall()
            
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
                    print(f"Criando card {i+1}/{len(records)}: {record[1]}")
                    try:
                        card = create_result_widget(record)
                        if responsive_app_manager:
                            responsive_app_manager.add_card_to_layout(card)
                        else:
                            results_list.controls.append(card)
                    except Exception as card_error:
                        print(f"Erro ao criar card para {record[1]}: {card_error}")
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

    results_list = ft.ListView(
        expand=True, 
        spacing=10, 
        padding=20
    )

    # Referências para dropdowns que precisam ser atualizados com tema
    month_dropdown = ft.Dropdown(
        label="Mês", 
        options=month_options, 
        ref=selected_month, 
        width=120, 
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
                bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        label="PO", 
                        expand=True, 
                        border_radius=8,
                        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                        border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline'),
                        ref=selected_po
                    ),
                    ft.TextField(
                        label="BU", 
                        expand=True, 
                        border_radius=8, 
                        ref=selected_bu, 
                        on_change=lambda e: search_suppliers(),
                        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                        color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                        border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                    ),
                    month_dropdown,
                    year_dropdown,
                ],
                spacing=10,
            ),
        ],
        spacing=15,
        #bgcolor="#162FB9" if page.theme_mode == ft.ThemeMode.DARK and page.theme is not None else None,
    )

    # Container dos campos de busca com referência para atualização de tema
    score_form_container = ft.Container(
        content=score_form, 
        padding=15,
        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
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
            selected_config_tab.current = idx
            themes_content.visible = idx == 0
            suppliers_content.visible = idx == 1
            criteria_content.visible = idx == 2
            users_content.visible = idx == 3
            lists_content.visible = idx == 4
            log_content.visible = idx == 5
            update_config_tabs()
            page.update()
        return handler

    def config_tab_item(icon, text, idx):
        is_selected = selected_config_tab.current == idx
        colors = get_current_theme_colors(get_theme_name_from_page(page))
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, color=colors['primary'] if is_selected else colors['on_surface'], size=24),
                ft.Text(text, size=12, weight="bold" if is_selected else "normal",
                       color=colors['primary'] if is_selected else colors['on_surface'])
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            border_radius=8,
            bgcolor=colors['primary_container'] if is_selected else None,
            on_click=set_config_tab(idx),
            animate=200,
        )

    def update_config_tabs():
        config_tabs_row.controls = [
            config_tab_item(ft.Icons.PALETTE, "Themes", 0),
            config_tab_item(ft.Icons.BUSINESS, "Suppliers", 1),
            config_tab_item(ft.Icons.TUNE, "Criteria", 2),
            config_tab_item(ft.Icons.PEOPLE, "Users", 3),
            config_tab_item(ft.Icons.LIST, "Lists", 4),
            config_tab_item(ft.Icons.HISTORY, "Log", 5),
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
            if db_conn:
                cursor = db_conn.cursor()
                cursor.execute("SELECT theme_mode FROM theme_settings ORDER BY last_updated DESC LIMIT 1")
                default_theme = cursor.fetchone()
                if default_theme:
                    theme_radio_group.value = default_theme[0]
                    print(f"Tema padrão carregado: {default_theme[0]}")
        except Exception as e:
            print(f"Erro ao carregar tema padrão: {e}")

    # Controle de duração do toast
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
        show_toast(f"⚙️ Duração do toast alterada para {new_duration}s", "blue")
    
    toast_duration_slider.on_change = update_toast_duration

    # Conteúdo da sub-aba Themes
    themes_content = ft.Container(
        content=ft.Column([
            ft.Text("Configuração de Tema", size=20, weight="bold"),
            ft.Divider(),
            theme_radio_group,
            ft.Divider(),
            ft.Text("Configurações de Interface", size=16, weight="bold"),
            ft.Row([
                ft.Text("Duração das notificações (toast):"),
                toast_duration_slider,
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
                    # Adicionar cada item mantendo o estilo da load_all_lists_data
                    for item in items:
                        alias = item["alias"]
                        display_text = item["display"]
                        is_selected = lists_controls[key]['selected_item'] == alias
                        colors = get_current_theme_colors(get_theme_name_from_page(page))
                        
                        # Separar as linhas do display_text
                        lines = display_text.split('\n')
                        line1 = lines[0] if lines else display_text
                        line2 = lines[1] if len(lines) > 1 else ""
                        
                        col.controls.append(
                            ft.ListTile(
                                title=ft.Text(
                                    line1, 
                                    size=14, 
                                    weight="bold",
                                    color=colors['primary'] if is_selected else colors['on_surface']
                                ),
                                subtitle=ft.Text(
                                    line2, 
                                    size=12, 
                                    color="outline"
                                ) if line2 else None,
                                content_padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                dense=True,
                                on_click=lambda e, k=key, v=alias: select_list_item(k, v),
                                selected=is_selected,
                                bgcolor=colors['primary_container'] if is_selected else None
                            )
                        )
                        
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
                    page.snack_bar = ft.SnackBar(ft.Text("❌ Selecione um item da lista para excluir"))
                    page.snack_bar.open = True
                    page.update()
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
                    
                    page.snack_bar = ft.SnackBar(ft.Text(f"✅ Item '{value}' removido de {list_type}"))
                    page.snack_bar.open = True
                    page.update()
                    
                except Exception as ex:
                    # Fechar dialog mesmo se der erro
                    page.close(dialog)
                    
                    # mostrar mensagem amigável
                    import sqlite3 as _sqlite
                    if isinstance(ex, _sqlite.IntegrityError):
                        page.snack_bar = ft.SnackBar(ft.Text(f"❌ Não foi possível excluir '{value}': restrição de integridade."))
                    else:
                        page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao deletar '{value}': {ex}"))
                    page.snack_bar.open = True
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
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao tentar excluir item: {ex}"))
            page.snack_bar.open = True
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
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ SQIE '{alias}' adicionado com sucesso"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            import sqlite3 as _sqlite
            if isinstance(ex, _sqlite.IntegrityError):
                lists_controls['sqie']['feedback'].value = f"Alias '{alias}' já existe"
                lists_controls['sqie']['feedback'].color = 'red'
                lists_controls['sqie']['feedback'].visible = True
                page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao inserir sqie: {ex}"))
                page.snack_bar.open = True
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
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ Item adicionado com sucesso em {key}"))
                page.snack_bar.open = True
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
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao inserir item: {ex}"))
                page.snack_bar.open = True
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
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao inserir em {table}: {ex}"))
                page.snack_bar.open = True
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
                    ),
                    ft.OutlinedButton(
                        'Excluir', 
                        on_click=lambda e: delete_alias_handler('sqie_table','alias', lists_controls['sqie']['alias'].value.strip().upper() if lists_controls['sqie']['alias'].value else lists_controls['sqie']['input'].value.strip()),
                        icon=ft.Icons.DELETE
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
                    ),
                    ft.OutlinedButton(
                        'Excluir', 
                        on_click=lambda e: delete_alias_handler('continuity_table','alias', lists_controls['continuity']['alias'].value.strip().upper() if lists_controls['continuity']['alias'].value else lists_controls['continuity']['input'].value.strip()),
                        icon=ft.Icons.DELETE
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
                                ft.ElevatedButton('Adicionar', on_click=add_alias_handler_sqie, icon=ft.Icons.ADD),
                                ft.OutlinedButton('Excluir', 
                                    on_click=lambda e: delete_alias_handler('sqie_table','alias'), 
                                    icon=ft.Icons.DELETE)
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
                                    icon=ft.Icons.ADD),
                                ft.OutlinedButton('Excluir', 
                                    on_click=lambda e: delete_alias_handler('continuity_table','alias'), 
                                    icon=ft.Icons.DELETE)
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
                                    icon=ft.Icons.ADD),
                                ft.OutlinedButton('Excluir', 
                                    on_click=lambda e: delete_alias_handler('planner_table','alias'), 
                                    icon=ft.Icons.DELETE)
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
                                    icon=ft.Icons.ADD),
                                ft.OutlinedButton('Excluir', 
                                    on_click=lambda e: delete_alias_handler('sourcing_table','alias'), 
                                    icon=ft.Icons.DELETE)
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
                                    icon=ft.Icons.ADD),
                                ft.OutlinedButton('Excluir', 
                                    on_click=lambda e: delete_alias_handler('business_unit_table','bu'), 
                                    icon=ft.Icons.DELETE)
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
                                    icon=ft.Icons.ADD),
                                ft.OutlinedButton('Excluir', 
                                    on_click=lambda e: delete_alias_handler('categories_table','category'), 
                                    icon=ft.Icons.DELETE)
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
        supplier_id = record[0] if len(record) > 0 else ""
        vendor_name = record[1] if len(record) > 1 else ""
        supplier_category = record[2] if len(record) > 2 else ""
        bu = record[3] if len(record) > 3 else ""
        supplier_name = record[4] if len(record) > 4 else ""
        supplier_email = record[5] if len(record) > 5 else ""
        supplier_number = record[6] if len(record) > 6 else ""
        supplier_status = record[7] if len(record) > 7 else ""
        planner = record[8] if len(record) > 8 else ""
        continuity = record[9] if len(record) > 9 else ""
        sourcing = record[10] if len(record) > 10 else ""
        sqie = record[11] if len(record) > 11 else ""

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
            "supplier_name": ft.TextField(
                label="Supplier Name",
                value=supplier_name,  # Preencher com valor do banco
                filled=False,
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

        def show_snackbar(message):
            """Exibe mensagem de feedback para o usuário."""
            page.snack_bar = ft.SnackBar(ft.Text(message))
            page.snack_bar.open = True
            page.update()

        def save_supplier(e):
            """Salva ou atualiza dados do supplier no banco de dados."""
            print(f"🔧 DEBUG: save_supplier chamada para supplier ID: {supplier_id}")
            
            if not db_conn:
                show_snackbar("❌ Erro: Banco de dados não conectado.")
                return

            # Função auxiliar para tratar valores
            def safe_strip(value):
                if value is None:
                    return ""
                return str(value).strip()

            # Validações básicas
            if not safe_strip(fields["vendor_name"].value):
                show_snackbar("❌ Campo Vendor Name é obrigatório!")
                return
            
            if not safe_strip(fields["supplier_name"].value):
                show_snackbar("❌ Campo Supplier Name é obrigatório!")
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
                cursor.execute(check_query, (supplier_id,))
                exists = cursor.fetchone()[0] > 0
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
                    cursor.execute(update_query, (
                        safe_strip(fields["vendor_name"].value),
                        safe_strip(fields["supplier_category"].value),
                        safe_strip(fields["bu"].value),
                        safe_strip(fields["supplier_name"].value),
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
                        (supplier_id, vendor_name, supplier_category, bu, supplier_name,
                         supplier_email, supplier_number, supplier_status, planner, 
                         continuity, sourcing, sqie)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(insert_query, (
                        supplier_id,
                        safe_strip(fields["vendor_name"].value),
                        safe_strip(fields["supplier_category"].value),
                        safe_strip(fields["bu"].value),
                        safe_strip(fields["supplier_name"].value),
                        safe_strip(fields["supplier_email"].value),
                        safe_strip(fields["supplier_number"].value),
                        safe_strip(fields["supplier_status"].value),
                        safe_strip(fields["planner"].value),
                        safe_strip(fields["continuity"].value),
                        safe_strip(fields["sourcing"].value),
                        safe_strip(fields["sqie"].value)
                    ))
                    action = "criado"
                
                db_conn.commit()
                print(f"🔧 DEBUG: Dados commitados no banco")
                show_snackbar(f"✅ Supplier {safe_strip(fields['vendor_name'].value)} {action} com sucesso!")
                print(f"Supplier {supplier_id} {action}")

            except Exception as ex:
                show_toast(f"❌ Erro ao salvar: {str(ex)}", "red")
                print(f"Erro ao salvar supplier: {ex}")
            finally:
                e.control.disabled = False
                e.control.text = "Salvar"
                page.update()

        def delete_supplier(e):
            """Deleta supplier após confirmação com código de 5 letras."""
            print(f"🗑️ DEBUG: delete_supplier chamada para supplier ID: {supplier_id}")
            
            def handle_confirm(e):
                """Callback para confirmar a exclusão"""
                try:
                    if not db_conn:
                        show_snackbar("❌ Erro: Banco de dados não conectado.")
                        return
                    cursor = db_conn.cursor()
                    cursor.execute("DELETE FROM supplier_score_records_table WHERE supplier_id = ?", (supplier_id,))
                    cursor.execute("DELETE FROM favorites_table WHERE supplier_id = ?", (supplier_id,))
                    cursor.execute("DELETE FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
                    db_conn.commit()
                    if card in suppliers_results_list.controls:
                        suppliers_results_list.controls.remove(card)
                    show_snackbar(f"✅ Supplier {vendor_name} deletado com sucesso!")
                    print(f"Supplier {supplier_id} deletado com sucesso")
                except Exception as ex:
                    show_snackbar(f"❌ Erro ao deletar: {str(ex)}")
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
            ft.ElevatedButton("Salvar", on_click=save_supplier, icon=ft.Icons.SAVE),
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
                ft.Row([fields["bu"], fields["supplier_name"]], spacing=10),
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
        
        def show_snackbar(message):
            """Exibe mensagem de feedback para o usuário."""
            page.snack_bar = ft.SnackBar(ft.Text(message))
            page.snack_bar.open = True
            page.update()
        
        def handle_confirm(e):
            """Callback para confirmar a criação do supplier"""
            print("🔍 DEBUG: handle_confirm chamado")
            
            # Função auxiliar para tratar valores (TextField e Dropdown)
            def safe_strip(value):
                if value is None:
                    return ""
                return str(value).strip()
                
            def get_field_value(field):
                """Obtém valor tanto de TextField quanto de Dropdown"""
                if hasattr(field, 'value'):
                    return safe_strip(field.value)
                return ""
            
            if not db_conn:
                print("🔍 DEBUG: Banco de dados não conectado")
                show_snackbar("❌ Erro: Banco de dados não conectado.")
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
                
                cursor.execute(insert_query, (
                    get_field_value(add_dialog.fields["vendor_name"]),
                    get_field_value(add_dialog.fields["supplier_category"]),
                    get_field_value(add_dialog.fields["bu"]),
                    get_field_value(add_dialog.fields["supplier_name"]),
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
                
                show_snackbar(f"✅ Supplier {vendor_name} criado com sucesso!")
                page.close(add_dialog)
                
            except Exception as ex:
                print(f"🔍 DEBUG: Erro ao inserir: {ex}")
                show_snackbar(f"❌ Erro ao criar supplier: {str(ex)}")
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
            cursor.execute(query, params)
            records = cursor.fetchall()
            
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
                    print(f"Criando card {i+1}/{len(records)}: {record[1]}")
                    try:
                        card = create_supplier_card(record, page)
                        suppliers_results_list.controls.append(card)
                    except Exception as card_error:
                        print(f"Erro ao criar card para {record[1]}: {card_error}")
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
        
        # Remover toast após 3 segundos
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
            page.snack_bar = ft.SnackBar(ft.Text("❌ Erro: Conexão com banco não disponível"))
            page.snack_bar.open = True
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
            cur = db_conn.cursor()
            print("🔄 Iniciando atualização no banco de dados...")
            
            # Atualizar cada critério na tabela criteria_table com 2 casas decimais
            for criteria_name, value in criteria_values.items():
                # Arredondar para 2 casas decimais antes de salvar
                rounded_value = round(value, 2)
                cur.execute("UPDATE criteria_table SET value = ? WHERE criteria_category = ?", 
                          (str(rounded_value), criteria_name))
                print(f"  ✅ Critério atualizado: {criteria_name} = {rounded_value}")
            
            db_conn.commit()
            print("✅ Commit realizado com sucesso!")
            
            show_toast("✅ Critérios atualizados com sucesso!", "green")
            
        except Exception as ex:
            print(f"❌ Erro ao atualizar critérios: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text("❌ Erro ao atualizar critérios!"))
            page.snack_bar.open = True
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
    users_controls = {
        'wwid': wwid_field_ref,
        'name': name_field_ref, 
        'password': password_field_ref,
        'privilege': privilege_dropdown_ref,
        'otif_check': otif_check_ref,
        'nil_check': nil_check_ref,
        'pickup_check': pickup_check_ref,
        'package_check': package_check_ref,
        'action_btn': action_btn_ref,
        'clear_btn': clear_btn_ref
    }
    
    # Container do formulário de usuários com referência para atualização de tema
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
        ], spacing=15),
        bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
        padding=ft.padding.all(20),
        border_radius=8,
        border=ft.border.all(1, get_current_theme_colors(get_theme_name_from_page(page)).get('outline'))
    )
    
    users_content = ft.Container(
        content=ft.Column([
            # Título fixo (fora do scroll)
            ft.Text("Gerenciamento de Usuários", size=20, weight="bold"),
            ft.Divider(),
            
            # Conteúdo com scroll
            ft.Container(
                content=ft.ListView([
                    # Header com informações
                    ft.Container(
                        content=ft.Row([
                            ft.Text("Configure usuários e suas permissões de avaliação", 
                                   size=14, color="outline"),
                        ]),
                        padding=ft.padding.only(bottom=10)
                    ),
                    
                    # Referência ao container global do formulário de usuário
                    users_form_container,

                    
                    ft.Container(height=10),
                    
                    # Linha 3: Permissões de notas (checkboxes) - fora do container com fundo
                    ft.Column([
                        ft.Text("Permissões de Avaliação:", size=16, weight="bold"),
                        ft.Row([
                            ft.Checkbox(label="OTIF", value=False, ref=otif_check_ref),
                            ft.Checkbox(label="NIL", value=False, ref=nil_check_ref),
                            ft.Checkbox(label="Pickup", value=False, ref=pickup_check_ref),
                            ft.Checkbox(label="Package", value=False, ref=package_check_ref),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
                    ], spacing=8),
                    
                    ft.Container(height=15),
                    
                    # Botões de ação
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
                    
                    # Lista de usuários
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Usuários Cadastrados", size=16, weight="bold"),
                            ft.Container(
                                content=ft.ListView(
                                    spacing=8,
                                    expand=True,
                                    ref=users_list_ref,  # Referência específica para a lista de usuários
                                ),
                                height=300,
                                border=ft.border.all(1, "outline"),
                                border_radius=8,
                                padding=8,
                            ),
                        ], spacing=10),
                        padding=ft.padding.symmetric(vertical=10)
                    ),
                    
                ], expand=True, spacing=8),
                expand=True
            )
            
        ], spacing=0),
        padding=20,
        visible=False
    )

    # Referências dos controles de usuários
    def extract_users_refs():
        """Extrai as referências dos controles do users_content"""
        users_refs = {}
        
        # Navegar pela nova estrutura com scroll
        scroll_container = users_content.content.controls[2].content  # ListView dentro do Container
        
        # O formulário está como um Container (form_outer_container) cujo content é um Column 
        # contendo um Row (linha 1) e outro Row (linha 2). A variável users_form_container foi criada com esse formato.
        form_outer_container = scroll_container.controls[1]  # Container do formulário
        form_column = form_outer_container.content  # Column([...])
        
        # Linha 1: WWID e Nome
        row1 = form_column.controls[0]
        users_refs['wwid'] = row1.controls[0]
        users_refs['name'] = row1.controls[1]
        
        # Linha 2: Senha e Privilégio
        row2 = form_column.controls[1]
        users_refs['password'] = row2.controls[0]
        users_refs['privilege'] = row2.controls[1]
        
        # Checkboxes (fora do container com fundo)
        permissions_column = scroll_container.controls[3]
        checkboxes_row = permissions_column.controls[1]
        users_refs['otif_check'] = checkboxes_row.controls[0]
        users_refs['nil_check'] = checkboxes_row.controls[1]
        users_refs['pickup_check'] = checkboxes_row.controls[2]
        users_refs['package_check'] = checkboxes_row.controls[3]
        
        # Botões (fora do container com fundo)
        buttons_container = scroll_container.controls[5]
        buttons_row = buttons_container.content
        users_refs['action_btn'] = buttons_row.controls[0]  # Botão Add/Update
        users_refs['clear_btn'] = buttons_row.controls[1]
        
        # Lista de usuários - usar referência direta
        users_refs['users_list'] = users_list_ref.current
        
        return users_refs

    # Funções para gerenciamento de usuários
    def load_users_full():
        """Carrega todos os usuários da tabela."""
        if not db_conn:
            return []
        try:
            print("📋 Lista sendo atualizada...")
            cur = db_conn.cursor()
            cur.execute("""
                SELECT user_wwid, user_name, user_password, user_privilege, 
                       otif, nil, pickup, package 
                FROM users_table 
                ORDER BY user_wwid
            """)
            rows = cur.fetchall()
            users = []
            for row in rows:
                wwid, name, password, privilege, otif, nil, pickup, package = row
                
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
                    colors = get_current_theme_colors(get_theme_name_from_page(page))

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
                                    cur = db_conn.cursor()
                                    cur.execute("DELETE FROM users_table WHERE UPPER(user_wwid) = ?", (w.upper(),))
                                    db_conn.commit()
                                    page.close(dialog)
                                    # Se o usuário selecionado foi excluído, limpar seleção e campos
                                    if globals().get('selected_user') == w:
                                        clear_users_fields()
                                    refresh_users_list()
                                    page.snack_bar = ft.SnackBar(ft.Text(f"✅ Usuário '{w}' removido com sucesso"))
                                    page.snack_bar.open = True
                                    page.update()
                                except Exception as ex:
                                    page.close(dialog)
                                    page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao excluir usuário: {ex}"))
                                    page.snack_bar.open = True
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
                            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao tentar excluir usuário: {ex}"))
                            page.snack_bar.open = True
                            page.update()

                    delete_btn = ft.TextButton(
                        "Apagar",
                        icon=ft.Icons.DELETE,
                        style=ft.ButtonStyle(color="red"),
                        on_click=_delete_from_card
                    )

                    header_row = ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.PERSON, color=colors['primary']),
                            ft.Text(f"{name_display}", size=15, weight="bold", color=colors['on_surface'])
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
                        bgcolor=colors['primary_container'] if is_selected else get_current_theme_colors(get_theme_name_from_page(page)).get('card_background'),
                        border_radius=8,
                        border=ft.border.all(1, colors['outline'])
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
            cur = db_conn.cursor()
            cur.execute("""
                SELECT user_wwid, user_name, user_password, user_privilege,
                       otif, nil, pickup, package
                FROM users_table 
                WHERE user_wwid = ?
            """, (wwid,))
            
            row = cur.fetchone()
            if row:
                wwid_val, name, password, privilege, otif, nil, pickup, package = row
                
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
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao carregar usuário: {ex}"))
            page.snack_bar.open = True
            page.update()

    def clear_users_fields():
        """Limpa todos os campos do formulário de usuários."""
        try:
            print("Limpando todos os campos...")
            
            # Limpar campos usando busca direta na estrutura
            try:
                wwid_field = find_field_by_label("WWID")
                if wwid_field:
                    wwid_field.value = ""
            except Exception as e:
                print(f"Erro ao limpar WWID: {e}")
            
            try:
                name_field = find_field_by_label("Nome Completo")
                if name_field:
                    name_field.value = ""
            except Exception as e:
                print(f"Erro ao limpar Name: {e}")
            
            try:
                password_field = find_field_by_label("Senha")
                if password_field:
                    password_field.value = ""
            except Exception as e:
                print(f"Erro ao limpar Password: {e}")
            
            try:
                privilege_field = find_field_by_label("Nível de Privilégio")
                if privilege_field:
                    privilege_field.value = None
            except Exception as e:
                print(f"Erro ao limpar Privilege: {e}")
            
            # Limpar checkboxes usando busca direta
            checkbox_labels = ["OTIF", "NIL", "Pickup", "Package"]
            for label in checkbox_labels:
                try:
                    checkbox = find_checkbox_by_label(label)
                    if checkbox:
                        checkbox.value = False
                except Exception as e:
                    print(f"Erro ao limpar checkbox {label}: {e}")
            
            # Limpar seleção global
            global selected_user
            selected_user = None
            
            # Atualizar página diretamente
            try:
                page.update()
            except Exception as e:
                print(f"Erro ao atualizar página: {e}")
            
            # Atualizar botão de ação
            update_action_button()
            
            # Atualizar lista visual (remover destaque)
            refresh_users_list()
            
            print("Campos limpos com sucesso!")
            
        except Exception as ex:
            print(f"Erro ao limpar campos: {ex}")

    def add_or_update_user():
        """Adiciona ou atualiza um usuário baseado na função original."""
        print("🔥 FUNÇÃO add_or_update_user CHAMADA!")
        try:
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
                page.snack_bar = ft.SnackBar(ft.Text("❌ Preencha WWID, Senha e Privilégio"))
                page.snack_bar.open = True
                page.update()
                return
            
            cur = db_conn.cursor()
            
            # Verifica se já existe o usuário
            cur.execute("SELECT 1 FROM users_table WHERE UPPER(user_wwid) = ?", (wwid,))
            resultado = cur.fetchone()
            
            if resultado:
                # Atualiza usuário existente
                print(f"🔄 Atualizando usuário EXISTENTE {wwid}...")
                cur.execute("""
                    UPDATE users_table
                    SET user_name = ?, user_password = ?, user_privilege = ?, 
                        otif = ?, nil = ?, pickup = ?, package = ?
                    WHERE UPPER(user_wwid) = ?
                """, (name, password, privilege, otif, nil, pickup, package, wwid))
                
                print(f"✅ Usuário {wwid} atualizado com sucesso!")
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ Usuário '{wwid}' atualizado com sucesso"))
            else:
                # Cria novo usuário
                print(f"💾 Inserindo NOVO usuário {wwid} no banco de dados...")
                cur.execute("""
                    INSERT INTO users_table (user_wwid, user_name, user_password, user_privilege, 
                                           otif, nil, pickup, package) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (wwid, name, password, privilege, otif, nil, pickup, package))
                
                print(f"✅ Usuário {wwid} inserido com sucesso!")
                page.snack_bar = ft.SnackBar(ft.Text(f"✅ Usuário '{wwid}' criado com sucesso"))
            
            db_conn.commit()
            page.snack_bar.open = True
            page.update()
            
            print(f"Lista atualizada com {len(load_users_full())} usuários!")
            # Atualizar lista
            refresh_users_list()
            
        except Exception as ex:
            show_toast(f"❌ Erro ao salvar usuário: {ex}", "red")
            page.snack_bar.open = True
            page.update()
            print(f"Erro ao adicionar/atualizar usuário: {ex}")

    def delete_user():
        """Exclui o usuário baseado no WWID do campo de texto."""
        try:
            # Pegar WWID do campo de texto
            wwid = users_controls['wwid'].value.strip() if users_controls['wwid'].value else ''

            
            if not wwid:
                page.snack_bar = ft.SnackBar(ft.Text("❌ Digite um WWID para excluir"))
                page.snack_bar.open = True
                page.update()
                return
            
            # Verificar se o usuário existe no banco
            if not check_user_exists(wwid):
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ Usuário '{wwid}' não encontrado"))
                page.snack_bar.open = True
                page.update()
                return
            
            # Função para confirmar e executar a exclusão
            def confirm_delete_user(e):
                try:
                    cur = db_conn.cursor()
                    cur.execute("DELETE FROM users_table WHERE UPPER(user_wwid) = ?", (wwid.upper(),))
                    db_conn.commit()
                    
                    # Fechar dialog
                    page.close(dialog)
                    
                    # Limpar campos e seleção
                    clear_users_fields()
                    
                    # Atualizar lista
                    refresh_users_list()
                    
                    page.snack_bar = ft.SnackBar(ft.Text(f"✅ Usuário '{wwid}' removido com sucesso"))
                    page.snack_bar.open = True
                    page.update()
                    
                except Exception as ex:
                    # Fechar dialog mesmo se der erro
                    page.close(dialog)
                    
                    page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao excluir usuário: {ex}"))
                    page.snack_bar.open = True
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
            page.snack_bar = ft.SnackBar(ft.Text(f"❌ Erro ao tentar excluir usuário: {ex}"))
            page.snack_bar.open = True
            page.update()
            print(f"Erro geral no delete_user: {ex}")

    # Referências para os controles da aba Log
    log_user_filter_ref = ft.Ref()
    log_start_date_ref = ft.Ref()
    log_end_date_ref = ft.Ref()

    log_controls = {
        'user_filter': log_user_filter_ref,
        'start_date': log_start_date_ref,
        'end_date': log_end_date_ref,
    }

    # Conteúdo da sub-aba Log
    log_content = ft.Container(
        content=ft.Column([
            ft.Text("Log de Atividades", size=20, weight="bold"),
            ft.Divider(),
            ft.Row([
                ft.TextField(
                    ref=log_user_filter_ref,
                    label="Filtrar por usuário", 
                    expand=True,
                    bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                    color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                    border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                ),
                ft.TextField(
                    ref=log_start_date_ref,
                    label="Data inicial", 
                    expand=True,
                    bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                    color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                    border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                ),
                ft.TextField(
                    ref=log_end_date_ref,
                    label="Data final", 
                    expand=True,
                    bgcolor=get_current_theme_colors(get_theme_name_from_page(page)).get('field_background'),
                    color=get_current_theme_colors(get_theme_name_from_page(page)).get('on_surface'),
                    border_color=get_current_theme_colors(get_theme_name_from_page(page)).get('outline')
                ),
                ft.ElevatedButton("Filtrar", icon=ft.Icons.FILTER_LIST),
            ], spacing=10),
            ft.Container(height=20),
            ft.Container(
                content=ft.Text("Log de atividades aparecerá aqui...", italic=True),
                height=300,
                border=ft.border.all(1, "outline"),
                border_radius=8,
                padding=20,
            )
        ], spacing=15),
        padding=20,
        visible=False
    )

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

    score_view = ft.Column(
        [
            ft.Container(
                content=score_view_content, 
                alignment=ft.alignment.top_center, 
                padding=ft.padding.only(top=20, left=20, right=20, bottom=10)
            ),
            ft.Divider(),
            results_list,
        ],
        visible=True,
        expand=True,
    )
    timeline_view = ft.Container(
        content=ft.Text("Timeline View"), 
        alignment=ft.alignment.center, 
        expand=True, 
        visible=False
    )
    risks_view = ft.Container(
        content=ft.Column([
            ft.Text("Gestão de Riscos", size=24, weight="bold"),
            ft.Divider(),
            ft.Text("Aqui você pode gerenciar os riscos dos fornecedores.", size=16),
            ft.Container(height=20),
            ft.ElevatedButton("Adicionar Novo Risco", icon=ft.Icons.ADD_CIRCLE_OUTLINE),
        ]), 
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
                        content=ft.Column([score_view, timeline_view, risks_view, email_view, configs_view], expand=True),
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
    responsive_app_manager.check_initial_window_state()  # Verificar estado inicial da janela
    print("📱 Gerenciador responsivo inicializado e estado inicial verificado")

    update_menu()
    update_config_tabs()  # Inicializar as abas de configuração
    
    # Inicializar controles de usuário
    print("Extraindo referências dos controles de usuário...")
    try:
        users_controls.update(extract_users_refs())
        print(f"Controles extraídos: {list(users_controls.keys())}")
    except Exception as ex:
        print(f"Erro ao extrair controles: {ex}")
    
    # Configurar eventos dos botões de usuário
    try:
        print("Configurando eventos dos botões...")
        users_controls['action_btn'].on_click = lambda e: add_or_update_user()
        users_controls['clear_btn'].on_click = lambda e: clear_users_fields()
        print("Eventos configurados com sucesso!")
    except Exception as ex:
        print(f"Erro ao configurar eventos: {ex}")
    
    load_all_lists_data()  # Carregar dados existentes das tabelas
    
    # Carregar usuários na inicialização
    refresh_users_list()
    
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

# ===== FUNÇÃO PRINCIPAL =====
def main():
    """Função principal que inicia com tela de login"""
    ft.app(target=login_screen)

if __name__ == "__main__":
    main()