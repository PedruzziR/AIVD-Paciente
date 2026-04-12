import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ================= CONFIGURAÇÕES DE E-MAIL =================
SEU_EMAIL = st.secrets["EMAIL_USUARIO"]
SENHA_DO_EMAIL = st.secrets["SENHA_USUARIO"]
# ===========================================================

# ================= CONEXÃO COM GOOGLE SHEETS =================
@st.cache_resource
def conectar_planilha():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=escopos)
    client = gspread.authorize(creds)
    return client.open("AIVD-Paciente").sheet1 

try:
    planilha = conectar_planilha()
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()
# =============================================================

def enviar_email_resultados(nome_paciente, cpf, perguntas, respostas):
    assunto = f"Resultados AIVD-Paciente - Paciente: {nome_paciente}"
    
    corpo = f"Avaliação AIVD-Paciente (Autoavaliação) concluída.\n\n"
    corpo += f"=== DADOS DO(A) PACIENTE ===\n"
    corpo += f"Nome Completo: {nome_paciente}\n"
    corpo += f"CPF de Login: {cpf}\n\n"
    corpo += "================ RESPOSTAS ================\n\n"
    
    # Lista cada pergunta com a resposta selecionada abaixo
    for i, pergunta in enumerate(perguntas):
        corpo += f"{pergunta}\n"
        corpo += f"Resposta: {respostas[i]}\n\n"

    msg = MIMEMultipart()
    msg['From'] = SEU_EMAIL
    msg['To'] = "psicologabrunaligoski@gmail.com"
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SEU_EMAIL, SENHA_DO_EMAIL)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

st.set_page_config(page_title="AIVD-Paciente", layout="centered")

if "logado" not in st.session_state:
    st.session_state.logado = False
if "avaliacao_concluida" not in st.session_state:
    st.session_state.avaliacao_concluida = False

st.title("Clínica de Psicologia e Psicanálise Bruna Ligoski")

# ================= TELA DE LOGIN =================
if not st.session_state.logado:
    st.write("Bem-vindo(a) à Avaliação AIVD-Paciente.")
    
    with st.form("form_login"):
        cpf_input = st.text_input("CPF do Paciente (Apenas números)")
        senha_input = st.text_input("Senha", type="password")
        if st.form_submit_button("Acessar"):
            if senha_input == st.secrets["SENHA_MESTRA"]:
                try:
                    cpfs = planilha.col_values(1)
                except:
                    cpfs = []
                if cpf_input in cpfs:
                    st.error("Acesso bloqueado. CPF já registrado.")
                else:
                    st.session_state.logado = True
                    st.session_state.cpf_paciente = cpf_input
                    st.rerun()
            else:
                st.error("Senha incorreta.")

# ================= TELA FINAL =================
elif st.session_state.avaliacao_concluida:
    st.success("Avaliação concluída e enviada com sucesso! Muito obrigado pela sua colaboração.")

# ================= QUESTIONÁRIO AIVD-PACIENTE =================
else:
    st.write("### AIVD-Paciente")
    st.write("Leia cada item cuidadosamente. Marque a opção que mais se adequar a você de 1 a 3.")
    st.write("**Chave de resposta:** 1 - Não consegue | 2 - Com ajuda parcial | 3 - Sem ajuda")
    st.divider()
    
    perguntas = [
        "1. O(a) senhor(a) consegue usar o telefone?",
        "2. O(a) senhor(a) consegue ir a locais distantes, usando algum transporte, sem necessidade de planejamentos especiais?",
        "3. O(a) senhor(a) consegue fazer compras?",
        "4. O(a) senhor(a) consegue preparar suas próprias refeições?",
        "5. O(a) senhor(a) consegue arrumar a casa?",
        "6. O(a) senhor(a) consegue fazer trabalhos manuais domésticos, como pequenos reparos?",
        "7. O(a) senhor(a) consegue lavar e passar sua roupa?",
        "8. O(a) senhor(a) consegue tomar seus remédios na dose e horários corretos?",
        "9. O(a) senhor(a) consegue cuidar de suas finanças?"
    ]

    opcoes_respostas = ["1 - Não consegue", "2 - Com ajuda parcial", "3 - Sem ajuda"]

    with st.form("formulario_avaliacao"):
        st.subheader("Identificação")
        nome_paciente = st.text_input("Nome Completo *")
        st.divider()

        respostas_coletadas = {}
        for i, p in enumerate(perguntas):
            st.write(f"**{p}**")
            respostas_coletadas[i] = st.radio(f"q_{i}", opcoes_respostas, index=None, label_visibility="collapsed")
            st.write("---")

        st.markdown("<small>Fonte: Escala de Atividades Instrumentais de Vida Diária – AIVD. Lawton & Brody, 1969.</small>", unsafe_allow_html=True)
        st.write("")

        if st.form_submit_button("Finalizar"):
            if not nome_paciente or any(r is None for r in respostas_coletadas.values()):
                st.error("Preencha todos os campos e responda todas as questões.")
            else:
                if enviar_email_resultados(nome_paciente, st.session_state.cpf_paciente, perguntas, respostas_coletadas):
                    try:
                        planilha.append_row([st.session_state.cpf_paciente])
                    except:
                        pass
                    st.session_state.avaliacao_concluida = True
                    st.rerun()
                else:
                    st.error("Houve um erro no envio. Avise a profissional responsável.")
