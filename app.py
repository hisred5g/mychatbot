import os
from dotenv import load_dotenv
import streamlit as st
from google import genai
from google.genai import types

load_dotenv()

SYSTEM_PROMPT = "너는 파이썬 개발자야. 코딩에 관련된 질문에 친절하게 대답하지"

st.set_page_config(page_title="Gemini Chatbot", page_icon="💬")
st.title("💬 파이썬 가이드 챗봇")

# ── 세션 상태 ─────────────────────────────────────────────
if "messages" not in st.session_state:
    # role: "user" | "assistant", content: str
    st.session_state.messages = []

# ── 상단: 대화 전체 초기화 버튼 ───────────────────────────
top_cols = st.columns([1, 6, 1])
with top_cols[0]:
    if st.button("초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── 말풍선 스타일(CSS) ─────────────────────────────────────
st.markdown(
    """
    <style>
      .chat-wrap { width: 100%; }
      .chat-row { display: flex; margin: 8px 0; }
      .chat-row.user { justify-content: flex-end; }
      .chat-row.ai   { justify-content: flex-start; }
      .bubble {
        max-width: 80%;
        padding: 12px 14px;
        border-radius: 18px;
        line-height: 1.55;
        word-wrap: break-word;
        white-space: pre-wrap;
        box-shadow: 0 1px 2px rgba(0,0,0,0.08);
        font-size: 16px;
      }
      .bubble.user {
        background: #DCF8C6;     /* user: 연두색 */
        border-top-right-radius: 6px;
      }
      .bubble.ai {
        background: #F1F0F0;     /* ai: 회색 */
        border-top-left-radius: 6px;
      }
      .name {
        font-size: 12px; opacity: 0.6; margin-bottom: 4px;
      }
      .container { margin-top: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── 히스토리(말풍선) 렌더링 ────────────────────────────────
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in st.session_state.messages:
    role_class = "user" if m["role"] == "user" else "ai"
    name = "나" if m["role"] == "user" else "AI"
    # 간단한 HTML 렌더(마크다운 처리 필요 시 st.markdown 병행 가능)
    html = f"""
    <div class="chat-row {role_class}">
      <div class="bubble {role_class}">
        <div class="name">{name}</div>
        {m['content']}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── 프롬프트 빌더(시스템+히스토리+현재입력 텍스트로 통합) ─────────
def build_prompt(messages, user_text):
    history_txt = ""
    for msg in messages:
        role = "사용자" if msg["role"] == "user" else "AI"
        history_txt += f"{role}: {msg['content']}\n"
    return (
        f"[시스템]\n{SYSTEM_PROMPT}\n\n"
        f"[대화]\n{history_txt}"
        f"사용자: {user_text}\nAI:"
    )

# ── 입력(하단 고정) ───────────────────────────────────────
user_input = st.chat_input("메시지를 입력하세요…")

# ── 메시지 처리 ──────────────────────────────────────────
if user_input is not None:
    # 1) 사용자 메시지를 기록
    st.session_state.messages.append({"role": "user", "content": user_input})

    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # 4) 프롬프트 구성
        prompt = build_prompt(st.session_state.messages[:-1], user_input)

        # 5) 모델 호출 (google-genai는 config=GenerateContentConfig 로 전달)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7, 
            ),
        )
        answer = getattr(resp, "text", "") or "(빈 응답)"

        # 6) AI 응답 기록 & 즉시 갱신
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

    except Exception as e:
        st.error(f"오류: {e}")
