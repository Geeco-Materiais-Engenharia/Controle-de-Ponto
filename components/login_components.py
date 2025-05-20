import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from services.auth_service import encrypt_token, decrypt_token

def show_login_form():
    # st.set_page_config(page_title="Login", layout="centered")

    # Lê do localStorage (chave 'auth_token') — retorna None se não existir
    encrypted_token = streamlit_js_eval(js_expressions="localStorage.getItem('auth_token')", key="get_token")

    st.markdown("<h1 style='text-align: center;'>🔐 Login</h1>", unsafe_allow_html=True)

    with st.form(key="login_form"):
        name = st.text_input("👤 Nome")
        password = st.text_input("🔑 Senha", type="password")

        if encrypted_token:
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Entrar")
            with col2:
                clear = st.form_submit_button("Limpar dados")

            if submit:
                try:
                    decrypted = decrypt_token(encrypted_token, name, password)
                    st.session_state.authenticated = True
                    st.session_state.token = decrypted
                    st.success("✅ Login realizado!")
                    st.rerun()
                except Exception as e:
                    st.error("❌ Credenciais inválidas ou token corrompido.")

            if clear:
                streamlit_js_eval(js_expressions="localStorage.removeItem('auth_token')", key="clear_token")
                st.success("✅ Token removido! Recarregue a página.")

        else:
            token = st.text_input("🔐 Token", type="password")
            submit = st.form_submit_button("Entrar")

            if submit:
                if not (name and password and token):
                    st.error("⚠️ Preencha todos os campos.")
                else:
                    try:
                        encrypted = encrypt_token(token, name, password)
                        # Salva o token criptografado no localStorage
                        streamlit_js_eval(js_expressions=f"localStorage.setItem('auth_token', '{encrypted}')", key="set_token")
                        st.session_state.authenticated = True
                        st.session_state.token = token
                        st.success("✅ Login realizado! Recarregando...")
                        st.rerun()
                    except Exception as e:
                        st.error("❌ Erro ao criptografar o token.")
