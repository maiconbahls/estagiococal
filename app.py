import streamlit as st
import pandas as pd
import plotly.express as px  # Necessário para os gráficos do Dashboard
import base64
import os
# from streamlit_user_agent import get_user_agent # <--- REMOVIDO
from datetime import datetime
import csv

# --- 1. CONFIGURAÇÃO INICIAL ---
st.set_page_config(layout="wide")

# Inicializar session_state
if 'pagina_selecionada' not in st.session_state:
    st.session_state.pagina_selecionada = "Home"
if 'registration_count' not in st.session_state:
    st.session_state.registration_count = 0

CSV_FILE = "registros.csv"
BASE_FILE = "Base.xlsx" # Corrigido para "B" maiúsculo
GESTOR_FILE = "gestor.xlsx"
CSV_FEEDBACK = "feedback_gestor_programa.csv"

# --- SENHAS CARREGADAS COM SEGURANÇA ---
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


# --- 2. FUNÇÕES DE APOIO (ATUALIZADAS) ---

# Colunas que o CSV deve ter
COLUNAS_REGISTROS = [
    'Data_Registro', 'Colaborador', 'Setor', 
    'Categoria_Atividade', 'Nome_Projeto', 'Data_Inicio_Projeto', 'Previsao_Conclusao',
    'Status', 'Percentual_Concluido', 'Observacoes'
]
DATE_COLS_REGISTROS = ['Data_Registro', 'Data_Inicio_Projeto', 'Previsao_Conclusao']

# ATUALIZADO: Converte datas ao ler o CSV
def initialize_data():
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
            
            # --- CORREÇÃO DO ERRO DE DATA ---
            # Converte colunas de data (que são strings 'dd/mm/YYYY') para datetime
            for col in DATE_COLS_REGISTROS:
                df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
            
            return df
        except Exception as e:
            st.error(f"Erro ao ler {CSV_FILE}: {e}. Pode ser necessário apagá-lo na área de Administração.")
            return pd.DataFrame(columns=COLUNAS_REGISTROS)

def mudar_pagina(nova_pagina):
    st.session_state.pagina_selecionada = nova_pagina

def delete_all_data():
    if os.path.exists(CSV_FILE):
        df_empty = pd.DataFrame(columns=COLUNAS_REGISTROS)
        df_empty.to_csv(CSV_FILE, index=False, encoding='utf-8')
        st.success("✅ Todos os registros de ATIVIDADES foram apagados com sucesso!")
    else:
        st.warning("O arquivo de registros de atividades não existe.")
    st.rerun()

# --- Funções de Apoio (CRUD) ---
def get_base64_of_bin_file(bin_file):
    file_path = os.path.abspath(bin_file)
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

def get_home_page_css(file_path):
    try:
        ext = os.path.splitext(file_path)[1][1:]
    except:
        ext = "png"
    bin_str = get_base64_of_bin_file(file_path)
    if not bin_str:
        return ""
    # CSS (sem alterações)
    return f'''
    <style>
        [data-testid="stSidebar"] {{
            display: none;
        }}
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/{ext};base64,{bin_str}");
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
    </style>
    '''

# --- 3. EXECUÇÃO DE CSS/FUNDO E BARRA LATERAL (MUDANÇA AQUI) ---
# Lógica de detecção de mobile foi REMOVIDA
is_mobile = False # <--- MUDANÇA AQUI: Sempre será False

st.sidebar.title("Menu")
st.sidebar.radio(
    "Selecione a funcionalidade:",
    ("Home", "Dashboard", "Registro de Atividade", "Registro de Feedback", "Administração"),
    key="pagina_selecionada"
)
st.sidebar.divider()

if st.session_state.pagina_selecionada != "Home":
    st.sidebar.title("Filtros")
    data_inicio = st.sidebar.date_input("Data Início", datetime.now().date().replace(day=1), format="DD/MM/YYYY")
    data_fim = st.sidebar.date_input("Data Fim", format="DD/MM/YYYY")
    
    try:
        base_tmp = pd.read_excel(BASE_FILE)
        lista_estagiarios = sorted(base_tmp["COLABORADOR"].dropna().unique().tolist())
        lista_estagiarios.insert(0, "Todos")
        filtro_estagiario_sidebar = st.sidebar.selectbox("Estagiário", lista_estagiarios)
    except Exception:
        st.sidebar.warning("Não foi possível carregar lista de estagiários (base.xlsx).")
        filtro_estagiario_sidebar = "Todos"


# --- 4. PÁGINAS ---
df_data = initialize_data()

# ========= HOME =========
if st.session_state.pagina_selecionada == "Home":
    # (Código da Home com botões "Trilha de Desenvolvimento" e "Treinamentos")
    try:
        # --- MUDANÇA AQUI: Sempre usa "fundo.jpg" ---
        css = get_home_page_css("fundo.jpg") 
        if css:
            st.markdown(css, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o fundo: {e}")

    # --- MUDANÇA AQUI: Lógica de mobile removida ---
    # Sempre mostra o layout de desktop
    st.markdown("<br>" * 15, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📋 Registro de Atividade", use_container_width=True, on_click=mudar_pagina, args=("Registro de Atividade",))
        st.button("Trilha de Desenvolvimento", use_container_width=True) 
    with col2:
        st.button("💬 Registro de Feedback", use_container_width=True, on_click=mudar_pagina, args=("Registro de Feedback",))
        st.button("Treinamentos", use_container_width=True)
    with col3:
        st.button("📊 Dashboard", use_container_width=True, on_click=mudar_pagina, args=("Dashboard",))
        st.button("🔒 Administração", use_container_width=True, on_click=mudar_pagina, args=("Administração",))


# ========= DASHBOARD (ATUALIZADO COM RANKING E CORES) =========
elif st.session_state.pagina_selecionada == "Dashboard":
    
    st.title("📊 Relatórios de Feedback dos Gestores")
    st.divider()

    # --- 1. SEÇÃO DE FEEDBACKS ---
    if os.path.exists(CSV_FEEDBACK):
        df_feedback = pd.read_csv(CSV_FEEDBACK)
    else:
        df_feedback = pd.DataFrame() # Cria um dataframe vazio se o arquivo não existir

    cols_competencias = [] # Inicializa a lista de competências
    
    if not df_feedback.empty:
        df_display_feedback = df_feedback.copy()
        colunas_para_renomear = {'Data_Hora': 'DATA', 'Gestor': 'GESTOR'}
        df_display_feedback.rename(columns=colunas_para_renomear, inplace=True)

        if filtro_estagiario_sidebar != "Todos" and "Estagiario" in df_display_feedback.columns:
            df_display_feedback = df_display_feedback[df_display_feedback["Estagiario"] == filtro_estagiario_sidebar]
            # Também filtrar o df_feedback original para os gráficos
            df_feedback = df_feedback[df_feedback["Estagiario"] == filtro_estagiario_sidebar]

        # Ocultar coluna de feedback livre
        colunas_para_ocultar = ['Feedback_Livre', 'sugestao_melhoria']
        for col in colunas_para_ocultar:
            if col in df_display_feedback.columns:
                df_display_feedback = df_display_feedback.drop(columns=[col])
        
        st.subheader("Tabela de Feedbacks Recebidos")
        st.dataframe(df_display_feedback, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Análise Gráfica")
        
        # --- COLUNA 1: GRÁFICO DE PIZZA DE FEEDBACK (CORRIGIDO) ---
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Análise de Feedbacks (Gestores)**")
            
            # --- CORREÇÃO: Lógica de Coluna Dinâmica ---
            # Ele vai pegar QUALQUER coluna que não seja as de ID
            colunas_excluir = ['DATA', 'GESTOR', 'Data_Hora', 'Gestor', 'Estagiario', 'Feedback_Livre', 'sugestao_melhoria']
            cols_competencias = [col for col in df_feedback.columns if col not in colunas_excluir]
            
            if not cols_competencias or df_feedback.empty:
                st.warning("Nenhum dado de competência (Ex: 'Iniciativa' ou 'estrutura_suporte') foi encontrado no feedback.")
                df_grafico = pd.DataFrame() # Criar df_grafico vazio para o ranking
            else:
                mapa_notas = {"Excelente": 4, "Bom": 3, "Regular": 2, "Ruim": 1, None: 0}
                mapa_cores = {
                     'Excelente': '#76B82A', # Verde
                     'Bom': '#30515F',      # Azul Escuro
                     'Regular': '#B2B2B2',  # Cinza
                     'Ruim': '#B2B2B2'      # Cinza
                }
                
                df_grafico = df_feedback.copy()
                df_pizza_data = []
                for col in cols_competencias:
                    # Adicionar cálculo de nota para o ranking (se a coluna for uma das novas)
                    if col in ['Iniciativa', 'Aprendizagem', 'Qualidade', 'Relacoes']:
                        df_grafico[f'Nota_{col}'] = df_grafico[col].map(mapa_notas).fillna(0)
                    
                    # Adicionar contagem para o gráfico de pizza
                    contagem = df_grafico[col].value_counts().reset_index()
                    contagem.columns = ['Avaliação', 'Contagem']
                    df_pizza_data.append(contagem)

                if df_pizza_data:
                    df_pizza_total = pd.concat(df_pizza_data).groupby('Avaliação').sum().reset_index()
                    
                    fig_pie = px.pie(df_pizza_total, names='Avaliação', values='Contagem', 
                                     title="Distribuição Geral das Avaliações",
                                     color='Avaliação', # Força o uso da coluna
                                     color_discrete_map=mapa_cores) # E força o mapa de cores
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Sem dados para o gráfico de pizza de feedback.")
        
        # --- COLUNA 2: NOVO GRÁFICO DE STATUS DE PROJETOS ---
        with col2:
            st.markdown("**Status dos Projetos (Estagiários)**")
            
            if not df_data.empty:
                # Pegar o último status de cada projeto
                df_projetos_unicos = df_data.sort_values(by='Data_Registro', ascending=True).drop_duplicates(subset=['Colaborador', 'Nome_Projeto'], keep='last')
                
                # Filtrar pelo estagiário selecionado na sidebar
                if filtro_estagiario_sidebar != "Todos":
                    df_projetos_unicos = df_projetos_unicos[df_projetos_unicos['Colaborador'] == filtro_estagiario_sidebar]
                
                df_status_counts = df_projetos_unicos['Status'].value_counts().reset_index()
                df_status_counts.columns = ['Status', 'Contagem']

                mapa_cores_status = {
                    'Concluído': '#76B82A', # Verde (Cocal)
                    'Iniciado': '#30515F',  # Azul Escuro (Cocal)
                    'Pendente': '#B2B2B2'   # Cinza (Cocal)
                }

                fig_pie_status = px.pie(df_status_counts, names='Status', values='Contagem', 
                                         title="Distribuição Geral de Status de Projetos",
                                         color='Status',
                                         color_discrete_map=mapa_cores_status)
                st.plotly_chart(fig_pie_status, use_container_width=True)
            else:
                st.info("Nenhum projeto registrado.")

        # --- GRÁFICO DE BARRAS (ABAIXO) ---
        if not df_grafico.empty and cols_competencias:
            # Pegar apenas as colunas de notas que realmente existem
            cols_notas_existentes = [f'Nota_{col}' for col in cols_competencias if f'Nota_{col}' in df_grafico.columns]
            
            if cols_notas_existentes: # Só mostrar se tiver as colunas de nota novas
                st.markdown(f"**Média por Competência ({filtro_estagiario_sidebar})**")
                medias = []
                for col_nota, col_nome in zip(cols_notas_existentes, cols_competencias):
                    media = df_grafico[col_nota].mean()
                    medias.append({'Competência': col_nome, 'Média': media})
                
                df_medias = pd.DataFrame(medias)
                
                # --- APLICAÇÃO DO GRADIENTE E BARRAS FINAS ---
                fig_bar = px.bar(df_medias, x='Competência', y='Média', 
                                 title="Média por Competência (4=Excelente, 1=Ruim)",
                                 text=df_medias['Média'].apply(lambda x: f'{x:.2f}'),
                                 range_y=[0, 4],
                                 color='Média', # Mapear cor para a Média
                                 # Gradiente Azul -> Verde
                                 color_continuous_scale=[[0, '#30515F'], [1, '#76B82A']], 
                                 range_color=[0, 4] 
                                )
                
                # Afinar as barras (aumentando o espaço entre elas)
                fig_bar.update_layout(bargap=0.5)
                
                # Remover a colorbar (legenda de cor)
                fig_bar.update_layout(coloraxis_showscale=False)
                
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("O gráfico de média por competência só funciona com os novos formulários de feedback (Iniciativa, Qualidade, etc.)")
    else:
        st.info("Nenhum feedback registrado até o momento.")
        df_grafico = pd.DataFrame() # Criar df_grafico vazio se não houver feedbacks

    # --- 2. SEÇÃO DE RELATÓRIO DE ATIVIDADES ---
    st.markdown("---")
    st.title("📋 Relatório de Atividades dos Estagiários")
    
    if not df_data.empty:
        try:
            df_data_copy = df_data.copy()
            df_filtrada = df_data_copy[
                (df_data_copy['Data_Registro'].dt.date >= data_inicio) &
                (df_data_copy['Data_Registro'].dt.date <= data_fim)
            ]
            if filtro_estagiario_sidebar != "Todos":
                df_filtrada = df_filtrada[df_filtrada['Colaborador'] == filtro_estagiario_sidebar]
            
            # Formatar as datas de volta para string para exibição
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
        
        
    # --- 3. NOVA SEÇÃO: RANKING DE DESEMPENHO ---
    st.markdown("---")
    st.title("🏆 Ranking de Desempenho dos Estagiários")
    st.info("Esta tabela combina os feedbacks dos gestores com a entrega de projetos para classificar o desempenho.")

    try:
        # 1. Obter lista mestre de estagiários
        base_estagiarios = pd.read_excel(BASE_FILE)
        df_ranking = pd.DataFrame(base_estagiarios["COLABORADOR"].dropna().unique(), columns=["Estagiário"])

        # 2. Calcular Nota Média de Feedback
        # Pegar apenas as colunas de notas que realmente existem
        cols_notas_existentes = [f'Nota_{col}' for col in cols_competencias if f'Nota_{col}' in df_grafico.columns]
        
        if not df_grafico.empty and cols_notas_existentes: 
            df_notas_melted = df_grafico.melt(id_vars=['Estagiario'], value_vars=cols_notas_existentes, value_name='Nota')
            df_notas_medias = df_notas_melted.groupby('Estagiario')['Nota'].mean().reset_index()
            df_notas_medias.rename(columns={'Estagiario': 'Estagiário', 'Nota': 'Nota Média (de 4.0)'}, inplace=True)
            df_ranking = pd.merge(df_ranking, df_notas_medias, on="Estagiário", how="left")
        else:
            df_ranking["Nota Média (de 4.0)"] = 0.0

        # 3. Calcular Métricas de Projetos (usando df_data)
        if not df_data.empty:
            # Pegar o último status de cada projeto
            df_projetos_unicos = df_data.sort_values(by='Data_Registro', ascending=True).drop_duplicates(subset=['Colaborador', 'Nome_Projeto'], keep='last')
            
            # Contar Projetos Concluídos
            df_concluidos = df_projetos_unicos[df_projetos_unicos['Status'] == 'Concluído'].groupby('Colaborador')['Nome_Projeto'].count().reset_index()
            df_concluidos.rename(columns={'Colaborador': 'Estagiário', 'Nome_Projeto': 'Projetos Concluídos'}, inplace=True)
            df_ranking = pd.merge(df_ranking, df_concluidos, on="Estagiário", how="left")

            # Contar Projetos Atrasados
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

        # Limpar NaNs e ordenar
        df_ranking.fillna(0, inplace=True)
        df_ranking = df_ranking.sort_values(by=["Nota Média (de 4.0)", "Projetos Concluídos", "Projetos Atrasados"], ascending=[False, False, True])
        
        st.dataframe(df_ranking, use_container_width=True,
                     column_config={
                         "Nota Média (de 4.0)": st.column_config.NumberColumn(format="%.2f ⭐"),
                         "Projetos Atrasados": st.column_config.NumberColumn(format="%d ⚠️")
                     })

    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar o ranking de desempenho: {e}")


# ========= REGISTRO DE ATIVIDADE =========
elif st.session_state.pagina_selecionada == "Registro de Atividade":
    # (Código com Status "Iniciado" e % automático)
    st.title("📋 Registro de Atividade")

    try:
        base = pd.read_excel(BASE_FILE, dtype=str)
    except Exception as e:
        st.warning(f"Não foi possível carregar {BASE_FILE}: {e}")
        base = pd.DataFrame(columns=["MATRICULA", "COLABORADOR", "DESCRIÇÃO LOCAL", "UNIDADE"])

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
    matricula = st.text_input("Matrícula", key="matricula_input")

    confirmar = st.button("Confirmar matrícula")

    if confirmar and matricula:
        st.session_state["matricula_digitada"] = matricula

    if st.session_state.get("matricula_digitada"):
        matricula = st.session_state["matricula_digitada"]
        estagiario = base.loc[base["MATRICULA"].astype(str) == str(matricula)] if "MATRICULA" in base.columns else pd.DataFrame()

        if not estagiario.empty:
            nome = estagiario["COLABORADOR"].values[0]
            setor_estagiario = estagiario["DESCRIÇÃO LOCAL"].values[0] 
            unidade = estagiario["UNIDADE"].values[0]
            st.success(f"Bem-vindo(a), **{nome}** ({setor_estagiario} - {unidade}) 👋")
            
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

        else:
            st.error("⚠️ Matrícula não encontrada na base. Verifique e tente novamente.")
    elif confirmar and not matricula:
        st.warning("Por favor, digite uma matrícula antes de confirmar.")

# ========= REGISTRO DE FEEDBACK =========
elif st.session_state.pagina_selecionada == "Registro de Feedback":
    
    st.title("💬 Registro de Feedback do Gestor")
    st.markdown("---")
    
    if "gestor_autenticado" not in st.session_state:
        st.session_state.gestor_autenticado = False
    if "dados_gestor" not in st.session_state:
        st.session_state.dados_gestor = None

    if not st.session_state.gestor_autenticado:
        st.subheader("🔐 Acesso Restrito ao Gestor")
        matricula = st.text_input("Digite sua matrícula:")
        senha = st.text_input("Digite a senha:", type="password")

        if st.button("Entrar"):
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
            estagiario = st.selectbox("Estagiário:", estagiarios)

            st.markdown("### 1️⃣ Iniciativa e Proatividade")
            iniciativa = st.radio(
                "O estagiário demonstra iniciativa para buscar tarefas, sugerir melhorias e resolver problemas de forma autônoma?",
                ["Excelente", "Bom", "Regular", "Ruim"],
                horizontal=True
            )
            st.markdown("### 2️⃣ Capacidade de Aprendizagem e Adaptação")
            aprendizagem = st.radio(
                "Com que rapidez o estagiário absorve novos conhecimentos e se adapta a mudanças na rotina?",
                ["Excelente", "Bom", "Regular", "Ruim"],
                horizontal=True
            )
            st.markdown("### 3️⃣ Qualidade e Entrega das Atividades")
            qualidade = st.radio(
                "Qual o nível de precisão, atenção aos detalhes e cumprimento dos prazos nas tarefas atribuídas?",
                ["Excelente", "Bom", "Regular", "Ruim"],
                horizontal=True
            )
            st.markdown("### 4️⃣ Relações Interpessoais e Feedback")
            relacoes = st.radio(
                "O estagiário se comunica de forma clara, trabalha bem em equipe e aplica feedbacks recebidos?",
                ["Excelente", "Bom", "Regular", "Ruim"],
                horizontal=True
            )
            st.markdown("### 5️⃣ Registre seu feedback sobre o estagiário:")
            sugestao = st.text_area("Escreva aqui o feedback livre:")
            enviar = st.form_submit_button("💾 Enviar Feedback")

            if enviar:
                if not estagiario:
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
                            estagiario,
                            iniciativa,
                            aprendizagem,
                            qualidade,
                            relacoes,
                            sugestao
                        ])
                    st.success("✅ Feedback registrado com sucesso!")

# ========= ADMIN (ATUALIZADO COM CORREÇÃO DE DATA) =========
elif st.session_state.pagina_selecionada == "Administração":
    
    st.title("🔒 Administração de Dados")
    st.markdown("---")
    password_input = st.text_input("Digite a senha de administrador:", type="password")

    if password_input == ACCESS_PASSWORD:
        st.success("Acesso Concedido!")

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

        
        # --- NOVA SEÇÃO: EDIÇÃO DE ATIVIDADES ---
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
                    # Agora que as datas são datetime, podemos usar o DateColumn
                    column_config={
                        "Deletar": st.column_config.CheckboxColumn("Deletar?", default=False),
                        "Data_Registro": st.column_config.DateColumn("Registro", format="DD/MM/YYYY", disabled=True),
                        "Colaborador": st.column_config.Column(disabled=True),
                        "Setor": st.column_config.Column(disabled=True),
                        "Data_Inicio_Projeto": st.column_config.DateColumn("Início", format="DD/MM/YYYY"),
                        "Previsao_Conclusao": st.column_config.DateColumn("Previsão", format="DD/MM/YYYY"),
                        "Percentual_Concluido": st.column_config.NumberColumn("%", format="%d%%"), # Ainda mostramos
                        "Status": st.column_config.SelectboxColumn("Status", options=["Iniciado", "Pendente", "Concluído"]) 
                    },
                    num_rows="dynamic" 
                )

                if st.button("Salvar Atividades e Apagar Selecionadas"):
                    df_para_salvar_ativ = edited_df_atividades[edited_df_atividades['Deletar'] == False].copy()
                    df_para_salvar_ativ.drop(columns=['Deletar'], inplace=True)
                    
                    try:
                        # --- ATUALIZAR % AUTOMATICAMENTE ---
                        def map_status_to_percent(status):
                            if status == "Iniciado": return 0
                            elif status == "Pendente": return 50
                            elif status == "Concluído": return 100
                            return 0
                        df_para_salvar_ativ['Percentual_Concluido'] = df_para_salvar_ativ['Status'].apply(map_status_to_percent)
                        
                        # --- CORREÇÃO DO ERRO DE DATA (Salvamento) ---
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