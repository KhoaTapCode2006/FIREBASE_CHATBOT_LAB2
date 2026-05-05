import streamlit as st
import requests

st.set_page_config(page_title="My AI Text Generator", layout="centered")

st.title("TEXT GENERATOR (DEEPSEEK-R1)")
st.markdown("---")

prompt = st.text_area("Nhập câu prompt của bạn vào đây:", placeholder="Ví dụ: Write an essay about the definition of AI...")

if st.button("Gửi"):
    if prompt:
        with st.spinner("AI đang suy nghĩ..."):
            try:

                response = requests.post(
                    "http://127.0.0.1:8000/generate",
                    json={"prompt": prompt, "max_new_tokens": 150}
                )
                
                if response.status_code == 200:
                    data = response.json()

                    with st.expander("Xem quá trình suy luận (Reasoning)"):
                        st.write(data["reasoning"])

                    answer = data.get("generated_text", "Xin lỗi, AI không thể trả lời cho câu prompt này.")
                    
                    st.subheader("Phản hồi từ AI:")
                    st.info(answer) 
                else:
                    st.error("Lỗi kết nối đến API!")
            except Exception as e:
                st.error(f"Đã xảy ra lỗi: {e}")
    else:
        st.warning("Vui lòng nhập nội dung trước khi gửi.")