import streamlit as st
import numpy as np
import io
import wave
import matplotlib.pyplot as plt

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sintetizador Matemático",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS para um visual Dark moderno semelhante ao React
st.markdown("""
    <style>
        .main { background-color: #020617; color: #f8fafc; font-family: sans-serif; }
        .stSidebar { background-color: #0f172a; }
        h1, h2, h3 { color: #38bdf8 !important; }
        .stButton>button { 
            background-color: #10b981; color: white; border-radius: 8px; font-weight: bold; width: 100%;
        }
        .stButton>button:hover { background-color: #059669; }
        .katex-html { color: #cbd5e1; font-size: 1.1em; }
        .math-box { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CABEÇALHO
# ==========================================
st.title("Sintetizador Matemático de Formas de Onda")
st.markdown("Escreva sua própria função matemática ou escolha uma Série de Fourier e ouça o resultado sonoro instantaneamente!")
st.markdown("---")

# ==========================================
# PRESETS DE FUNÇÕES E SÉRIES
# ==========================================
PRESETS = {
    "Onda Senoidal Pura": {
        "formula": "np.sin(2 * np.pi * f * t)",
        "latex": r"y(t) = \sin(2\pi f t)",
        "desc": "A forma mais pura de som. Um único harmônico."
    },
    "Onda Quadrada (Série de Fourier)": {
        "formula": "sum([ (4/(np.pi*(2*k+1))) * np.sin(2 * np.pi * (2*k+1) * f * t) for k in range(N)])",
        "latex": r"y(t) = \sum_{k=0}^{N-1} \frac{4}{\pi(2k+1)} \sin(2\pi(2k+1)ft)",
        "desc": "Composição de harmônicos ímpares. Som 'oco' típico de videogames antigos."
    },
    "Onda Dente de Serra (Série)": {
        "formula": "sum([ (2/(np.pi*n)) * ((-1)**(n+1)) * np.sin(2 * np.pi * n * f * t) for n in range(1, N+1)])",
        "latex": r"y(t) = \sum_{n=1}^{N} \frac{2}{\pi n} (-1)^{n+1} \sin(2\pi nft)",
        "desc": "Contém todos os harmônicos inteiros. Timbre rico e brilhante (metaleiras e cordas)."
    },
    "Onda Amortecida (Batimento)": {
        "formula": "np.exp(-3*t) * (np.sin(2 * np.pi * f * t) + np.sin(2 * np.pi * (f*1.02) * t))",
        "latex": r"y(t) = e^{-3t} \left( \sin(2\pi f_1 t) + \sin(2\pi f_2 t) \right)",
        "desc": "Duas frequências muito próximas causam 'batimento', e o som decai no tempo (como um sino ou corda percutida)."
    },
    "Personalizada (Escreva seu código)": {
        "formula": "np.sin(2 * np.pi * f * t) * np.sin(2 * np.pi * 5 * t)",
        "latex": r"y(t) = \text{Sua Equação Python/NumPy (Ex: AM, FM, Ruído)}",
        "desc": "Use 't' como variável de tempo, 'f' como frequência base e 'N' como harmônicos (se usar sum)."
    }
}

# ==========================================
# BARRA LATERAL (CONTROLES)
# ==========================================
with st.sidebar:
    st.header("Parâmetros do Sintetizador")
    
    preset_choice = st.selectbox("Escolha a Forma de Onda:", list(PRESETS.keys()))
    
    st.markdown("### Ajustes Acústicos")
    freq = st.slider("Frequência Base (Hz) - $f$", 110, 880, 220, 10, help="220Hz = Nota Lá (A3)")
    duracao = st.slider("Duração do Áudio (s)", 0.5, 5.0, 2.0, 0.5)
    volume = st.slider("Volume Acústico", 0.0, 1.0, 0.5, 0.1)
    
    st.markdown("### Precisão Matemática")
    if "Série" in preset_choice or "Série" in PRESETS[preset_choice]["desc"]:
        harmonics = st.slider("Harmônicos de Fourier (N)", 1, 50, 10)
    else:
        harmonics = 1 # Fallback
        
    st.markdown("---")
    st.markdown("<div style='font-size: 0.85em; color: #94a3b8;'>Dica: O ouvido humano percebe de 20Hz a 20.000Hz. Frequências mais altas na Série de Fourier criarão o timbre real do instrumento.</div>", unsafe_allow_html=True)

# ==========================================
# MOTOR DE SÍNTESE SONORA E GRÁFICO
# ==========================================
col_plot, col_info = st.columns([2, 1])

with col_info:
    st.markdown("### Informações da Equação")
    st.markdown(f"<div class='math-box'>{PRESETS[preset_choice]['desc']}</div>", unsafe_allow_html=True)
    
    st.markdown("#### Fórmúla Analítica:")
    st.latex(PRESETS[preset_choice]['latex'])
    
    st.markdown("#### Expressão Avaliada:")
    
    if preset_choice == "Personalizada (Escreva seu código)":
        if 'custom_eq' not in st.session_state:
            st.session_state['custom_eq'] = PRESETS[preset_choice]["formula"]
            
        def update_eq(val, action="add"):
            """Callback executado ao clicar nos botões da calculadora"""
            if action == "add":
                st.session_state['custom_eq'] += val
            elif action == "backspace":
                st.session_state['custom_eq'] = st.session_state['custom_eq'][:-1]
            elif action == "clear":
                st.session_state['custom_eq'] = ""

        def update_from_area():
            """Sincroniza caso o usuário resolva digitar manualmente no teclado"""
            st.session_state['custom_eq'] = st.session_state['text_area_eq']

        st.text_area(
            "Edite a expressão (Sintaxe NumPy - use 't' e 'f'):", 
            value=st.session_state['custom_eq'], 
            height=80,
            key='text_area_eq',
            on_change=update_from_area
        )
        
        st.markdown("##### Teclado Científico Acústico")
        
        # Matriz de botões: (Label que aparece, Valor inserido no código)
        teclas = [
            [('sin(', 'np.sin('), ('cos(', 'np.cos('), ('exp(', 'np.exp('), ('π', 'np.pi'), ('⌫', 'backspace')],
            [('7', '7'), ('8', '8'), ('9', '9'), ('÷', '/'), ('t', 't')],
            [('4', '4'), ('5', '5'), ('6', '6'), ('×', '*'), ('f', 'f')],
            [('1', '1'), ('2', '2'), ('3', '3'), ('-', '-'), ('(', '(')],
            [('0', '0'), ('.', '.'), ('^', '**'), ('+', '+'), (')', ')')]
        ]
        
        # Desenha a grade de botões perfeitamente alinhada
        for linha in teclas:
            cols = st.columns(5)
            for i, (label, valor) in enumerate(linha):
                with cols[i]:
                    if label == '⌫':
                        st.button(label, on_click=update_eq, args=("", "backspace"), use_container_width=True, key=f"btn_{label}")
                    else:
                        st.button(label, on_click=update_eq, args=(valor, "add"), use_container_width=True, key=f"btn_{label}_{valor}")
                        
        st.button("Limpar Tudo", on_click=update_eq, args=("", "clear"), use_container_width=True)

        formula_to_eval = st.session_state['custom_eq']
    else:
        st.code(PRESETS[preset_choice]["formula"], language="python")
        formula_to_eval = PRESETS[preset_choice]["formula"]
        
    gerar_audio = st.button("Gerar e Ouvir Som", use_container_width=True, type="primary")

# Lógica de Geração do Áudio
if gerar_audio or 'audio_data' not in st.session_state:
    try:
        # Parâmetros de Amostragem de Áudio
        sample_rate = 44100 # Qualidade de CD
        t = np.linspace(0, duracao, int(sample_rate * duracao), endpoint=False)
        f = freq
        N = harmonics
        
        # Avalia a equação matemática de forma vetorizada com NumPy
        # Nota: Eval é usado aqui em ambiente seguro (local/oficina) para permitir digitação livre de fórmulas.
        with st.spinner("Sintetizando áudio matemático..."):
            y_eval = eval(formula_to_eval)
            
            # Normalização (Evitar estouro de áudio)
            if np.max(np.abs(y_eval)) > 0:
                y_eval = y_eval / np.max(np.abs(y_eval)) 
            
            y_eval = y_eval * volume
            
            # Converte float (-1.0 a 1.0) para Inteiro 16-bit PCM (formato WAV)
            audio_pcm = np.int16(y_eval * 32767)
            
            # Cria o arquivo WAV em memória (Buffer)
            wav_io = io.BytesIO()
            with wave.open(wav_io, 'wb') as wf:
                wf.setnchannels(1) # Mono
                wf.setsampwidth(2) # 2 bytes = 16 bits
                wf.setframerate(sample_rate)
                wf.writeframes(audio_pcm.tobytes())
            
            st.session_state['audio_data'] = wav_io.getvalue()
            
            # Gráfico de Visualização Rápida (Plota apenas os primeiros ciclos)
            ciclos_para_plotar = 4
            amostras_plot = int((sample_rate / freq) * ciclos_para_plotar)
            
            st.session_state['plot_t'] = t[:amostras_plot] * 1000 # em milissegundos
            st.session_state['plot_y'] = y_eval[:amostras_plot]
            
    except Exception as e:
        st.error(f"Erro ao avaliar a equação matemática. Verifique a sintaxe. Detalhes: {e}")

# ==========================================
# RENDERIZAÇÃO DO ÁUDIO E GRÁFICO
# ==========================================
with col_plot:
    st.markdown("### Osciloscópio (Visualização da Onda)")
    
    if 'audio_data' in st.session_state:
        # Toca o Áudio Nativo do Streamlit
        st.audio(st.session_state['audio_data'], format="audio/wav")
        
        # Plota o gráfico com Matplotlib estilo Dark
        fig, ax = plt.subplots(figsize=(10, 4.5))
        fig.patch.set_facecolor('#020617')
        ax.set_facecolor('#0f172a')
        
        ax.plot(st.session_state['plot_t'], st.session_state['plot_y'], color='#38bdf8', linewidth=2.5)
        ax.fill_between(st.session_state['plot_t'], st.session_state['plot_y'], 0, color='#38bdf8', alpha=0.1)
        
        ax.set_title(f"Recorte Temporal ({freq} Hz)", color='white', pad=15)
        ax.set_xlabel("Tempo (milissegundos)", color='#94a3b8')
        ax.set_ylabel("Amplitude Acústica", color='#94a3b8')
        
        ax.tick_params(colors='#94a3b8')
        for spine in ax.spines.values():
            spine.set_color('#334155')
            
        ax.grid(True, linestyle='--', color='#334155', alpha=0.7)
        ax.set_ylim(-1.2, 1.2)
        
        st.pyplot(fig)