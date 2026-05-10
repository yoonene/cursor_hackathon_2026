"""인테이크 → POST /reading/start → POST /chat/stream(SSE).

  cd src/backend
  uv sync --extra demo
  uv run streamlit run demo/streamlit_demo.py

환경변수 SAJU_BACKEND_URL (기본 http://127.0.0.1:8000).
궁합 대기 상태면 `partner` 폼 전용 팝업(다이얼로그)이 열립니다.
"""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Callable
from datetime import datetime

import httpx
import streamlit as st


def _default_base_url() -> str:
    return os.environ.get("SAJU_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")


def stream_chat_sse(
    base: str,
    session_id: str,
    *,
    message: str = "",
    partner: dict | None = None,
    on_delta: Callable[[str], None] | None = None,
) -> tuple[str, dict | None]:
    """POST /chat/stream. Returns (assistant_text, complete_event_dict or None)."""
    url = f"{base.rstrip('/')}/chat/stream"
    payload: dict[str, object] = {"session_id": session_id, "message": (message or "").strip()}
    if partner is not None:
        payload["partner"] = partner

    assistant_acc = ""
    complete_blob: dict | None = None
    current_event = ""

    with httpx.Client(timeout=120.0) as hc:
        with hc.stream("POST", url, json=payload) as rr:
            if rr.status_code != 200:
                return (
                    f"오류 ({rr.status_code}): {rr.read().decode(errors='replace')}",
                    None,
                )
            for line in rr.iter_lines():
                if line is None:
                    continue
                if line.startswith("event:"):
                    current_event = line[6:].strip()
                elif line.startswith("data:"):
                    data = json.loads(line[5:].strip())
                    if current_event == "prelude":
                        rp = st.session_state.get("reading_json")
                        if isinstance(rp, dict):
                            rp["counseling_board"] = data.get("counseling_board", rp.get("counseling_board"))
                            rp["saju_report"] = data.get("saju_report", rp.get("saju_report"))
                            rp["current_stage"] = data.get("current_stage")
                            st.session_state.reading_json = rp
                        show_partner = (
                            data.get("current_stage") == "collecting_compatibility_info"
                            or data.get("partner_intake_requested")
                        )
                        if show_partner:
                            st.session_state.partner_compat_dialog_needed = True
                    elif current_event == "delta":
                        assistant_acc += data.get("text", "")
                        if on_delta is not None:
                            on_delta(assistant_acc)
                    elif current_event == "complete":
                        complete_blob = data
                        assistant_acc = data.get("assistant_message", assistant_acc) or assistant_acc
                        cs = data.get("current_stage")
                        pint = bool(data.get("partner_intake_requested"))
                        if cs != "collecting_compatibility_info" and not pint:
                            st.session_state.partner_compat_dialog_needed = False
                        rp = st.session_state.get("reading_json")
                        if isinstance(rp, dict):
                            rp["current_stage"] = cs
                            rp["counseling_board"] = data.get(
                                "counseling_board", rp.get("counseling_board")
                            )
                            st.session_state.reading_json = rp

    return assistant_acc, complete_blob


@st.dialog("상대방 사주 정보 (궁합)")
def partner_compat_dialog(base: str) -> None:
    """궁합용 상대 1명 — API `partner` 블록으로 전송합니다."""
    st.caption("이름은 선택, 생년월일은 필수입니다.")

    pname = st.text_input("이름 또는 별명", value="", placeholder="선택")
    pbirth = st.date_input(
        "상대 생년월일",
        datetime(1995, 6, 2).date(),
        key="partner_birth",
    )
    use_pt = st.checkbox("상대 출생 시각 입력", value=False)
    ptime = None
    if use_pt:
        ptime = st.time_input(
            "출생 시각",
            datetime.now().replace(hour=12, minute=0, second=0, microsecond=0).time(),
        )
    gender_opt = st.selectbox(
        "성별",
        options=[
            ("입력 안 함", None),
            ("여성", "female"),
            ("남성", "male"),
            ("기타", "other"),
            ("비공개", "prefer_not_to_say"),
        ],
        format_func=lambda x: x[0],
        index=0,
        key="partner_gender_pick",
    )
    sid = st.session_state.get("session_id")
    if not sid:
        st.error("먼저 본인 리딩을 시작하세요.")
        return

    c1, c2 = st.columns(2)
    with c2:
        if st.button("나중에", use_container_width=True):
            st.session_state.partner_compat_dialog_needed = False
            st.rerun()
    with c1:
        do_submit = st.button("제출하고 궁합 보기", type="primary", use_container_width=True)

    if do_submit:
        partner_payload: dict[str, object] = {"birth_date": pbirth.isoformat()}
        tn = pname.strip()
        if tn:
            partner_payload["display_name"] = tn
        if use_pt and ptime is not None:
            partner_payload["birth_time"] = ptime.strftime("%H:%M")
        g_val = gender_opt[1]
        if g_val is not None:
            partner_payload["gender"] = g_val

        ph = st.empty()
        txt, complete = stream_chat_sse(
            base,
            sid,
            message="",
            partner=partner_payload,
        )
        st.session_state.partner_compat_dialog_needed = False
        if complete is None or txt.startswith("오류"):
            st.error(txt)
            return

        ph.success("궁합 결과 반영했습니다.")
        st.session_state.setdefault("messages", []).append({"role": "assistant", "content": txt})
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="AI 사주 상담 데모", layout="wide")
    st.title("사주 리딩 + 후속 상담 (백엔드 데모)")
    st.caption("SSE `/chat/stream`, 궁합 대기 시 상대 폼 팝업.")

    if "partner_compat_dialog_needed" not in st.session_state:
        st.session_state.partner_compat_dialog_needed = False

    base_url = _default_base_url()
    with st.sidebar:
        base_input = st.text_input("백엔드 URL", value=base_url)
        if st.button("연결 테스트"):
            try:
                r = httpx.get(f"{base_input.rstrip('/')}/health", timeout=10.0)
                if r.status_code == 200:
                    st.success(f"헬스 OK: {r.text}")
                else:
                    st.warning(f"{r.status_code}: {r.text}")
            except OSError as e:
                st.error(str(e))

    base = base_input.rstrip("/")

    if st.session_state.partner_compat_dialog_needed:
        partner_compat_dialog(base)

    left, right = st.columns([1, 2], gap="medium")

    with left:
        st.subheader("1) 인테이크")
        name = st.text_input("이름(표시)", value="", placeholder="선택", key="user_name")
        birth = st.date_input("생년월일", datetime(1998, 4, 21).date())
        use_time = st.checkbox("출생 시각 입력", value=True)
        birth_time = None
        if use_time:
            birth_time = st.time_input(
                "출생 시각",
                datetime.now().replace(hour=14, minute=30, second=0, microsecond=0).time(),
            )
        gender = st.selectbox(
            "성별",
            options=[
                ("입력 안 함", None),
                ("여성", "female"),
                ("남성", "male"),
                ("기타", "other"),
                ("비공개", "prefer_not_to_say"),
            ],
            format_func=lambda x: x[0],
            index=0,
        )

        run_reading = st.button("전체 리딩 시작", type="primary")

    if run_reading:
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.partner_compat_dialog_needed = False
        payload: dict[str, object] = {
            "session_id": st.session_state.session_id,
            "birth_date": birth.isoformat(),
        }
        trimmed = name.strip()
        if trimmed:
            payload["display_name"] = trimmed
        if use_time and birth_time is not None:
            payload["birth_time"] = birth_time.strftime("%H:%M")
        g_val = gender[1]
        if g_val is not None:
            payload["gender"] = g_val

        url = f"{base}/reading/start"
        try:
            with httpx.Client(timeout=120.0) as hc:
                r = hc.post(url, json=payload)
            if r.status_code != 200:
                st.error(f"리딩 실패 ({r.status_code}):\n{r.text}")
                st.session_state.pop("reading_json", None)
            else:
                data = r.json()
                st.session_state.reading_json = data
                assistant = data.get("assistant_message", "")
                if assistant:
                    st.session_state.messages.append({"role": "assistant", "content": assistant})
                st.success("리딩이 준비되었습니다. 오른쪽에서 이어서 질문할 수 있습니다.")
        except Exception as exc:  # noqa: BLE001
            st.exception(exc)
            st.session_state.pop("reading_json", None)

    with right:
        st.subheader("2) 결과 & 채팅")
        rp = st.session_state.get("reading_json")
        if isinstance(rp, dict):
            with st.expander("saju_report (JSON)", expanded=False):
                st.json(rp.get("saju_report", {}))

        session_id = st.session_state.get("session_id")

        for msg in st.session_state.get("messages", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        chat_prompt = st.chat_input(
            "후속 질문을 입력하세요…",
            disabled=not session_id or st.session_state.partner_compat_dialog_needed,
        )

        if st.session_state.partner_compat_dialog_needed and session_id:
            st.info("궁합을 보려면 위 **상대방 사주 정보** 팝업을 채워 주세요.")

        if chat_prompt and session_id:
            if st.session_state.partner_compat_dialog_needed:
                st.warning("먼저 상대방 정보 팝업을 완료하거나 닫아 주세요.")
            else:
                st.session_state.setdefault("messages", []).append({"role": "user", "content": chat_prompt})
                assistant_acc = ""
                place = st.empty()
                try:
                    txt, _ = stream_chat_sse(
                        base,
                        session_id,
                        message=chat_prompt,
                        partner=None,
                        on_delta=lambda acc: place.markdown(acc),
                    )
                    assistant_acc = txt
                    if assistant_acc.startswith("오류"):
                        place.error(assistant_acc)
                except Exception as exc:  # noqa: BLE001
                    assistant_acc = f"요청 오류: {exc}"
                    place.error(assistant_acc)
                st.session_state.messages.append({"role": "assistant", "content": assistant_acc})
                st.rerun()


if __name__ == "__main__":
    main()
