"""
Email Manager - Classe para gerenciar envio de emails de scorecard
"""
import flet as ft
import win32com.client
import pythoncom
import threading
import random
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import smtplib
from PIL import Image
import re
import os


class EmailManager:
    def __init__(self, db_manager, page_ref=None, get_theme_colors_func=None, get_theme_name_func=None, show_snack_bar_func=None):
        self.db_manager = db_manager
        self.page_ref = page_ref
        self.get_theme_colors = get_theme_colors_func
        self.get_theme_name = get_theme_name_func
        self.show_snack_bar = show_snack_bar_func
        
        # Lista de emails selecionados
        self.supplier_emails_data = []
        
        # Configurações de email
        self.email_config = {
            'sender_email': '',
            'sender_password': '',
            'configured': False
        }
        
        # Containers e campos UI
        self.email_cards_container = ft.Row([], spacing=5, wrap=True)
        self.email_preview_container = self._create_preview_container()
        self.add_email_field = self._create_add_email_field()
        self.supplier_dropdown_email = self._create_supplier_dropdown()
        
        # Conteúdos das abas
        self.individual_email_content = self._create_individual_content()
        self.batch_email_content = self._create_batch_content()
        
        # Dados para envio em lote
        self.suppliers_for_batch = []
        self.selected_suppliers_list = ft.Column([], spacing=5)
        self.batch_suppliers_table = self._create_batch_table()
        
    def _create_preview_container(self):
        """Cria o container de preview do email"""
        return ft.Container(
            content=ft.Column([
                ft.Text("Preview do E-mail", size=16, weight="bold"),
                ft.Divider(),
                ft.Container(
                    content=ft.Text("Selecione um fornecedor para visualizar o preview do email.", 
                                   size=14),
                    padding=20,
                    expand=True,
                    width=None,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREY_500)
                )
            ], spacing=10, expand=True),
            expand=True,
            width=None,
            height=None
        )
    
    def _create_add_email_field(self):
        """Cria o campo para adicionar emails"""
        return ft.TextField(
            label="Adicionar Email",
            hint_text="Digite emails separados por ; ou espaço e pressione Enter",
            width=400,
            on_submit=lambda e: self.add_emails_from_input(e.control.value)
        )
    
    def _create_supplier_dropdown(self):
        """Cria o dropdown de fornecedores"""
        return ft.Dropdown(
            label="Selecionar Fornecedor",
            hint_text="Escolha o fornecedor...",
            width=400,
            on_change=lambda e: self.force_email_field_update(e.control.value)
        )
    
    def _create_batch_table(self):
        """Cria a tabela para seleção em lote"""
        return ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Selecionado", weight="bold")),
                ft.DataColumn(ft.Text("Fornecedor", weight="bold")),
                ft.DataColumn(ft.Text("Email", weight="bold")),
                ft.DataColumn(ft.Text("Status", weight="bold")),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            data_row_max_height=50,
            heading_row_color=ft.Colors.BLUE_50,
            heading_row_height=40
        )
    
    def parse_emails(self, email_string):
        """Separa emails por ; ou espaço e remove duplicatas"""
        if not email_string:
            return []
        
        # Separar por ; ou espaço
        emails = re.split(r'[;\s]+', email_string.strip())
        
        # Filtrar emails válidos e remover duplicatas
        valid_emails = []
        for email in emails:
            email = email.strip()
            if email and email not in valid_emails and '@' in email:
                valid_emails.append(email)
        
        return valid_emails
    
    def add_emails_from_input(self, email_string):
        """Adiciona emails do campo de input aos cards"""
        if not email_string.strip():
            return
            
        new_emails = self.parse_emails(email_string)
        
        # Adicionar emails que ainda não existem
        for email in new_emails:
            if email not in self.supplier_emails_data:
                self.supplier_emails_data.append(email)
        
        # Limpar campo de input
        self.add_email_field.value = ""
        self.add_email_field.update()
        
        # Atualizar cards
        self.update_email_cards()
    
    def update_email_cards(self):
        """Atualiza os cards visuais baseados na lista de emails"""
        self.email_cards_container.controls.clear()
        
        for email in self.supplier_emails_data:
            card = self.create_email_card(email, self.remove_email_card)
            self.email_cards_container.controls.append(card)
        
        self.email_cards_container.update()
        if self.page_ref:
            self.page_ref.update()
            print(f"DEBUG: Atualizados {len(self.supplier_emails_data)} cards de email")
    
    def set_supplier_emails(self, emails_list):
        """Define a lista de emails do fornecedor"""
        self.supplier_emails_data.clear()
        self.supplier_emails_data.extend(emails_list)
        self.update_email_cards()
    
    def create_email_card(self, email, on_remove):
        """Cria um mini card para um email com botão X para remover"""
        return ft.Container(
            content=ft.Row([
                ft.Text(email, size=11, color=ft.Colors.WHITE),
                ft.IconButton(
                    ft.Icons.CLOSE,
                    icon_size=10,
                    on_click=lambda e: on_remove(email),
                    icon_color=ft.Colors.WHITE,
                    tooltip="Remover email",
                    style=ft.ButtonStyle(
                        padding=ft.padding.all(2),
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                )
            ], spacing=1, tight=True, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=ft.Colors.BLUE_600,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
            border_radius=8,
            margin=ft.margin.all(1),
            height=24
        )
    
    def remove_email_card(self, email_to_remove):
        """Remove um email específico dos cards"""
        if email_to_remove in self.supplier_emails_data:
            self.supplier_emails_data.remove(email_to_remove)
            self.update_email_cards()
    
    def force_email_field_update(self, supplier_id):
        """Força a atualização imediata do campo de email"""
        try:
            self.update_email_preview(supplier_id)
            if self.page_ref:
                self.page_ref.update()
        except Exception as e:
            print(f"Erro ao atualizar campo de email: {e}")
    
    def update_email_preview(self, supplier_id):
        """Atualiza o preview do email com base no fornecedor selecionado"""
        # Obter cores do tema
        if self.get_theme_name and self.get_theme_colors:
            theme_name = self.get_theme_name(self.page_ref) if self.page_ref else "white"
            Colors = self.get_theme_colors(theme_name)
        else:
            Colors = {'on_surface_variant': ft.Colors.GREY_600, 'on_surface': ft.Colors.BLACK, 
                     'outline': ft.Colors.GREY_300, 'surface': ft.Colors.WHITE,
                     'surface_variant': ft.Colors.with_opacity(0.05, ft.Colors.GREY_500),
                     'error': ft.Colors.RED}
        
        if not supplier_id:
            preview_content = ft.Text("Selecione um fornecedor para visualizar o preview do email.", 
                                    size=14, color=Colors.get('on_surface_variant'))
            self.set_supplier_emails([])
        else:
            # Buscar dados do fornecedor
            supplier_data = self.db_manager.query("SELECT vendor_name, supplier_email, bu FROM supplier_database_table WHERE supplier_id = ?", (supplier_id,))
            if supplier_data:
                supplier = supplier_data[0]
                
                # Processar emails do fornecedor
                if supplier['supplier_email']:
                    email_list = self.parse_emails(supplier['supplier_email'])
                    self.set_supplier_emails(email_list)
                else:
                    self.set_supplier_emails([])
                
                # Gerar HTML do email
                html_content = self.generate_performance_scorecard_html(supplier)
                
                # Criar display de emails para o preview
                email_display = '; '.join(self.supplier_emails_data) if self.supplier_emails_data else 'Email não cadastrado'
                
                preview_content = ft.Column([
                    ft.Text(f"Para: {email_display}", 
                           size=12, weight="bold", color=Colors.get('on_surface')),
                    ft.Text(f"Assunto: Monthly Performance Scorecard - {supplier['vendor_name']}", 
                           size=12, color=Colors.get('on_surface')),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Markdown(
                            value=f"```html\n{html_content[:2000]}...\n```" if len(html_content) > 2000 else f"```html\n{html_content}\n```",
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            code_theme=ft.MarkdownCodeTheme.GITHUB,
                            code_style=ft.TextStyle(size=10)
                        ),
                        padding=10,
                        border=ft.border.all(1, Colors.get('outline')),
                        border_radius=8,
                        bgcolor=Colors.get('surface'),
                        expand=True,
                        width=None
                    )
                ], spacing=8, expand=True)
            else:
                preview_content = ft.Text("Fornecedor não encontrado.", size=14, color=Colors.get('error'))
                self.set_supplier_emails([])
        
        # Atualizar o container de preview
        try:
            self.email_preview_container.content = ft.Column([
                ft.Text("Preview do E-mail", size=16, weight="bold"),
                ft.Divider(),
                ft.Container(
                    content=preview_content,
                    padding=15,
                    expand=True,
                    width=None,
                    border=ft.border.all(1, Colors.get('outline', ft.Colors.GREY_300)),
                    border_radius=8,
                    bgcolor=Colors.get('surface_variant', ft.Colors.with_opacity(0.05, ft.Colors.GREY_500))
                )
            ], spacing=10, expand=True)
            
            self.email_preview_container.update()
            if self.page_ref:
                self.page_ref.update()
                
        except Exception as e:
            print(f"DEBUG: Erro ao atualizar preview: {e}")
    
    def generate_performance_scorecard_html(self, supplier):
        """Gera o HTML completo do scorecard de performance"""
        # Gerar dados de exemplo (na implementação real, você pegaria do banco de dados)
        months = ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
        data = []
        for m in months:
            pkg = random.randint(6, 10)
            pku = random.randint(6, 10)
            nil = random.randint(6, 10)
            otf = random.randint(6, 10)
            score = round((pkg + pku + nil + otf) / 4, 2)
            data.append([m, pkg, pku, nil, otf, score])

        df = pd.DataFrame(data, columns=["Month", "Package", "PickUp", "NIL", "OTIF", "TotalScore"])
        
        target = 9.0  # Pode ser obtido do banco de dados
        today = datetime.now().strftime("%B %d, %Y")
        
        # Média trimestral
        def trimestre_media(df, trimestre_idx):
            start = (trimestre_idx - 1) * 3
            end = start + 3
            return round(df["TotalScore"].iloc[start:end].mean(), 2)

        quarterly_scores = {
            "Q1": trimestre_media(df, 1),
            "Q2": trimestre_media(df, 2),
            "Q3": trimestre_media(df, 3),
            "Q4": trimestre_media(df, 4),
        }

        # Critérios e pesos (pode vir do banco de dados)
        criterios_pesos = {
            "Package": 0.25,
            "PickUp": 0.25,
            "NIL": 0.25,
            "OTIF": 0.25
        }

        # Mensagens importantes
        mensagens_importantes = [
            "⚠️ Lembrete: Envio obrigatório dos certificados ISO até o final do mês.",
            "⚠️ Atualize suas informações no portal Cummins para garantir conformidade.",
            "⚠️ Próxima reunião de revisão agendada para o dia 15/10."
        ]

        # Gerar tabela HTML principal
        email_table_html = f"""
        <table cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse: collapse; margin-bottom: 20px; font-size: 14px; color: #333;">
            <thead>
                <tr style="background-color: #d32f2f; color: #ffffff;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Month</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">Package</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">PickUp</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">NIL</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">OTIF</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">TotalScore</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f'<tr><td style="border: 1px solid #ddd; padding: 8px; text-align: left; font-weight: bold;">{row["Month"]}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{row["Package"]}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{row["PickUp"]}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{row["NIL"]}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{row["OTIF"]}</td><td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{row["TotalScore"]}</td></tr>' for index, row in df.iterrows())}
            </tbody>
        </table>
        <p style="margin: 10px 0; font-size: 14px; text-align: right;"><strong>Target:</strong> {target}</p>
        """

        # Tabela trimestral
        email_quarterly_table_html = f"""
        <table cellpadding="0" cellspacing="0" border="0" width="50%" style="border-collapse: collapse; margin: 0 auto 30px auto; font-size: 14px; color: #333;">
          <tr style="background-color: #d32f2f; color: #fff;">
            <th style="padding:8px; text-align: center; border: 1px solid #ddd;">Quarter</th>
            <th style="padding:8px; text-align: center; border: 1px solid #ddd;">Average Score</th>
          </tr>
          {''.join(f"<tr><td style='padding:8px; text-align:left; border: 1px solid #ddd;'>{q}</td><td style='padding:8px; text-align:center; border: 1px solid #ddd;'>{score}</td></tr>" for q, score in quarterly_scores.items())}
        </table>
        """

        # Tabela de critérios
        email_criteria_table_html = f"""
        <table cellpadding="0" cellspacing="0" border="0" width="50%" style="border-collapse: collapse; margin: 0 auto 30px auto; font-size: 14px; color: #333;">
            <tr style="background-color: #d32f2f; color: #fff;">
                <th style="padding:8px; text-align: center; border: 1px solid #ddd;">Criterion</th>
                <th style="padding:8px; text-align: center; border: 1px solid #ddd;">Weight</th>
            </tr>
            {''.join(f"<tr><td style='padding:8px; text-align:left; border: 1px solid #ddd;'>{k}</td><td style='padding:8px; text-align:center; border: 1px solid #ddd;'>{v*100:.0f}%</td></tr>" for k, v in criterios_pesos.items())}
        </table>
        """

        # HTML completo do email
        html_email = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head><meta charset="UTF-8">
        <title>Performance Scorecard</title>
        </head>
        <body style="margin:0; padding:20px; background-color:#f4f7f6; font-family: Arial, sans-serif; color:#333;">
          <table cellpadding="20" cellspacing="0" border="0" width="100%" bgcolor="#f4f7f6">
            <tr>
              <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="800" bgcolor="#ffffff" style="border-collapse: collapse; border-radius:8px; overflow:hidden; box-shadow:0 0 10px rgba(0,0,0,0.1); table-layout: fixed; word-break: break-word;">
                  <tr>
                    <td style="padding:0; background-color:#d32f2f; color:#fff;">
                      <table cellpadding="0" cellspacing="0" border="0" width="100%">
                        <tr>
                            <td style="padding: 10px; vertical-align: top;">
                                <p style="margin: 0; padding: 4px 0;"><strong>Supplier:</strong> {supplier['vendor_name']}</p>
                                <p style="margin: 0; padding: 4px 0;"><strong>BU:</strong> {supplier.get('bu', 'N/A')}</p>
                                <p style="margin: 0; padding: 4px 0;"><strong>Date:</strong> {today}</p>
                            </td>
                            <td style="padding: 10px; text-align: right; vertical-align: top;">
                                <img src="cid:cummins_logo_header" width="80" height="80" alt="Cummins Logo">
                            </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:20px 30px;">
                      <h1 style="color:#d32f2f; margin:0 0 20px 0; border-bottom:2px solid #d32f2f; padding-bottom:10px;">Monthly Performance Scorecard</h1>
                      {email_table_html}
                      <h2 style="color:#d32f2f; margin:20px 0 20px 0; border-bottom:2px solid #d32f2f; padding-bottom:10px;">Performance Visualization</h2>
                      <div style="text-align:center; margin:20px 0;">
                        <img src="cid:score_chart" alt="Score Chart" style="max-width:100%; height:auto; border:1px solid #ddd; border-radius:5px;">
                      </div>
                      <h2 style="color:#d32f2f; margin:20px 0; border-bottom:2px solid #d32f2f; padding-bottom:10px;">Quarterly Performance</h2>
                      {email_quarterly_table_html}
                      <h2 style="color:#d32f2f; margin-top:20px; border-bottom:2px solid #d32f2f; padding-bottom:10px;">Critérios Utilizados e Pesos</h2>
                      {email_criteria_table_html}
                      <h2 style="color:#d32f2f; margin-top:20px; border-bottom:2px solid #d32f2f; padding-bottom:10px;">Mensagens Importantes</h2>
                      <ul style="margin:0 0 20px 20px; padding:0;">
                        {"".join(f'<li style="margin-bottom:5px;">{msg}</li>' for msg in mensagens_importantes)}
                      </ul>
                      <hr style="border:0; border-top:1px solid #eee; margin:20px 0;">
                      <h2 style="color:#d32f2f; margin-top:0; border-bottom:2px solid #d32f2f; padding-bottom:10px;">Manager's Message</h2>
                      <p style="margin-top:0;">Dear Supplier,<br><br>
                      Please find the performance scorecard for the year to date. We would like to schedule a meeting to discuss these results and define action plans for continuous improvement.<br><br>
                      We appreciate your partnership.</p>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:20px 30px; background-color:#f9f9f9; text-align: center;">
                      <p style="margin:5px 0;"><strong>Best regards,</strong></p>
                      <p style="margin:5px 0;">Cummins Inc.</p>
                      <img src="cid:cummins_logo_footer" width="100" alt="Cummins Logo">
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """
        
        return html_email
    
    def send_email_via_outlook(self, recipient_emails, supplier_name, supplier_data=None):
        """Envia email via Outlook com HTML completo"""
        try:
            # Conectar ao Outlook
            outlook = win32com.client.Dispatch("Outlook.Application")
            
            # Criar novo email
            mail = outlook.CreateItem(0)
            
            # Configurar destinatários
            mail.To = recipient_emails
            
            # Configurar assunto
            mail.Subject = f"Monthly Performance Scorecard - {supplier_name}"
            
            # Gerar HTML do email
            if supplier_data:
                html_content = self.generate_performance_scorecard_html(supplier_data)
            else:
                # Fallback para dados básicos
                supplier_basic = {'vendor_name': supplier_name, 'bu': 'N/A'}
                html_content = self.generate_performance_scorecard_html(supplier_basic)
            
            # Configurar corpo HTML
            mail.HTMLBody = html_content
            
            # Enviar o email automaticamente
            mail.Send()
            
            return True, f"✅ Email enviado automaticamente para {recipient_emails}"
            
        except Exception as e:
            return False, f"❌ Erro ao enviar email: {str(e)}"
    
    def load_suppliers_for_email(self):
        """Carrega lista de fornecedores para o dropdown"""
        try:
            suppliers = self.db_manager.query("SELECT DISTINCT supplier_id, vendor_name FROM supplier_database_table ORDER BY vendor_name")
            options = [ft.dropdown.Option("", "Selecione um fornecedor...")]
            
            for supplier in suppliers:
                options.append(ft.dropdown.Option(
                    key=str(supplier['supplier_id']),
                    text=supplier['vendor_name']
                ))
            
            return options
        except Exception as e:
            print(f"Erro ao carregar fornecedores: {e}")
            return [ft.dropdown.Option("", "Erro ao carregar fornecedores")]
    
    def send_individual_email(self):
        """Envia email individual para o fornecedor selecionado"""
        if not self.supplier_dropdown_email.value:
            if self.show_snack_bar:
                self.show_snack_bar("Selecione um fornecedor primeiro!", True)
            return
        
        # Verificar se há emails para enviar
        if not self.supplier_emails_data:
            if self.show_snack_bar:
                self.show_snack_bar("Nenhum email encontrado para o fornecedor!", True)
            return
        
        # Buscar dados do fornecedor
        supplier_data = self.db_manager.query("SELECT vendor_name, supplier_email, bu FROM supplier_database_table WHERE supplier_id = ?", (self.supplier_dropdown_email.value,))
        if not supplier_data:
            if self.show_snack_bar:
                self.show_snack_bar("Fornecedor não encontrado!", True)
            return
        
        supplier = supplier_data[0]
        recipient_emails = '; '.join(self.supplier_emails_data)
        
        # Criar dialog de confirmação
        dialog = EmailSendConfirmationDialog(
            supplier_name=supplier['vendor_name'],
            supplier_email=recipient_emails,
            on_confirm=lambda e: self._confirm_send_email(dialog, supplier, recipient_emails),
            on_cancel=lambda e: self._cancel_send_email(dialog),
            get_theme_colors=self.get_theme_colors,
            get_theme_name=self.get_theme_name,
            page_ref=self.page_ref
        )
        
        if self.page_ref:
            self.page_ref.overlay.append(dialog)
            dialog.open = True
            self.page_ref.update()
    
    def _confirm_send_email(self, dialog, supplier, recipient_emails):
        """Confirma e envia o email"""
        dialog.open = False
        if self.page_ref:
            self.page_ref.update()
        
        # Enviar em thread separada
        def send_email_thread():
            try:
                # Inicializar COM na thread
                pythoncom.CoInitialize()
                
                try:
                    success, message = self.send_email_via_outlook(
                        recipient_emails,
                        supplier['vendor_name'],
                        supplier
                    )
                    
                    # Atualizar UI na thread principal
                    def update_ui():
                        if self.show_snack_bar:
                            self.show_snack_bar(message, not success)
                    
                    if self.page_ref:
                        self.page_ref.run_thread(update_ui)
                    
                finally:
                    pythoncom.CoUninitialize()
                    
            except Exception as e:
                def update_ui():
                    if self.show_snack_bar:
                        self.show_snack_bar(f"Erro inesperado: {str(e)}", True)
                if self.page_ref:
                    self.page_ref.run_thread(update_ui)
        
        threading.Thread(target=send_email_thread).start()
    
    def _cancel_send_email(self, dialog):
        """Cancela o envio do email"""
        dialog.open = False
        if self.page_ref:
            self.page_ref.update()
    
    def _create_individual_content(self):
        """Cria o conteúdo da aba individual"""
        return ft.Column([
            ft.Container(height=10),
            ft.Row([
                # Coluna esquerda - Seleção e ações
                ft.Container(
                    content=ft.Column([
                        ft.Text("Selecionar Fornecedor", size=16, weight="bold"),
                        ft.Container(height=5),
                        self.supplier_dropdown_email,
                        ft.Container(height=10),
                        # Container para mini cards dos emails
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Emails:", size=11, weight="bold"),
                                self.email_cards_container
                            ], spacing=3),
                            padding=8,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=6,
                            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.GREY_500),
                            width=400,
                            height=100
                        ),
                        ft.Container(height=5),
                        # Campo para adicionar emails
                        self.add_email_field,
                        ft.Container(height=10),
                        ft.Row([
                            ft.ElevatedButton(
                                "Enviar E-mail",
                                icon=ft.Icons.SEND,
                                on_click=lambda e: self.send_individual_email(),
                                bgcolor=ft.Colors.BLUE_600,
                                color=ft.Colors.WHITE
                            ),
                        ], spacing=10)
                    ], spacing=5),
                    padding=15,
                    border_radius=8,
                    width=400,
                    expand=False
                ),
                ft.Container(width=20),
                # Coluna direita - Preview do email
                ft.Container(
                    content=self.email_preview_container,
                    expand=True
                )
            ], expand=True)
        ], spacing=10, expand=True, scroll=ft.ScrollMode.AUTO)
    
    def _create_batch_content(self):
        """Cria o conteúdo da aba em lote (placeholder)"""
        return ft.Column([
            ft.Container(height=20),
            ft.Text("Funcionalidade em desenvolvimento...", size=16, color=ft.Colors.GREY_600),
        ], spacing=10, expand=True)
    
    def apply_theme_styling(self):
        """Aplica estilo do tema atual aos componentes"""
        try:
            if not self.get_theme_name or not self.get_theme_colors:
                return
                
            theme_name = self.get_theme_name(self.page_ref) if self.page_ref else "white"
            Colors = self.get_theme_colors(theme_name)
            
            # Aplicar cores aos componentes
            self.supplier_dropdown_email.bgcolor = Colors.get('field_background')
            self.supplier_dropdown_email.color = Colors.get('on_surface')
            self.supplier_dropdown_email.border_color = Colors.get('outline')
            
            self.add_email_field.bgcolor = Colors.get('field_background')
            self.add_email_field.color = Colors.get('on_surface')
            self.add_email_field.border_color = Colors.get('outline')
            
            # Atualizar componentes
            self.supplier_dropdown_email.update()
            self.add_email_field.update()
            
        except Exception as e:
            print(f"Erro ao aplicar tema aos componentes de email: {e}")
    
    def get_email_tabs(self):
        """Retorna as abas de email configuradas"""
        # Obter cores do tema
        if self.get_theme_name and self.get_theme_colors:
            theme_name = self.get_theme_name(self.page_ref) if self.page_ref else "white"
            Colors = self.get_theme_colors(theme_name)
        else:
            Colors = {
                'primary': ft.Colors.BLUE_600,
                'on_surface': ft.Colors.BLACK,
                'on_surface_variant': ft.Colors.GREY_600,
                'outline': ft.Colors.GREY_400
            }
        
        # Conteúdo centralizado para aba Individual
        individual_content = ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.CONSTRUCTION,
                    size=80,
                    color=Colors.get('primary', ft.Colors.BLUE_600)
                ),
                ft.Container(height=20),
                ft.Text(
                    "Envio Individual",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.get('on_surface', ft.Colors.BLACK)
                ),
                ft.Container(height=10),
                ft.Text(
                    "Funcionalidade em desenvolvimento...",
                    size=16,
                    color=Colors.get('on_surface_variant', ft.Colors.GREY_600)
                ),
                ft.Container(height=10),
                ft.Text(
                    "🚧 Em breve você poderá enviar scorecards individuais para fornecedores específicos",
                    size=12,
                    color=Colors.get('outline', ft.Colors.GREY_400),
                    text_align=ft.TextAlign.CENTER
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5
            ),
            alignment=ft.alignment.center,
            expand=True,
            width=None,
            height=None
        )
        
        # Conteúdo centralizado para aba em Lote
        batch_content = ft.Container(
            content=ft.Column([
                ft.Icon(
                    ft.Icons.CONSTRUCTION,
                    size=80,
                    color=Colors.get('primary', ft.Colors.BLUE_600)
                ),
                ft.Container(height=20),
                ft.Text(
                    "Envio em Lote",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=Colors.get('on_surface', ft.Colors.BLACK)
                ),
                ft.Container(height=10),
                ft.Text(
                    "Funcionalidade em desenvolvimento...",
                    size=16,
                    color=Colors.get('on_surface_variant', ft.Colors.GREY_600)
                ),
                ft.Container(height=10),
                ft.Text(
                    "🚧 Em breve você poderá enviar scorecards para múltiplos fornecedores simultaneamente",
                    size=12,
                    color=Colors.get('outline', ft.Colors.GREY_400),
                    text_align=ft.TextAlign.CENTER
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=5
            ),
            alignment=ft.alignment.center,
            expand=True,
            width=None,
            height=None
        )
        
        return ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Envio Individual",
                    icon=ft.Icons.PERSON,
                    content=individual_content
                ),
                ft.Tab(
                    text="Envio em Lote", 
                    icon=ft.Icons.GROUP,
                    content=batch_content
                ),
            ],
            expand=True
        )
    
    def initialize_suppliers_dropdown(self):
        """Inicializa o dropdown de fornecedores"""
        try:
            self.supplier_dropdown_email.options = self.load_suppliers_for_email()
            self.supplier_dropdown_email.update()
        except Exception as e:
            print(f"Erro ao inicializar dropdown de fornecedores: {e}")


class EmailSendConfirmationDialog(ft.AlertDialog):
    def __init__(self, supplier_name, supplier_email, on_confirm, on_cancel, 
                 get_theme_colors=None, get_theme_name=None, page_ref=None):
        super().__init__()
        self.supplier_name = supplier_name
        self.supplier_email = supplier_email
        self.on_confirm_callback = on_confirm
        self.on_cancel_callback = on_cancel
        
        # Obter cores do tema atual
        if get_theme_name and get_theme_colors and page_ref:
            theme_name = get_theme_name(page_ref)
            Colors = get_theme_colors(theme_name)
        else:
            Colors = {'on_surface': ft.Colors.BLACK, 'surface_variant': ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                     'outline': ft.Colors.GREY_300, 'primary': ft.Colors.BLUE_600, 'on_primary': ft.Colors.WHITE,
                     'secondary': ft.Colors.GREEN_600, 'tertiary': ft.Colors.ORANGE_700}
        
        self.title = ft.Text("📧 Confirmar Envio de Email", color=Colors.get('on_surface'))
        
        self.content = ft.Column([
            ft.Text(f"Deseja enviar automaticamente o scorecard para:", color=Colors.get('on_surface')),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.BUSINESS, color=Colors.get('primary'), size=20),
                        ft.Text(f"{self.supplier_name}", weight=ft.FontWeight.BOLD, color=Colors.get('on_surface'))
                    ], spacing=10),
                    ft.Row([
                        ft.Icon(ft.Icons.EMAIL, color=Colors.get('secondary'), size=20),
                        ft.Text(f"{self.supplier_email}", color=Colors.get('on_surface'))
                    ], spacing=10)
                ], spacing=5),
                padding=15,
                bgcolor=Colors.get('surface_variant'),
                border_radius=8,
                border=ft.border.all(1, Colors.get('outline'))
            ),
            ft.Text("⚡ O email será enviado automaticamente via Outlook (mala direta).", 
                   size=12, color=Colors.get('tertiary'), weight=ft.FontWeight.BOLD)
        ], tight=True, spacing=15, width=400)
        
        self.actions = [
            ft.TextButton(
                "Cancelar", 
                on_click=self.cancel,
                style=ft.ButtonStyle(color=Colors.get('on_surface'))
            ),
            ft.ElevatedButton(
                "Enviar Agora", 
                on_click=self.confirm,
                bgcolor=Colors.get('primary'),
                color=Colors.get('on_primary'),
                icon=ft.Icons.SEND
            )
        ]
        self.actions_alignment = ft.MainAxisAlignment.END
    
    def confirm(self, e):
        self.on_confirm_callback(e)
    
    def cancel(self, e):
        self.on_cancel_callback(e)