import streamlit as st
from services.auth_service import encrypt_token, decrypt_token
from streamlit_cookies_controller import CookieController

def show_login_form():
    st.markdown("""
        <style>
       
        .login-title {
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 class='login-title'>🔐 Login</h1>", unsafe_allow_html=True)

    cookie_controller = CookieController()
    encrypted_token = cookie_controller.get("auth_token")

    # Formulário
    with st.form(key="login_form"):
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        name = st.text_input("👤 Nome")
        password = st.text_input("🔑 Senha", type="password")

        if encrypted_token:
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button("Entrar", use_container_width=True)
            with col2:
                clear = st.form_submit_button("Limpar dados salvos", use_container_width=True)

            if submit:
                try:
                    decrypted_token = decrypt_token(encrypted_token, name, password)
                    st.session_state.token = decrypted_token
                    st.session_state.authenticated = True
                    st.rerun()
                except Exception:
                    st.error("❌ Credenciais inválidas ou token corrompido.")

            if clear:
                cookie_controller.remove("auth_token")
                st.success("✅ Dados salvos removidos. Recarregue a página.")
        else:
            token = st.text_input("🔐 Token", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)

            if submit:
                if not (name and password and token):
                    st.error("⚠️ Preencha todos os campos.")
                else:
                    try:
                        encrypted_token = encrypt_token(token, name, password)
                        cookie_controller.set("auth_token", encrypted_token, max_age=60 * 60 * 24 * 7)
                        st.session_state.token = token
                        st.session_state.authenticated = True
                        st.rerun()
                    except Exception:
                        st.error("❌ Erro ao criptografar o token.")

        st.markdown('</div>', unsafe_allow_html=True)
