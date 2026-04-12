import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

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
    return client.open("Controle_Tokens").sheet1 

try:
    planilha = conectar_planilha()
except Exception as e:
    st.error(f"Erro de conexão com a planilha de controle: {e}")
    st.stop()
# =============================================================

def enviar_email_resultados(nome_paciente, token, perguntas, respostas):
    # Lógica de Cálculo e Classificação
    total_pontos = 0
    contagem = {"INDEPENDÊNCIA": 0, "SEMI-DEPENDÊNCIA": 0, "DEPENDÊNCIA": 0}
    detalhes_respostas = []

    for i, resp in enumerate(respostas.values()):
        score = int(resp[0]) # Pega o primeiro caractere da string (1, 2 ou 3)
        total_pontos += score
        
        if score == 3:
            status = "INDEPENDÊNCIA"
        elif score == 2:
            status = "SEMI-DEPENDÊNCIA"
        else:
            status = "DEPENDÊNCIA"
        
        contagem[status] += 1
        detalhes_respostas.append(f"{perguntas[i]}\nResposta: {resp} — {status}")

    assunto = f"Resultados AIVD-Paciente - Paciente: {nome_paciente}"
    
    corpo = f"Avaliação AIVD-Paciente (Autoavaliação) concluída.\n\n"
    corpo += f"=== DADOS DO(A) PACIENTE ===\n\n"
    corpo += f"Nome Completo: {nome_paciente}\n"
    corpo += f"Token de Validação: {token}\n\n"
    
    corpo += f"=== RESUMO DO SCORE ===\n"
    corpo += f"PONTUAÇÃO TOTAL: {total_pontos} de 27\n" # 9 perguntas x 3 pontos = 27 (ajustado para 9 itens)
    corpo += f"DEPENDÊNCIA: {contagem['DEPENDÊNCIA']} | SEMI-DEPENDÊNCIA: {contagem['SEMI-DEPENDÊNCIA']} | INDEPENDÊNCIA: {contagem['INDEPENDÊNCIA']}\n\n"
    
    corpo += "================ RESPOSTAS ================\n\n"
    corpo += "\n\n".join(detalhes_respostas)

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

# Estilização do botão em Azul
st.markdown("""
    <style>
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #0047AB !important;
        color: white !important;
        border: none !important;
        padding: 0.6rem 2.5rem !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #003380 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

if "avaliacao_concluida" not in st.session_state:
    st.session_state.avaliacao_concluida = False

st.markdown("<h1 style='text-align: center;'>Clínica de Psicologia e Psicanálise Bruna Ligoski</h1>", unsafe_allow_html=True)

if st.session_state.avaliacao_concluida:
    st.success("Avaliação concluída e enviada com sucesso! Muito obrigado pela sua colaboração.")
    st.stop()

# ================= VALIDAÇÃO DO TOKEN =================
parametros = st.query_params
token_url = parametros.get("token", None)

if not token_url:
    st.warning("⚠️ Link de acesso inválido. Solicite um novo link à profissional.")
    st.stop()

try:
    registros = planilha.get_all_records()
    dados_token = None
    linha_alvo = 2
    for i, reg in enumerate(registros):
        if str(reg.get("Token")) == token_url:
            dados_token = reg
            linha_alvo += i
            break
    if not dados_token or dados_token.get("Status") != "Aberto":
        st.error("⚠️ Este link é inválido ou já foi utilizado.")
        st.stop()
except:
    st.error("Erro técnico na validação.")
    st.stop()

# ================= QUESTIONÁRIO AIVD =================
linha_fina = "<hr style='margin-top: 8px; margin-bottom: 8px;'/>"

st.markdown(linha_fina, unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Escala de Atividades Instrumentais de Vida Diária (AIVD-Paciente)</h3>", unsafe_allow_html=True)
st.markdown(linha_fina, unsafe_allow_html=True)

st.write("Leia cada item cuidadosamente. Marque a opção que mais se adequar a você de 1 a 3.")
st.markdown(linha_fina, unsafe_allow_html=True)
st.write("**Chave de resposta:** 1 - Não consegue | 2 - Com ajuda parcial | 3 - Sem ajuda")
st.markdown(linha_fina, unsafe_allow_html=True)

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
    nome_paciente = st.text_input("Nome Completo do(a) Paciente *")
    st.divider()

    respostas_coletadas = {}
    for i, p in enumerate(perguntas):
        st.write(f"**{p}**")
        respostas_coletadas[i] = st.radio(f"q_{i}", opcoes_respostas, index=None, label_visibility="collapsed")
        st.divider()

    st.markdown("<small>Fonte: Escala de Atividades Instrumentais de Vida Diária – AIVD. Lawton & Brody, 1969.</small>", unsafe_allow_html=True)

    if st.form_submit_button("Enviar Avaliação"):
        if not nome_paciente or any(r is None for r in respostas_coletadas.values()):
            st.error("Por favor, preencha o nome e responda todas as questões.")
        else:
            if enviar_email_resultados(nome_paciente, token_url, perguntas, respostas_coletadas):
                try:
                    planilha.update_cell(linha_alvo, 5, "Respondido")
                    st.session_state.avaliacao_concluida = True
                    st.rerun()
                except:
                    st.session_state.avaliacao_concluida = True
                    st.rerun()
            else:
                st.error("Erro ao enviar. Tente novamente.")
