import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
from datetime import datetime, time # Importar 'time'
import csv
from dateutil.relativedelta import relativedelta 
from streamlit.errors import StreamlitAPIException

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(layout="wide")

# Inicializar session_state
if 'pagina_selecionada' not in st.session_state:
    st.session_state.pagina_selecionada = "Home"
if 'registration_count' not in st.session_state:
    st.session_state.registration_count = 0

# --- Nomes dos Arquivos ---
CSV_FILE = "registros.csv"
BASE_FILE = "Base.xlsx"
GESTOR_FILE = "gestor.xlsx"
CSV_FEEDBACK = "feedback_gestor_programa.csv"
TRILHA_FILE = "progresso_trilha.csv" 
SOMAR_FILE = "somar_ideias.xlsx" 
TREINAMENTOS_FILE = "treinamentos.csv" 

# --- Senhas ---
try:
    SENHA_GESTOR = st.secrets["SENHA_GESTOR"]
    ACCESS_PASSWORD = st.secrets["SENHA_ADMIN"]
except FileNotFoundError:
    st.warning("Arquivo 'secrets.toml' não encontrado. Usando senhas de fallback.")
    SENHA_GESTOR = "cocal@2025" 
    ACCESS_PASSWORD = "cocal"
except KeyError:
    st.warning("Senhas não configuradas no 'secrets.toml'. Usando senhas de fallback.")
    SENHA_GESTOR = "cocal@2025"
    ACCESS_PASSWORD = "cocal"

# --- Tópicos da Trilha ---
TRILHA_MESES = {
    "Mes_1": "Mês 1: Onboarding, Integração (DP, TI, S.T.) e Cultura Cocal.",
    "Mes_2": "Mês 2: Alinhamento com Gestor, Treinamento Somar Ideias e Engajamento à Cultura.",
    "Mes_3": "Mês 3: Feedback com Gestor e Treinamento: Conhecimento na Função.",
    "Mes_4": "Mês 4: Registro da Ideia (Somar) e Treinamento: Segurança.",
    "Mes_5": "Mês 5: Apresentação da Ideia de Melhoria (RH/Gestor) e Feedback de Desempenho.",
    "Mes_6": "Mês 6: Alinhamento Final (RH/Gestor) e Análise de Efetivação/Remanejamento."
}
COLUNAS_TRILHA = ['Matricula', 'Mes_1', 'Mes_2', 'Mes_3', 'Mes_4', 'Mes_5', 'Mes_6']
COLUNAS_REGISTROS = [
    'Data_Registro', 'Colaborador', 'Setor', 
    'Categoria_Atividade', 'Nome_Projeto', 'Data_Inicio_Projeto', 'Previsao_Conclusao',
    'Status', 'Percentual_Concluido', 'Observacoes'
]
DATE_COLS_REGISTROS = ['Data_Registro', 'Data_Inicio_Projeto', 'Previsao_Conclusao']
# --- ATUALIZADO: Colunas de Treinamento ---
COLUNAS_TREINAMENTOS = [
    'Nome_Treinamento', 'Data', 'Inicio', 'Termino', 'Modalidade', 'Local_Link', 'Unidade'
]
DATE_COLS_TREINAMENTOS = ['Data'] 
TIME_COLS_TREINAMENTOS = ['Inicio', 'Termino'] 

# --- 2. FUNÇÕES DE APOIO (ATUALIZADAS) ---

def initialize_data(): # Registros de Atividades
    if not os.path.exists(CSV_FILE):
        df = pd.DataFrame(columns=COLUNAS_REGISTROS)
        df.to_csv(CSV_FILE, index=False, encoding='utf-8')
        return df
    else:
        try:
            df = pd.read_csv(CSV_FILE)
            if not all(col in df.columns for col in COLUNAS_REGISTROS):
                st.warning("O arquivo 'registros.csv' está desatualizado. Apague-o na área de Administração.")
                for col in COLUNAS_REGISTROS:
                    if col not in df.columns:
                        df[col] = pd.NA
                df = df[COLUNAS_REGISTROS]
            
            for col in DATE_COLS_REGISTROS:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
            
            return df
        except Exception as e:
            st.error(f"Erro ao ler {CSV_FILE}: {e}. Pode ser necessário apagá-lo na área de Administração.")
            return pd.DataFrame(columns=COLUNAS_REGISTROS)

def initialize_trilha(): # Trilha de Desenvolvimento
    if not os.path.exists(TRILHA_FILE):
        try:
            base_df = pd.read_excel(BASE_FILE, dtype={'MATRICULA': str})
            if "MATRICULA" in base_df.columns:
                matriculas = base_df["MATRICULA"].dropna().unique()
                trilha_data = []
                for m in matriculas:
                    trilha_data.append({
                        'Matricula': m, 
                        'Mes_1': False, 'Mes_2': False, 'Mes_3': False,
                        'Mes_4': False, 'Mes_5': False, 'Mes_6': False
                    })
                df_trilha = pd.DataFrame(trilha_data, columns=COLUNAS_TRILHA)
                df_trilha.to_csv(TRILHA_FILE, index=False, encoding='utf-8')
                return df_trilha
            else:
                st.error("Arquivo 'Base.xlsx' não contém a coluna 'MATRICULA'.")
                return pd.DataFrame(columns=COLUNAS_TRILHA)
        except Exception as e:
            st.error(f"Erro ao inicializar progresso_trilha.csv: {e}")
            return pd.DataFrame(columns=COLUNAS_TRILHA)
    else:
        try:
            return pd.read_csv(TRILHA_FILE, dtype={'Matricula': str})
        except Exception as e:
            st.error(f"Erro ao ler {TRILHA_FILE}: {e}")
            return pd.DataFrame(columns=COLUNAS_TRILHA)

def initialize_somar(): # Somar Ideias
    if not os.path.exists(SOMAR_FILE):
        # st.warning(f"O arquivo '{SOMAR_FILE}' não foi encontrado. O indicador do Somar Ideias está desabilitado.")
        # st.warning("Por favor, adicione o arquivo ao repositório do app.")
        return pd.DataFrame()
    else:
        try:
            df = pd.read_excel(SOMAR_FILE)
            cols_necessarias = ['STATUS IDEIA', 'NOME RESPONSAVEL', 'IDEIAS ENVIADAS']
            if not all(col in df.columns for col in cols_necessarias):
                st.error(f"O arquivo '{SOMAR_FILE}' não contém as colunas necessárias: {cols_necessarias}")
                return pd.DataFrame()
            return df
        except Exception as e:
            st.error(f"Erro ao ler {SOMAR_FILE}: {e}")
            return pd.DataFrame()

# --- ATUALIZADO: Função de Treinamentos ---
def initialize_treinamentos():
    if not os.path.exists(TREINAMENTOS_FILE):
        df = pd.DataFrame(columns=COLUNAS_TREINAMENTOS)
        df.to_csv(TREINAMENTOS_FILE, index=False, encoding='utf-8')
        return df
    else:
        try:
            df = pd.read_csv(TREINAMENTOS_FILE)
            if not all(col in df.columns for col in COLUNAS_TREINAMENTOS):
                st.warning(f"O arquivo '{TREINAMENTOS_FILE}' está desatualizado. Apague-o na área de Administração.")
                for col in COLUNAS_TREINAMENTOS:
                    if col not in df.columns:
                        df[col] = pd.NA
                df = df[COLUNAS_TREINAMENTOS] # Garante a ordem e colunas corretas
            
            # Converter colunas de data e hora
            for col in DATE_COLS_TREINAMENTOS:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
            # Corrigir conversão de hora
            for col in TIME_COLS_TREINAMENTOS:
                df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
            
            return df
        except Exception as e:
            st.error(f"Erro ao ler {TREINAMENTOS_FILE}: {e}")
            return pd.DataFrame(columns=COLUNAS_TREINAMENTOS)


def mudar_pagina(nova_pagina):
    st.session_state.pagina_selecionada = nova_pagina

def delete_all_data():
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
        st.success("✅ Registros de ATIVIDADES foram apagados.")
    
    if os.path.exists(TRILHA_FILE):
        os.remove(TRILHA_FILE)
        st.success("✅ Progresso de TRILHAS foi apagado.")
        
    if os.path.exists(TREINAMENTOS_FILE):
        os.remove(TREINAMENTOS_FILE)
        st.success("✅ Calendário de TREINAMENTOS foi apagado.")
    
    st.rerun()

# --- Funções de Apoio (CRUD) ---
def get_base64_of_bin_file(bin_file):
    file_path = os.path.abspath(bin_file)
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        st.error(f"Erro ao carregar imagem: {bin_file}, {e}")
        return ""

# --- ATUALIZADO: CSS SIMPLIFICADO ---
def get_home_page_css(desktop_img, mobile_img):
    """Gera o CSS com Media Query para trocar APENAS o fundo."""
    
    try:
        desktop_ext = os.path.splitext(desktop_img)[1][1:]
        desktop_bin_str = get_base64_of_bin_file(desktop_img)
    except Exception:
        desktop_ext = "jpg"; desktop_bin_str = ""

    try:
        mobile_ext = os.path.splitext(mobile_img)[1][1:]
        mobile_bin_str = get_base64_of_bin_file(mobile_img)
    except Exception:
        mobile_ext = "jpg"; mobile_bin_str = ""

    # CSS Padrão (Desktop)
    css = f'''
    <style>
        /* Esconder sidebar na Home */
        [data-testid="stSidebar"] {{
            display: none;
        }}
        
        /* Fundo Padrão (MOBILE) */
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/{mobile_ext};base64,{mobile_bin_str}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: scroll;
        }}
        
        [data-testid="stHeader"] {{
            background-color: transparent;
        }}
        
        h1, h2, h3, p {{
            color: black !important;
            text-shadow: none !important;
        }}
        
        div[data-testid="stButton"] > button {{
            background-color: #FFFFFF;
            border: 1px solid #DDDDDD;
            border-radius: 10px;
            font-weight: bold;
        }}
        
        div[data-testid="stButton"] > button > div > span {{
            color: #000000 !important;
            text-shadow: none !important;
            filter: none !important;
        }}
        
        div[data-testid="stButton"] > button:hover {{
            background-color: #EEEEEE;
            color: #000000 !important;
            border: 1px solid #CCCCCC;
        }}

        /* --- AJUSTE DE POSIÇÃO DOS BOTÕES --- */
        .button-container {{
            /* Posição para Celular: 45% da altura (mais para cima) */
            margin-top: 45vh;
        }}
        
        /* Media Query para DESKTOP (Min-width) */
        @media (min-width: 701px) {{
            /* Fundo Desktop */
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/{desktop_ext};base64,{desktop_bin_str}");
            }}

            /* Posição para Desktop: 55% da altura da tela */
            .button-container {{
                margin-top: 55vh; 
            }}
        }}
    </style>
    '''
    return css

# --- 3. EXECUÇÃO DE CSS/FUNDO E BARRA LATERAL ---

st.sidebar.title("Menu")
# ATUALIZADO: Menu de páginas
st.sidebar.radio(
    "Selecione a funcionalidade:",
    ("Home", "Página do Estagiário", "Treinamentos", "Painel de Indicadores", "Avaliação do Gestor", "Administração"),
    key="pagina_selecionada"
)
st.sidebar.divider()

# Carregar dados
df_data = initialize_data()
df_trilha = initialize_trilha() 
df_somar = initialize_somar() # Carregar dados do Somar
df_treinamentos = initialize_treinamentos() # Carregar dados de treinamentos

# --- FILTROS SÓ NO PAINEL DE INDICADORES ---
if st.session_state.pagina_selecionada == "Painel de Indicadores":
    st.sidebar.title("Filtros")
    data_inicio = st.sidebar.date_input("Data Início", datetime.now().date().replace(day=1), format="DD/MM/YYYY", key="filtro_data_inicio")
    data_fim = st.sidebar.date_input("Data Fim", datetime.now().date(), format="DD/MM/YYYY", key="filtro_data_fim")
    
    try:
        # --- CORREÇÃO AQUI: Ler datas como datetime, mas MATRICULA como string ---
        base_tmp = pd.read_excel(BASE_FILE, dtype={'MATRICULA': str})
        lista_estagiarios = sorted(base_tmp["COLABORADOR"].dropna().unique().tolist())
        lista_estagiarios.insert(0, "Todos")
        filtro_estagiario_sidebar = st.sidebar.selectbox("Estagiário", lista_estagiarios, key="filtro_estagiario")
    except Exception as e:
        st.sidebar.warning("Não foi possível carregar lista de estagiários (base.xlsx).")
        filtro_estagiario_sidebar = "Todos"
else:
    # Definir valores padrão para as outras páginas não quebrarem
    data_inicio = datetime.now().date().replace(day=1)
    data_fim = datetime.now().date()
    filtro_estagiario_sidebar = "Todos"


# --- 4. PÁGINAS ---

# ========= HOME (LAYOUT ÚNICO E SIMPLIFICADO) =========
if st.session_state.pagina_selecionada == "Home":
    
    try:
        css = get_home_page_css("fundo.jpg", "fundocelular.jpg")
        st.markdown(css, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o fundo: {e}")

    
    st.markdown('<div class="button-container">', unsafe_allow_html=True) 
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📋 Página do Estagiário", use_container_width=True, on_click=mudar_pagina, args=("Página do Estagiário",), key="reg_desktop")
        # st.button("Trilha de Desenvolvimento", use_container_width=True, key="trilha_desktop", on_click=mudar_pagina, args=("Página do Estagiário",)) 
    with col2:
        st.button("📊 Painel de Indicadores", use_container_width=True, on_click=mudar_pagina, args=("Painel de Indicadores",), key="gestor_desktop")
        st.button("💬 Avaliação do Gestor", use_container_width=True, on_click=mudar_pagina, args=("Avaliação do Gestor",), key="feed_desktop")
    with col3:
        st.button("🗓️ Treinamentos", use_container_width=True, key="treina_desktop", on_click=mudar_pagina, args=("Treinamentos",))
        st.button("🔒 Administração", use_container_width=True, on_click=mudar_pagina, args=("Administração",), key="admin_desktop")
    
    st.markdown('</div>', unsafe_allow_html=True)


# ========= NOVA PÁGINA: PAINEL DE INDICADORES =========
elif st.session_state.pagina_selecionada == "Painel de Indicadores":
    
    st.button("🏠 Voltar para Home", on_click=mudar_pagina, args=("Home",))
    st.title("📊 Painel de Indicadores do Programa")
    st.markdown("---")
    
    # --- 1. LÓGICA DE LOGIN DO GESTOR (ATUALIZADA COM st.form) ---
    if "gestor_autenticado" not in st.session_state:
        st.session_state.gestor_autenticado = False
    if "dados_gestor" not in st.session_state:
        st.session_state.dados_gestor = None

    if not st.session_state.gestor_autenticado:
        st.subheader("🔐 Acesso Restrito ao Gestor")
        
        with st.form(key="gestor_login_indicadores_form"):
            matricula = st.text_input("Digite sua matrícula:")
            senha = st.text_input("Digite a senha:", type="password")
            entrar = st.form_submit_button("Entrar")

        if entrar:
            try:
                base_gestor = pd.read_excel(GESTOR_FILE)
            except Exception as e:
                st.error(f"Erro ao carregar planilha de gestores: {e}")
                base_gestor = pd.DataFrame(columns=["MATRICULA", "COLABORADOR"])

            if matricula and senha == SENHA_GESTOR:
                gestor = base_gestor.loc[base_gestor["MATRICULA"].astype(str) == str(matricula)]
                if not gestor.empty:
                    st.session_state.gestor_autenticado = True
                    st.session_state.dados_gestor = gestor.iloc[0]
                    st.success(f"✅ Bem-vindo, {gestor.iloc[0]['COLABORADOR']}!")
                    st.rerun()
                else:
                    st.error("❌ Matrícula não encontrada.")
            else:
                st.error("❌ Matrícula ou senha incorreta.")

    # --- 2. SE O GESTOR ESTIVER LOGADO ---
    if st.session_state.gestor_autenticado:
        
        # --- SEÇÃO DE DASHBOARD ---
        st.subheader("Análise de Feedbacks (Gestores)")
        if os.path.exists(CSV_FEEDBACK):
            df_feedback = pd.read_csv(CSV_FEEDBACK)
        else:
            df_feedback = pd.DataFrame() 

        cols_competencias = [] 
        
        if not df_feedback.empty:
            df_display_feedback = df_feedback.copy()
            colunas_para_renomear = {'Data_Hora': 'DATA', 'Gestor': 'GESTOR'}
            df_display_feedback.rename(columns=colunas_para_renomear, inplace=True)

            if filtro_estagiario_sidebar != "Todos" and "Estagiario" in df_display_feedback.columns:
                df_display_feedback = df_display_feedback[df_display_feedback["Estagiario"] == filtro_estagiario_sidebar]
                df_feedback = df_feedback[df_feedback["Estagiario"] == filtro_estagiario_sidebar]

            colunas_para_ocultar = ['Feedback_Livre', 'sugestao_melhoria']
            for col in colunas_para_ocultar:
                if col in df_display_feedback.columns:
                    df_display_feedback = df_display_feedback.drop(columns=[col])
            
            st.write("**Tabela de Feedbacks Recebidos**")
            st.dataframe(df_display_feedback, use_container_width=True)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Distribuição das Avaliações (Feedback)**")
                
                colunas_excluir = ['DATA', 'GESTOR', 'Data_Hora', 'Gestor', 'Estagiario', 'Feedback_Livre', 'sugestao_melhoria']
                cols_competencias = [col for col in df_feedback.columns if col not in colunas_excluir]
                
                if not cols_competencias or df_feedback.empty:
                    st.warning("Nenhum dado de competência (Ex: 'Iniciativa' ou 'estrutura_suporte') foi encontrado no feedback.")
                    df_grafico = pd.DataFrame() 
                else:
                    mapa_notas = {"Excelente": 4, "Bom": 3, "Regular": 2, "Ruim": 1, None: 0}
                    mapa_cores = {
                         'Excelente': '#76B82A', 'Bom': '#30515F',
                         'Regular': '#B2B2B2', 'Ruim': '#B2B2B2'
                    }
                    
                    df_grafico = df_feedback.copy()
                    df_pizza_data = []
                    for col in cols_competencias:
                        if col in ['Iniciativa', 'Aprendizagem', 'Qualidade', 'Relacoes']:
                            df_grafico[f'Nota_{col}'] = df_grafico[col].map(mapa_notas).fillna(0)
                        
                        contagem = df_grafico[col].value_counts().reset_index()
                        contagem.columns = ['Avaliação', 'Contagem']
                        df_pizza_data.append(contagem)

                    if df_pizza_data:
                        df_pizza_total = pd.concat(df_pizza_data).groupby('Avaliação').sum().reset_index()
                        
                        fig_pie = px.pie(df_pizza_total, names='Avaliação', values='Contagem', 
                                         color='Avaliação', 
                                         color_discrete_map=mapa_cores) 
                        st.plotly_chart(fig_pie, use_container_width=True)
                    else:
                        st.info("Sem dados para o gráfico de pizza de feedback.")
            
            with col2:
                st.markdown("**Status dos Projetos (Estagiários)**")
                
                if not df_data.empty:
                    df_projetos_unicos = df_data.sort_values(by='Data_Registro', ascending=True).drop_duplicates(subset=['Colaborador', 'Nome_Projeto'], keep='last')
                    
                    if filtro_estagiario_sidebar != "Todos":
                        df_projetos_unicos = df_projetos_unicos[df_projetos_unicos['Colaborador'] == filtro_estagiario_sidebar]
                    
                    df_status_counts = df_projetos_unicos['Status'].value_counts().reset_index()
                    df_status_counts.columns = ['Status', 'Contagem']

                    mapa_cores_status = {
                        'Concluído': '#76B82A', 'Iniciado': '#30515F', 'Pendente': '#B2B2B2'
                    }

                    fig_pie_status = px.pie(df_status_counts, names='Status', values='Contagem', 
                                             color='Status',
                                             color_discrete_map=mapa_cores_status)
                    st.plotly_chart(fig_pie_status, use_container_width=True)
                else:
                    st.info("Nenhum projeto registrado.")

            if not df_grafico.empty and cols_competencias:
                cols_notas_existentes = [f'Nota_{col}' for col in cols_competencias if f'Nota_{col}' in df_grafico.columns]
                
                if cols_notas_existentes: 
                    st.markdown(f"**Média por Competência ({filtro_estagiario_sidebar})**")
                    medias = []
                    for col_nota, col_nome in zip(cols_notas_existentes, cols_competencias):
                        media = df_grafico[col_nota].mean()
                        medias.append({'Competência': col_nome, 'Média': media})
                    
                    df_medias = pd.DataFrame(medias)
                    
                    fig_bar = px.bar(df_medias, x='Competência', y='Média', 
                                     title="Média por Competência (4=Excelente, 1=Ruim)",
                                     text=df_medias['Média'].apply(lambda x: f'{x:.2f}'),
                                     range_y=[0, 4],
                                     color='Média', 
                                     color_continuous_scale=[[0, '#30515F'], [1, '#76B82A']], 
                                     range_color=[0, 4] 
                                    )
                    
                    fig_bar.update_layout(bargap=0.5)
                    fig_bar.update_layout(coloraxis_showscale=False)
                    
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("O gráfico de média por competência só funciona com os novos formulários de feedback (Iniciativa, Qualidade, etc.)")
        else:
            st.info("Nenhum feedback registrado até o momento.")
            df_grafico = pd.DataFrame() 

        # --- SEÇÃO DE RELATÓRIO DE ATIVIDADES ---
        st.markdown("---")
        st.subheader("Relatório de Atividades dos Estagiários")
        
        if not df_data.empty:
            try:
                df_data_copy = df_data.copy()
                df_filtrada = df_data_copy[
                    (df_data_copy['Data_Registro'].dt.date >= data_inicio) &
                    (df_data_copy['Data_Registro'].dt.date <= data_fim)
                ]
                if filtro_estagiario_sidebar != "Todos":
                    df_filtrada = df_filtrada[df_filtrada['Colaborador'] == filtro_estagiario_sidebar]
                
                for col in DATE_COLS_REGISTROS:
                    if col in df_filtrada.columns:
                        df_filtrada[col] = df_filtrada[col].dt.strftime('%d/%m/%Y').replace('NaT', '')
                
                st.dataframe(df_filtrada, use_container_width=True)
                st.info(f"Exibindo {len(df_filtrada)} de {len(df_data)} registros totais.")
            except Exception as e:
                st.error(f"Erro ao processar e filtrar os dados de atividades: {e}")
                st.dataframe(df_data)
        else:
            st.info("Nenhuma atividade registrada para os filtros selecionados.")
            
            
        # --- SEÇÃO: RANKING DE DESEMPENHO ---
        st.markdown("---")
        st.subheader("🏆 Ranking de Desempenho dos Estagiários")
        
        try:
            base_estagiarios = pd.read_excel(BASE_FILE, dtype={'MATRICULA': str})
            df_ranking = pd.DataFrame(base_estagiarios["COLABORADOR"].dropna().unique(), columns=["Estagiário"])

            cols_notas_existentes = [f'Nota_{col}' for col in cols_competencias if f'Nota_{col}' in df_grafico.columns]
            
            if not df_grafico.empty and cols_notas_existentes: 
                df_notas_melted = df_grafico.melt(id_vars=['Estagiario'], value_vars=cols_notas_existentes, value_name='Nota')
                df_notas_medias = df_notas_melted.groupby('Estagiario')['Nota'].mean().reset_index()
                df_notas_medias.rename(columns={'Estagiario': 'Estagiário', 'Nota': 'Nota Média (de 4.0)'}, inplace=True)
                df_ranking = pd.merge(df_ranking, df_notas_medias, on="Estagiário", how="left")
            else:
                df_ranking["Nota Média (de 4.0)"] = 0.0

            if not df_data.empty:
                df_projetos_unicos = df_data.sort_values(by='Data_Registro', ascending=True).drop_duplicates(subset=['Colaborador', 'Nome_Projeto'], keep='last')
                
                df_concluidos = df_projetos_unicos[df_projetos_unicos['Status'] == 'Concluído'].groupby('Colaborador')['Nome_Projeto'].count().reset_index()
                df_concluidos.rename(columns={'Colaborador': 'Estagiário', 'Nome_Projeto': 'Projetos Concluídos'}, inplace=True)
                df_ranking = pd.merge(df_ranking, df_concluidos, on="Estagiário", how="left")

                hoje = pd.to_datetime(datetime.now().date())
                df_atrasados = df_projetos_unicos[
                    (df_projetos_unicos['Status'].isin(['Iniciado', 'Pendente'])) &
                    (df_projetos_unicos['Previsao_Conclusao'] < hoje)
                ].groupby('Colaborador')['Nome_Projeto'].count().reset_index()
                df_atrasados.rename(columns={'Colaborador': 'Estagiário', 'Nome_Projeto': 'Projetos Atrasados'}, inplace=True)
                df_ranking = pd.merge(df_ranking, df_atrasados, on="Estagiário", how="left")
                
            else:
                df_ranking["Projetos Concluídos"] = 0
                df_ranking["Projetos Atrasados"] = 0

            df_ranking.fillna(0, inplace=True)
            df_ranking = df_ranking.sort_values(by=["Nota Média (de 4.0)", "Projetos Concluídos", "Projetos Atrasados"], ascending=[False, False, True])
            
            st.dataframe(df_ranking, use_container_width=True,
                         column_config={
                             "Nota Média (de 4.0)": st.column_config.NumberColumn(format="%.2f ⭐"),
                             "Projetos Atrasados": st.column_config.NumberColumn(format="%d ⚠️")
                         })

        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o ranking de desempenho: {e}")
            
        # --- SEÇÃO: INDICADOR SOMAR IDEIAS ---
        st.markdown("---")
        st.subheader("💡 Indicador do Programa Somar Ideias")
        
        if df_somar.empty:
            st.info("O indicador do Somar Ideias não pôde ser carregado. Verifique o arquivo 'somar_ideias.xlsx'.")
        else:
            try:
                # Agrupar por responsável e status, somando as ideias
                df_somar_grouped = df_somar.groupby(['NOME RESPONSAVEL', 'STATUS IDEIA'])['IDEIAS ENVIADAS'].sum().reset_index()
                
                # Pivotar para ter status como colunas
                df_somar_pivot = df_somar_grouped.pivot_table(index='NOME RESPONSAVEL', 
                                                              columns='STATUS IDEIA', 
                                                              values='IDEIAS ENVIADAS', 
                                                              aggfunc='sum').fillna(0)
                
                # Calcular o Total
                df_somar_pivot['Total Ideias'] = df_somar_pivot.sum(axis=1)
                
                # Juntar com a base de estagiários para incluir quem não enviou
                base_estagiarios_nomes = base_estagiarios[['COLABORADOR']].drop_duplicates()
                df_somar_final = pd.merge(base_estagiarios_nomes, df_somar_pivot, 
                                          left_on='COLABORADOR', right_on='NOME RESPONSAVEL', 
                                          how='left').fillna(0)
                
                df_somar_final.rename(columns={'COLABORADOR': 'Estagiário'}, inplace=True)
                
                # Aplicar filtro da sidebar
                if filtro_estagiario_sidebar != "Todos":
                    df_somar_final = df_somar_final[df_somar_final['Estagiário'] == filtro_estagiario_sidebar]
                    df_somar_grouped = df_somar_grouped[df_somar_grouped['NOME RESPONSAVEL'] == filtro_estagiario_sidebar]
                
                
                st.write("**Tabela Resumo - Somar Ideias**")
                st.dataframe(df_somar_final, use_container_width=True)
                
                # Gráfico de Barras do Somar
                st.write("**Gráfico - Total de Ideias por Estagiário**")
                
                mapa_cores_somar = {
                    'IMPLEMENTADA': '#76B82A',
                    'EM EXECUÇÃO': '#30515F',
                    'EM ANÁLISE': '#B2B2B2',
                    'REJEITADA': '#E00000' # Um vermelho para rejeitada
                }
                
                # Precisamos do df_somar_grouped (antes de pivotar) para o gráfico de barras empilhadas
                fig_somar = px.bar(df_somar_grouped, 
                                   x='NOME RESPONSAVEL', 
                                   y='IDEIAS ENVIADAS', 
                                   color='STATUS IDEIA',
                                   title='Ideias Enviadas por Estagiário e Status',
                                   color_discrete_map=mapa_cores_somar,
                                   labels={'NOME RESPONSAVEL': 'Estagiário', 'IDEIAS ENVIADAS': 'Quantidade de Ideias'})
                
                st.plotly_chart(fig_somar, use_container_width=True)

            except Exception as e:
                st.error(f"Ocorreu um erro ao processar os dados do Somar Ideias: {e}")


# ========= PÁGINA DO ESTAGIÁRIO (REGISTRO + TRILHA + FEEDBACKS) =========
elif st.session_state.pagina_selecionada == "Página do Estagiário":
    
    st.button("🏠 Voltar para Home", on_click=mudar_pagina, args=("Home",))
    
    st.title("👨‍🎓 Página do Estagiário")

    try:
        # --- CORREÇÃO AQUI: Ler datas como datetime, mas MATRICULA como string ---
        base = pd.read_excel(BASE_FILE, dtype={'MATRICULA': str})
    except Exception as e:
        st.warning(f"Não foi possível carregar {BASE_FILE}: {e}")
        base = pd.DataFrame(columns=["MATRICULA", "COLABORADOR", "DESCRIÇÃO LOCAL", "UNIDADE", "ADMISSAO", "TERMINO CONTRATO"])

    try:
        if "DESCRIÇÃO LOCAL" in base.columns:
            lista_setores = sorted(base["DESCRIÇÃO LOCAL"].dropna().unique().tolist())
        else:
            lista_setores = []
    except Exception as e:
        st.warning(f"Não foi possível carregar lista de setores: {e}")
        lista_setores = []
    lista_setores.append("Outros") 

    st.write("Digite sua matrícula para continuar:")
    
    # --- ATUALIZADO: Login com st.form ---
    with st.form(key="estagiario_login_form"):
        matricula = st.text_input("Matrícula", key="matricula_input")
        confirmar = st.form_submit_button("Confirmar matrícula")

    if confirmar:
        if matricula:
            st.session_state["matricula_digitada"] = matricula
            st.rerun() # Força o recarregamento da página com a matrícula
        else:
            st.warning("Por favor, digite uma matrícula antes de confirmar.")

    if st.session_state.get("matricula_digitada"):
        # --- CORREÇÃO AQUI: Não precisa mais de .astype() ---
        estagiario = base.loc[base["MATRICULA"] == str(matricula)] if "MATRICULA" in base.columns else pd.DataFrame()

        if not estagiario.empty:
            nome = estagiario["COLABORADOR"].values[0]
            setor_estagiario = estagiario["DESCRIÇÃO LOCAL"].values[0] 
            
            # --- ATUALIZAÇÃO IMPORTANTE ---
            # Garantir que a coluna UNIDADE existe
            if "UNIDADE" not in estagiario.columns:
                st.error("A coluna 'UNIDADE' não foi encontrada no Base.xlsx. Não consigo filtrar os treinamentos.")
                unidade = "N/A" # Definir um padrão para evitar que o app quebre
            else:
                unidade = estagiario["UNIDADE"].values[0] # <--- PEGAMOS A UNIDADE AQUI
            
            st.success(f"Bem-vindo(a), **{nome.split()[0]}** ({setor_estagiario} - {unidade}) 👋")
            
            # --- 6. 🔔 MEUS PRÓXIMOS TREINAMENTOS (NOVO) ---
            st.subheader(f"🔔 Próximos Treinamentos ({unidade})")
            
            hoje = datetime.now().date()
            # Filtra treinamentos futuros E pela unidade do estagiário
            df_treinamentos_filtrados = df_treinamentos[
                (df_treinamentos['Data'].dt.date >= hoje) &
                (df_treinamentos['Unidade'] == unidade)
            ].copy()
            
            if df_treinamentos_filtrados.empty:
                st.info(f"Nenhum treinamento agendado para sua unidade ({unidade}) no momento.")
            else:
                df_treinamentos_filtrados.sort_values(by='Data', ascending=True, inplace=True)
                st.warning("Você tem treinamentos agendados! Veja abaixo:")
                
                for idx, row in df_treinamentos_filtrados.iterrows():
                    with st.container(border=True):
                        st.subheader(f"📍 {row['Nome_Treinamento']}")
                        st.caption(f"**🗓️ Data:** {row['Data'].strftime('%d/%m/%Y')}")
                        st.caption(f"**⏰ Horário:** {row['Inicio'].strftime('%H:%M')} - {row['Termino'].strftime('%H:%M')}")
                        st.caption(f"**💻 Modalidade:** {row['Modalidade']}")
                        
                        if row['Modalidade'] == "Presencial":
                            st.caption(f"**📍 Local:** {row['Local_Link']}")
                        else:
                            if str(row['Local_Link']).startswith('http'):
                                st.link_button("Acessar Link", row['Local_Link'])
                            else:
                                st.caption(f"**🔗 Link:** {row['Local_Link']}")
            
            st.divider()
            # --- FIM DA NOVA SEÇÃO ---

            # --- 1. FORMULÁRIO PARA CRIAR NOVOS PROJETOS ---
            st.subheader("1. Registrar um Novo Projeto")
            with st.expander("Clique aqui para abrir o formulário de novo projeto"):
                with st.form(key="novo_projeto_form"):
                    st.write("Preencha todos os dados para criar um novo projeto no seu nome.")
                    col1, col2 = st.columns(2)
                    with col1:
                        data_registro = st.date_input("Data do Registro (Hoje)", datetime.now(), format="DD/MM/YYYY")
                        
                        try:
                            index_setor = lista_setores.index(setor_estagiario)
                        except ValueError:
                            index_setor = len(lista_setores) - 1 # "Outros"
                        
                        categoria = st.selectbox("Descrição do Local (Setor)", lista_setores, index=index_setor)
                        data_inicio_proj = st.date_input("Data de Início do Projeto", datetime.now(), format="DD/MM/YYYY")
                    
                    with col2:
                        status = st.selectbox("Status", ["Iniciado", "Pendente", "Concluído"], index=0)
                        nome_projeto = st.text_input("Nome do Projeto / Atividade Específica", placeholder="Ex: Controle de Processos de Segurança")
                        previsao_conclusao = st.date_input("Previsão de Conclusão", datetime.now(), format="DD/MM/YYYY")
                    
                    obs = st.text_area("Observações Iniciais")
                    
                    enviar = st.form_submit_button("Registrar Novo Projeto", type="primary")

                if enviar:
                    if not nome_projeto:
                        st.warning("Por favor, preencha o 'Nome do Projeto'.")
                    else:
                        if status == "Iniciado":
                            percentual = 0
                        elif status == "Pendente":
                            percentual = 50
                        elif status == "Concluído":
                            percentual = 100
                        else:
                            percentual = 0
                        
                        nova_linha = pd.DataFrame([{
                            'Data_Registro': data_registro.strftime('%d/%m/%Y'), 
                            'Colaborador': nome,
                            'Setor': setor_estagiario,
                            'Categoria_Atividade': categoria,
                            'Nome_Projeto': nome_projeto,
                            'Data_Inicio_Projeto': data_inicio_proj.strftime('%d/%m/%Y'),
                            'Previsao_Conclusao': previsao_conclusao.strftime('%d/%m/%Y'),
                            'Status': status,
                            'Percentual_Concluido': percentual,
                            'Observacoes': obs
                        }])
                        
                        nova_linha.to_csv(CSV_FILE, mode='a', header=False, index=False, encoding='utf-8')
                        st.success(f"✅ Novo projeto '{nome_projeto}' registrado com sucesso!")
                        st.rerun()

            st.divider()

            # --- 2. EDITOR DE PROJETOS EXISTENTES ---
            st.subheader("2. Atualizar Meus Projetos")
            st.info("Aqui você pode editar o Status, Previsão e Observações dos seus projetos existentes.")

            df_registros_estagiario = df_data[df_data['Colaborador'] == nome].copy()
            
            if df_registros_estagiario.empty:
                st.warning("Você ainda não tem projetos registrados. Use o formulário acima para criar o primeiro.")
            else:
                try:
                    df_projetos_unicos = df_registros_estagiario.sort_values(
                        by='Data_Registro', ascending=True
                    ).drop_duplicates(
                        subset='Nome_Projeto', keep='last'
                    )
                    
                    df_projetos_unicos.set_index(df_projetos_unicos.index, inplace=True)

                    edited_df = st.data_editor(
                        df_projetos_unicos,
                        key="editor_projetos",
                        use_container_width=True,
                        column_config={
                            "Nome_Projeto": st.column_config.Column("Nome do Projeto", disabled=True),
                            "Data_Inicio_Projeto": st.column_config.DateColumn("Início", format="DD/MM/YYYY", disabled=True),
                            
                            "Status": st.column_config.SelectboxColumn(
                                "Status", options=["Iniciado", "Pendente", "Concluído"], required=True 
                            ),
                            "Previsao_Conclusao": st.column_config.DateColumn( 
                                "Previsão Conclusão", format="DD/MM/YYYY"
                            ),
                            "Observacoes": st.column_config.TextColumn("Observações"),
                            
                            "Percentual_Concluido": None,
                            "Categoria_Atividade": None,
                            "Setor": None,
                            "Colaborador": None,
                            "Data_Registro": None
                        }
                    )

                    if st.button("Salvar Alterações", type="primary"):
                        df_full_data = initialize_data() 
                        
                        df_full_data.update(edited_df)
                        
                        def map_status_to_percent(status):
                            if status == "Iniciado": return 0
                            elif status == "Pendente": return 50
                            elif status == "Concluído": return 100
                            return 0

                        df_full_data['Percentual_Concluido'] = df_full_data['Status'].apply(map_status_to_percent)
                        
                        for col in DATE_COLS_REGISTROS:
                            df_full_data[col] = df_full_data[col].dt.strftime('%d/%m/%Y').replace('NaT', '')
                        
                        df_full_data.to_csv(CSV_FILE, index=False, encoding='utf-8')
                        
                        st.success("✅ Projetos atualizados com sucesso!")
                        st.rerun()

                except Exception as e:
                    st.error(f"Ocorreu um erro ao carregar seu editor de projetos: {e}")
                    st.error("Se o problema persistir, apague o 'registros.csv' na página de Administração.")

            st.divider()

            # --- 3. DASHBOARD PESSOAL (NOVO) ---
            st.subheader("3. Meu Desempenho (Projetos)")
            
            if not df_registros_estagiario.empty:
                df_meus_projetos_unicos = df_registros_estagiario.sort_values(by='Data_Registro', ascending=True).drop_duplicates(subset=['Nome_Projeto'], keep='last')
                
                # Métricas
                hoje = pd.to_datetime(datetime.now().date())
                df_meus_ativos = df_meus_projetos_unicos[df_meus_projetos_unicos['Status'].isin(['Iniciado', 'Pendente'])]
                df_meus_concluidos = df_meus_projetos_unicos[df_meus_projetos_unicos['Status'] == 'Concluído']
                df_meus_atrasados = df_meus_ativos[df_meus_ativos['Previsao_Conclusao'] < hoje]

                col1_m, col2_m, col3_m = st.columns(3)
                col1_m.metric("Meus Projetos Ativos", len(df_meus_ativos))
                col2_m.metric("Meus Projetos Concluídos", len(df_meus_concluidos))
                col3_m.metric("Meus Projetos Atrasados", len(df_meus_atrasados))

                # Gráfico de Pizza Pessoal
                df_status_counts = df_meus_projetos_unicos['Status'].value_counts().reset_index()
                df_status_counts.columns = ['Status', 'Contagem']
                mapa_cores_status = {
                    'Concluído': '#76B82A', 'Iniciado': '#30515F', 'Pendente': '#B2B2B2'
                }
                fig_pie_meus_status = px.pie(df_status_counts, names='Status', values='Contagem', 
                                             title="Status dos Meus Projetos",
                                             color='Status',
                                             color_discrete_map=mapa_cores_status)
                st.plotly_chart(fig_pie_meus_status, use_container_width=True)

            else:
                st.info("Assim que você registrar seu primeiro projeto, seus indicadores aparecerão aqui.")
            
            st.divider()

            # --- 4. TRILHA DE DESENVOLVIMENTO (MOVIDA PARA CÁ) ---
            st.subheader("4. Minha Trilha de Desenvolvimento")
            
            coluna_admissao = "ADMISSAO" 
            coluna_termino = "TERMINO CONTRATO" # <--- NOVA COLUNA
            
            if coluna_admissao not in base.columns or coluna_termino not in base.columns:
                st.error(f"Erro: As colunas '{coluna_admissao}' ou '{coluna_termino}' não foram encontradas no arquivo 'Base.xlsx'.")
            else:
                try:
                    data_admissao_str = estagiario[coluna_admissao].values[0]
                    # --- CORREÇÃO AQUI: Forçar formato BR ---
                    data_admissao = pd.to_datetime(data_admissao_str, errors='coerce', format='%d/%m/%Y') 
                    
                    data_termino_str = estagiario[coluna_termino].values[0]
                    # --- CORREÇÃO AQUI: Forçar formato BR ---
                    data_termino = pd.to_datetime(data_termino_str, errors='coerce', format='%d/%m/%Y') 

                    if pd.isna(data_admissao) or pd.isna(data_termino):
                        st.error("Sua data de admissão ou término não foi encontrada ou está em formato incorreto.")
                    else:
                        # --- NOVO BLOCO DE MÉTRICAS DE CONTRATO ---
                        hoje_dt = datetime.now()
                        dias_para_termino = (data_termino - hoje_dt).days
                        
                        col1_data, col2_data, col3_data = st.columns(3)
                        col1_data.metric("Data de Início", data_admissao.strftime('%d/%m/%Y'))
                        col2_data.metric("Data de Término", data_termino.strftime('%d/%m/%Y'))
                        if dias_para_termino > 0:
                            col3_data.metric("Dias Restantes de Contrato", f"{dias_para_termino} dias")
                        else:
                            col3_data.metric("Contrato Encerrado", "🏁")
                        
                        progresso = df_trilha[df_trilha['Matricula'] == matricula]
                        
                        if progresso.empty:
                            st.warning("Seu progresso na trilha ainda não foi iniciado pelo RH.")
                        else:
                            progresso = progresso.iloc[0] 
                            
                            meses_completos = progresso[['Mes_1', 'Mes_2', 'Mes_3', 'Mes_4', 'Mes_5', 'Mes_6']].sum()
                            percentual_completo = int((meses_completos / 6) * 100)
                            
                            if percentual_completo == 100:
                                st.progress(percentual_completo, text="Trilha Concluída! 🎉")
                            else:
                                st.progress(percentual_completo, text=f"{percentual_completo}% Concluído")

                            st.markdown("---")
                            
                            etapa_atual_encontrada = False
                            
                            for i in range(1, 7):
                                mes_key = f"Mes_{i}"
                                mes_descricao = TRILHA_MESES[mes_key]
                                mes_concluido = progresso[mes_key]
                                data_limite = data_admissao + relativedelta(months=i)
                                
                                if mes_concluido:
                                    st.success(f"**{mes_descricao}** (Concluído!)", icon="✅")
                                else:
                                    if not etapa_atual_encontrada:
                                        if hoje_dt > data_limite:
                                            st.error(f"🚨 **{mes_descricao}** (Prazo: {data_limite.strftime('%d/%m/%Y')} - PENDENTE)", icon="🚨")
                                        else:
                                            st.info(f"⏳ **{mes_descricao}** (Prazo: {data_limite.strftime('%d/%m/%Y')} - ETAPA ATUAL)", icon="⏳")
                                        etapa_atual_encontrada = True
                                    else:
                                        st.caption(f"🔘 {mes_descricao} (Prazo: {data_limite.strftime('%d/%m/%Y')})")
                            
                except Exception as e:
                    st.error(f"Ocorreu um erro ao calcular sua trilha: {e}")

            st.divider()

            # --- 5. MEUS FEEDBACKS RECEBIDOS (NOVO) ---
            st.subheader("5. Meus Feedbacks Recebidos")
            
            if os.path.exists(CSV_FEEDBACK):
                df_meus_feedbacks = pd.read_csv(CSV_FEEDBACK)
                df_meus_feedbacks = df_meus_feedbacks[df_meus_feedbacks['Estagiario'] == nome]
            else:
                df_meus_feedbacks = pd.DataFrame()

            if df_meus_feedbacks.empty:
                st.info("Você ainda não recebeu nenhum feedback oficial do seu gestor.")
            else:
                st.write("Aqui estão os feedbacks que você recebeu (do mais recente para o mais antigo):")
                df_meus_feedbacks['Data_Hora'] = pd.to_datetime(df_meus_feedbacks['Data_Hora'])
                df_meus_feedbacks = df_meus_feedbacks.sort_values(by="Data_Hora", ascending=False)
                
                for idx, row in df_meus_feedbacks.iterrows():
                    with st.container(border=True):
                        st.write(f"**Feedback de:** {row['Gestor']} em {row['Data_Hora'].strftime('%d/%m/%Y')}")
                        
                        cols_fb_existentes = ['Iniciativa', 'Aprendizagem', 'Qualidade', 'Relacoes']
                        if all(col in row for col in cols_fb_existentes):
                            st.markdown(f"""
                            * **Iniciativa:** {row['Iniciativa']}
                            * **Aprendizagem:** {row['Aprendizagem']}
                            * **Qualidade:** {row['Qualidade']}
                            * **Relações:** {row['Relacoes']}
                            """)
                        
                        if pd.notna(row['Feedback_Livre']) and row['Feedback_Livre'].strip():
                            st.write("**Feedback Adicional:**")
                            st.info(f"{row['Feedback_Livre']}")

        else:
            st.error("⚠️ Matrícula não encontrada na base. Verifique e tente novamente.")
    elif confirmar and not matricula:
        st.warning("Por favor, digite uma matrícula antes de confirmar.")

# ========= NOVA PÁGINA: AVALIAÇÃO DO GESTOR =========
elif st.session_state.pagina_selecionada == "Avaliação do Gestor":
    
    st.button("🏠 Voltar para Home", on_click=mudar_pagina, args=("Home",))
    
    st.title("💬 Avaliação do Gestor")
    st.markdown("---")
    
    if "gestor_autenticado" not in st.session_state:
        st.session_state.gestor_autenticado = False
    if "dados_gestor" not in st.session_state:
        st.session_state.dados_gestor = None

    if not st.session_state.gestor_autenticado:
        st.subheader("🔐 Acesso Restrito ao Gestor")
        
        # --- ATUALIZADO: Login com st.form ---
        with st.form(key="gestor_login_avaliacao_form"):
            matricula = st.text_input("Digite sua matrícula:")
            senha = st.text_input("Digite a senha:", type="password")
            entrar = st.form_submit_button("Entrar")

        if entrar:
            try:
                base_gestor = pd.read_excel(GESTOR_FILE)
            except Exception as e:
                st.error(f"Erro ao carregar planilha de gestores: {e}")
                base_gestor = pd.DataFrame(columns=["MATRICULA", "COLABORADOR"])

            if matricula and senha == SENHA_GESTOR:
                gestor = base_gestor.loc[base_gestor["MATRICULA"].astype(str) == str(matricula)]
                if not gestor.empty:
                    st.session_state.gestor_autenticado = True
                    st.session_state.dados_gestor = gestor.iloc[0]
                    st.success(f"✅ Bem-vindo, {gestor.iloc[0]['COLABORADOR']}!")
                    st.rerun()
                else:
                    st.error("❌ Matrícula não encontrada.")
            else:
                st.error("❌ Matrícula ou senha incorreta.")

    if st.session_state.gestor_autenticado:
        gestor = st.session_state.dados_gestor
        unidade_gestor = gestor.get('UNIDADE', '') 
        st.markdown(f"👤 **Gestor:** {gestor.get('COLABORADOR', '')} **({unidade_gestor})**")
        st.divider()

        try:
            base_estagiarios = pd.read_excel(BASE_FILE)
            estagiarios = sorted(base_estagiarios["COLABORADOR"].dropna().unique().tolist())
        except Exception as e:
            st.warning(f"Não foi possível carregar base de estagiários: {e}")
            estagiarios = []

        with st.form("form_feedback"):
            st.subheader("Selecione o estagiário avaliado:")
            estagiario_fb = st.selectbox("Estagiário:", estagiarios, key="fb_estagiario")

            st.markdown("### 1️⃣ Iniciativa e Proatividade")
            iniciativa = st.radio(
                "O estagiário demonstra iniciativa para buscar tarefas, sugerir melhorias e resolver problemas de forma autônoma?",
                ["Excelente", "Bom", "Regular", "Ruim"],
                horizontal=True, key="fb_1")
            st.markdown("### 2️⃣ Capacidade de Aprendizagem e Adaptação")
            aprendizagem = st.radio(
                "Com que rapidez o estagiário absorve novos conhecimentos e se adapta a mudanças na rotina?",
                ["Excelente", "Bom", "Regular", "Ruim"],
                horizontal=True, key="fb_2")
            st.markdown("### 3️⃣ Qualidade e Entrega das Atividades")
            qualidade = st.radio(
                "Qual o nível de precisão, atenção aos detalhes e cumprimento dos prazos nas tarefas atribuídas?",
                ["Excelente", "Bom", "Regular", "Ruim"],
                horizontal=True, key="fb_3")
            st.markdown("### 4️⃣ Relações Interpessoais e Feedback")
            relacoes = st.radio(
                "O estagiário se comunica de forma clara, trabalha bem em equipe e aplica feedbacks recebidos?",
                ["Excelente", "Bom", "Regular", "Ruim"],
                horizontal=True, key="fb_4")
            st.markdown("### 5️⃣ Registre seu feedback sobre o estagiário:")
            sugestao = st.text_area("Escreva aqui o feedback livre:", key="fb_sugestao")
            enviar = st.form_submit_button("💾 Enviar Feedback")

            if enviar:
                if not estagiario_fb:
                    st.warning("Por favor, selecione um estagiário.")
                else:
                    if not os.path.exists(CSV_FEEDBACK):
                        with open(CSV_FEEDBACK, 'w', newline='', encoding='utf-8') as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                'Data_Hora', 'Gestor', 'Estagiario',
                                'Iniciativa', 'Aprendizagem', 'Qualidade',
                                'Relacoes', 'Feedback_Livre'
                            ])
                    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    with open(CSV_FEEDBACK, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            data_hora,
                            gestor.get('COLABORADOR',''),
                            estagiario_fb,
                            iniciativa,
                            aprendizagem,
                            qualidade,
                            relacoes,
                            sugestao
                        ])
                    st.success("✅ Feedback registrado com sucesso!")


# ========= NOVA PÁGINA: TREINAMENTOS =========
elif st.session_state.pagina_selecionada == "Treinamentos":
    
    st.button("🏠 Voltar para Home", on_click=mudar_pagina, args=("Home",))
    st.title("🗓️ Agenda de Treinamentos")
    st.markdown("---")

    if df_treinamentos.empty:
        st.info("Nenhum treinamento cadastrado no momento.")
    else:
        # Filtrar apenas treinamentos futuros
        hoje = datetime.now().date()
        # Corrigir filtro para datas (precisa converter a coluna 'Data' para date)
        df_treinamentos_futuros = df_treinamentos[df_treinamentos['Data'].dt.date >= hoje].copy()
        
        if df_treinamentos_futuros.empty:
            st.info("Nenhum treinamento futuro agendado no momento.")
        else:
            # Ordenar por data
            df_treinamentos_futuros.sort_values(by='Data', ascending=True, inplace=True)
            
            st.subheader("Próximos Eventos:")
            
            # Agrupar por data para um visual de agenda
            datas_unicas = df_treinamentos_futuros['Data'].dt.date.unique()
            
            for data in datas_unicas:
                # Mostrar a data como um cabeçalho
                st.markdown(f"### {data.strftime('%d/%m/%Y')}")
                treinamentos_do_dia = df_treinamentos_futuros[df_treinamentos_futuros['Data'].dt.date == data]
                
                # Criar colunas para os cartões
                cols = st.columns(3) 
                col_idx = 0
                
                for idx, row in treinamentos_do_dia.iterrows():
                    with cols[col_idx % 3]: # Loop de 0 a 2
                        with st.container(border=True):
                            st.subheader(f"📍 {row['Nome_Treinamento']}")
                            
                            # Usar st.caption para texto menor e ícones
                            st.caption(f"**⏰ Horário:** {row['Inicio'].strftime('%H:%M')} - {row['Termino'].strftime('%H:%M')}")
                            st.caption(f"**🏢 Unidade:** {row['Unidade']}")
                            st.caption(f"**💻 Modalidade:** {row['Modalidade']}")
                            
                            if row['Modalidade'] == "Presencial":
                                st.caption(f"**📍 Local:** {row['Local_Link']}")
                            else:
                                # Se for Online, tenta criar um link clicável
                                if str(row['Local_Link']).startswith('http'):
                                    st.link_button("Acessar Link do Treinamento", row['Local_Link'])
                                else:
                                    st.caption(f"**🔗 Link:** {row['Local_Link']}")
                    col_idx += 1
                st.markdown("---") # Divisor entre os dias


# ========= ADMIN (ATUALIZADO COM GESTÃO DE TRILHA) =========
elif st.session_state.pagina_selecionada == "Administração":
    
    st.button("🏠 Voltar para Home", on_click=mudar_pagina, args=("Home",))
    
    st.title("🔒 Administração de Dados")
    st.markdown("---")
    
    # --- ATUALIZADO: Login com st.form ---
    if "admin_autenticado" not in st.session_state:
        st.session_state.admin_autenticado = False
    
    if not st.session_state.admin_autenticado:
        with st.form(key="admin_login_form"):
            password_input = st.text_input("Digite a senha de administrador:", type="password")
            admin_entrar = st.form_submit_button("Entrar")
        
        if admin_entrar:
            if password_input == ACCESS_PASSWORD:
                st.session_state.admin_autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta. Acesso Negado.")
    
    if st.session_state.admin_autenticado:
        st.success("Acesso Concedido!")

        # --- SEÇÃO DE GESTÃO DE TREINAMENTOS (ATUALIZADA) ---
        st.markdown("## 🗓️ Gestão de Treinamentos")
        with st.expander("Cadastrar Novo Treinamento"):
            with st.form("form_novo_treinamento"):
                st.subheader("Preencha os dados do treinamento:")
                col1, col2 = st.columns(2)
                with col1:
                    nome_treinamento = st.text_input("Nome do Treinamento")
                    # CORRIGIDO: Adicionado format="DD/MM/YYYY"
                    data_treinamento = st.date_input("Data do Treinamento", datetime.now(), format="DD/MM/YYYY")
                    modalidade = st.selectbox("Modalidade", ["Presencial", "Online"])
                with col2:
                    # ATUALIZADO: Adicionado campo Unidade
                    unidade_treinamento = st.selectbox("Unidade", ["Narandiba", "Paraguaçu Paulista"])
                    local_link = st.text_input("Local (para Presencial) ou Link (para Online)")
                    hora_inicio = st.time_input("Horário de Início", time(9, 0))
                    hora_termino = st.time_input("Horário de Término", time(10, 0))
                
                enviar_treinamento = st.form_submit_button("💾 Salvar Treinamento")
                
                if enviar_treinamento:
                    if not nome_treinamento:
                        st.warning("Por favor, preencha o Nome do Treinamento.")
                    else:
                        nova_linha_treinamento = pd.DataFrame([{
                            'Nome_Treinamento': nome_treinamento,
                            'Data': data_treinamento.strftime('%d/%m/%Y'),
                            'Inicio': hora_inicio.strftime('%H:%M:%S'),
                            'Termino': hora_termino.strftime('%H:%M:%S'),
                            'Modalidade': modalidade,
                            'Local_Link': local_link,
                            'Unidade': unidade_treinamento # Salvar novo campo
                        }])
                        nova_linha_treinamento.to_csv(TREINAMENTOS_FILE, mode='a', header=False, index=False, encoding='utf-8')
                        st.success(f"✅ Treinamento '{nome_treinamento}' salvo!")
                        st.rerun()

        st.info("Aqui você pode editar ou apagar treinamentos já cadastrados.")
        
        # Corrigir o carregamento das datas para o editor
        df_treinamentos_admin = initialize_treinamentos() 
        df_treinamentos_admin['Deletar'] = False
        # ATUALIZADO: Adicionar 'Unidade' ao editor
        cols_treinamentos = ['Deletar'] + COLUNAS_TREINAMENTOS
        df_treinamentos_admin = df_treinamentos_admin[cols_treinamentos]

        edited_df_treinamentos = st.data_editor(
            df_treinamentos_admin,
            key="edit_treinamentos_df",
            use_container_width=True,
            column_config={
                "Deletar": st.column_config.CheckboxColumn("Deletar?"),
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Inicio": st.column_config.TimeColumn("Início", format="HH:mm"),
                "Termino": st.column_config.TimeColumn("Término", format="HH:mm"),
                "Modalidade": st.column_config.SelectboxColumn("Modalidade", options=["Presencial", "Online"]),
                "Local_Link": st.column_config.TextColumn("Local / Link"),
                # ATUALIZADO: Adicionada config da coluna Unidade
                "Unidade": st.column_config.SelectboxColumn("Unidade", options=["Narandiba", "Paraguaçu Paulista"], required=True)
            },
            num_rows="dynamic"
        )
        
        if st.button("Salvar Alterações nos Treinamentos"):
            df_para_salvar_trein = edited_df_treinamentos[edited_df_treinamentos['Deletar'] == False].copy()
            df_para_salvar_trein.drop(columns=['Deletar'], inplace=True)
            
            try:
                # Converter datas e horas de volta para string antes de salvar
                for col in DATE_COLS_TREINAMENTOS:
                    df_para_salvar_trein[col] = pd.to_datetime(df_para_salvar_trein[col]).dt.strftime('%d/%m/%Y').replace('NaT', '')
                for col in TIME_COLS_TREINAMENTOS:
                    # Garantir que é um objeto time antes de formatar
                    df_para_salvar_trein[col] = df_para_salvar_trein[col].apply(lambda x: x.strftime('%H:%M:%S') if isinstance(x, time) else (pd.to_datetime(x).strftime('%H:%M:%S') if pd.notna(x) else ''))

                df_para_salvar_trein.to_csv(TREINAMENTOS_FILE, index=False, encoding='utf-8')
                st.success("✅ Treinamentos atualizados com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar treinamentos: {e}")

        st.markdown("---") # Divisor

        # --- SEÇÃO DE GESTÃO DA TRILHA ---
        st.markdown("## 🧭 Gestão da Trilha de Desenvolvimento")
        
        # --- AÇÕES EM LOTE ---
        st.subheader("Ações em Lote")
        st.markdown("Use esta seção para marcar ou desmarcar uma etapa para **todos** os estagiários de uma vez.")
        
        trilha_mapa_reverso = {v: k for k, v in TRILHA_MESES.items()}
        
        col1, col2, col3 = st.columns([2, 1, 1]) # ATUALIZADO PARA 3 COLUNAS
        
        with col1:
            mes_selecionado = st.selectbox("Selecione a etapa para a ação em lote:", options=TRILHA_MESES.values())
        
        def marcar_lote_csv():
            try:
                mes_key = trilha_mapa_reverso[mes_selecionado] 
                df_trilha_lote = initialize_trilha()
                df_trilha_lote[mes_key] = True # Set to TRUE
                df_trilha_lote.to_csv(TRILHA_FILE, index=False, encoding='utf-8')
                st.success(f"Etapa '{mes_selecionado}' marcada como CONCLUÍDA para todos!")
            except Exception as e:
                st.error(f"Erro ao salvar ação em lote: {e}")
        
        # --- NOVA FUNÇÃO "DESMARCAR TODOS" ---
        def desmarcar_lote_csv():
            try:
                mes_key = trilha_mapa_reverso[mes_selecionado] 
                df_trilha_lote = initialize_trilha()
                df_trilha_lote[mes_key] = False # Set to FALSE
                df_trilha_lote.to_csv(TRILHA_FILE, index=False, encoding='utf-8')
                st.success(f"Etapa '{mes_selecionado}' marcada como PENDENTE para todos!")
            except Exception as e:
                st.error(f"Erro ao salvar ação em lote: {e}")
            
        with col2:
            st.button("Marcar Todos (Concluído)", on_click=marcar_lote_csv, use_container_width=True, type="primary")
            
        with col3:
            st.button("Desmarcar Todos (Pendente)", on_click=desmarcar_lote_csv, use_container_width=True, type="secondary") # NOVO BOTÃO
        
        st.divider()
        # --- FIM AÇÕES EM LOTE ---
        
        
        st.info("Aqui você pode marcar as etapas concluídas individualmente.")
        
        try:
            base_df_admin = pd.read_excel(BASE_FILE, dtype={'MATRICULA': str})
            base_df_admin = base_df_admin[['MATRICULA', 'COLABORADOR']]
            
            df_trilha_admin = initialize_trilha()
            
            df_trilha_display = pd.merge(base_df_admin, df_trilha_admin, 
                                         left_on='MATRICULA', right_on='Matricula', 
                                         how='left')
            
            df_trilha_display['Matricula'] = df_trilha_display['MATRICULA']
            df_trilha_display[COLUNAS_TRILHA] = df_trilha_display[COLUNAS_TRILHA].fillna(False)

            edited_df_trilha = st.data_editor(
                df_trilha_display,
                key="edit_trilha_df",
                use_container_width=True,
                disabled=['MATRICULA', 'COLABORADOR', 'Matricula'],
                column_config={
                    "COLABORADOR": "Estagiário",
                    "Mes_1": st.column_config.CheckboxColumn(TRILHA_MESES['Mes_1']),
                    "Mes_2": st.column_config.CheckboxColumn(TRILHA_MESES['Mes_2']),
                    "Mes_3": st.column_config.CheckboxColumn(TRILHA_MESES['Mes_3']),
                    "Mes_4": st.column_config.CheckboxColumn(TRILHA_MESES['Mes_4']),
                    "Mes_5": st.column_config.CheckboxColumn(TRILHA_MESES['Mes_5']),
                    "Mes_6": st.column_config.CheckboxColumn(TRILHA_MESES['Mes_6']),
                    "MATRICULA": None, # Esconder
                    "Matricula": None  # Esconder
                }
            )

            if st.button("Salvar Progresso das Trilhas"):
                df_para_salvar_trilha = edited_df_trilha[COLUNAS_TRILHA]
                df_para_salvar_trilha.to_csv(TRILHA_FILE, index=False, encoding='utf-8')
                st.success("✅ Progresso das trilhas foi salvo!")
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao carregar o editor de trilhas: {e}")
        
        st.markdown("---") # Divisor

        # --- SEÇÃO DE EDIÇÃO DE FEEDBACKS ---
        st.markdown("## ✏️ Editar / Apagar Feedbacks dos Gestores")
        st.info(f"Aqui você pode editar ou apagar linhas do arquivo '{CSV_FEEDBACK}'.")

        if os.path.exists(CSV_FEEDBACK):
            try:
                df_feed = pd.read_csv(CSV_FEEDBACK)
                df_feed = df_feed.reset_index(drop=True)
                df_feed['Deletar'] = False
                cols = ['Deletar'] + [col for col in df_feed.columns if col != 'Deletar']
                df_feed = df_feed[cols]

                edited_df_feed = st.data_editor(
                    df_feed,
                    key="edit_feedback_df",
                    use_container_width=True,
                    disabled=['Data_Hora', 'Gestor', 'Estagiario'],
                    column_config={"Deletar": st.column_config.CheckboxColumn("Deletar?",default=False)},
                    num_rows="dynamic"
                )

                if st.button("Salvar Feedbacks e Apagar Selecionados"):
                    df_para_salvar_feed = edited_df_feed[edited_df_feed['Deletar'] == False].copy()
                    df_para_salvar_feed.drop(columns=['Deletar'], inplace=True)
                    
                    try:
                        df_para_salvar_feed.to_csv(CSV_FEEDBACK, index=False, encoding='utf-8')
                        st.success("✅ Feedbacks atualizados com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar o arquivo de feedbacks: {e}")
            
            except Exception as e:
                st.error(f"Erro ao carregar o editor de feedbacks: {e}")
        else:
            st.warning(f"O arquivo {CSV_FEEDBACK} ainda não existe. Nenhum feedback para editar.")

        
        # --- SEÇÃO: EDIÇÃO DE ATIVIDADES ---
        st.markdown("---")
        st.markdown("## ✏️ Editar / Apagar Atividades dos Estagiários")
        st.info(f"Aqui você pode editar ou apagar linhas do arquivo de atividades '{CSV_FILE}'.")

        # df_data já foi carregado e datas convertidas
        if not df_data.empty:
            try:
                df_atividades = df_data.copy() # Usar uma cópia
                df_atividades = df_atividades.reset_index(drop=True) 
                
                df_atividades['Deletar'] = False
                cols = ['Deletar'] + [col for col in df_atividades.columns if col != 'Deletar']
                df_atividades = df_atividades[cols]

                edited_df_atividades = st.data_editor(
                    df_atividades,
                    key="edit_atividades_df",
                    use_container_width=True,
                    column_config={
                        "Deletar": st.column_config.CheckboxColumn("Deletar?", default=False),
                        "Data_Registro": st.column_config.DateColumn("Registro", format="DD/MM/YYYY", disabled=True),
                        "Colaborador": st.column_config.Column(disabled=True),
                        "Setor": st.column_config.Column(disabled=True),
                        "Data_Inicio_Projeto": st.column_config.DateColumn("Início", format="DD/MM/YYYY"),
                        "Previsao_Conclusao": st.column_config.DateColumn("Previsão", format="DD/MM/YYYY"),
                        "Percentual_Concluido": st.column_config.NumberColumn("%", format="%d%%"), 
                        "Status": st.column_config.SelectboxColumn("Status", options=["Iniciado", "Pendente", "Concluído"]) 
                    },
                    num_rows="dynamic" 
                )

                if st.button("Salvar Atividades e Apagar Selecionadas"):
                    df_para_salvar_ativ = edited_df_atividades[edited_df_atividades['Deletar'] == False].copy()
                    df_para_salvar_ativ.drop(columns=['Deletar'], inplace=True)
                    
                    try:
                        def map_status_to_percent(status):
                            if status == "Iniciado": return 0
                            elif status == "Pendente": return 50
                            elif status == "Concluído": return 100
                            return 0
                        df_para_salvar_ativ['Percentual_Concluido'] = df_para_salvar_ativ['Status'].apply(map_status_to_percent)
                        
                        for col in DATE_COLS_REGISTROS:
                            df_para_salvar_ativ[col] = df_para_salvar_ativ[col].dt.strftime('%d/%m/%Y').replace('NaT', '')
                        
                        df_para_salvar_ativ.to_csv(CSV_FILE, index=False, encoding='utf-8')
                        st.success("✅ Registros de atividades atualizados com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar o arquivo de atividades: {e}")
            
            except Exception as e:
                st.error(f"Erro ao carregar o editor de atividades: {e}")
        else:
            st.warning(f"O arquivo '{CSV_FILE}' (atividades) está vazio. Nenhum registro para editar.")


        # --- SEÇÃO DE APAGAR TUDO (ZONA DE PERIGO) ---
        st.markdown("---")
        st.markdown("## 🗑️ Zona de Perigo - Apagar *Todos* os Registros")
        st.warning("⚠️ Esta ação não pode ser desfeita e apaga *todos* os registros de atividades de uma vez.")
        
        st.button("APAGAR TODOS OS REGISTROS DE ATIVIDADES", 
                  on_click=delete_all_data, 
                  type="primary", 
                  use_container_width=True,
                  key="delete_all_atividades_btn")
    
    elif password_input:
        st.error("Senha incorreta. Acesso Negado.")