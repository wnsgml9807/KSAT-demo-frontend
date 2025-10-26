"""
Streamlit 프론트엔드
KSAT Agent 사용자 인터페이스
"""
import streamlit as st
import requests
import json
from typing import Dict, Any
import time
import base64
from pathlib import Path

# 페이지 설정
st.set_page_config(
    page_title="KSAT Agent",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS 스타일 (viewer_streamlit.py와 동일하게 복원)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700;800&display=swap');
    
    .passage-font {
        border: 0.5px solid black;
        border-radius: 0px;
        padding: 12px;
        margin-bottom: 20px;
        font-family: 'Nanum Myeongjo', serif !important;
        line-height: 1.7;
        letter-spacing: -0.01em;
        font-weight: 500;
        background: #ffffff;
        width: 12cm;
        text-align: justify;
        text-justify: inter-word;
    }
    
    .passage-font p { 
        margin: 0; 
        text-indent: 1em; 
        text-align: justify; 
    }
    
    .passage-font .section-label { 
        font-weight: 700; 
        margin: 1em 0 0.5em 0; 
        text-indent: 0; 
    }
    
    .passage-font .section-label:first-of-type { 
        margin-top: 0; 
    }
    
    .q-material .passage-font { 
        width: calc(12cm - 1em); 
    }
    
    .question-font {
        font-family: 'Nanum Myeongjo', serif !important;
        line-height: 1.7em;
        letter-spacing: -0.01em;
        font-weight: 500;
        margin-bottom: 1.5em;
        width: 12cm;
        text-align: justify;
        text-justify: inter-word;
    }
    
    .question-block { 
        padding: 8px 6px; 
    }
    
    .q-header { 
        font-weight: 700; 
        margin-bottom: 8px;
        text-indent: -1em; 
        padding-left: 1em;
    }
    
    .q-material { 
        margin: 8px 0; 
        margin-left: 1em; 
    }
    
    .q-choices { 
        margin-top: 8px; 
        margin-left: 1em; 
    }
    
    .q-choices p { 
        text-indent: -1em; 
        padding-left: 1em; 
        margin: 0.3em 0;
    }
    
    .explanation-item {
        text-indent: -1.5em;
        padding-left: 1.5em;
        margin: 0.3em 0;
    }
    
    /* 지문+문항 통합 컨테이너 */
    .content-wrapper {
        width: 100%;
        overflow-x: auto;
    }
    
    .content-container {
        display: flex;
        gap: 20px;
        width: calc(26cm + 20px);
        min-width: calc(26cm + 20px);
        margin: 0 auto;
    }
    
    .passage-section {
        width: 13cm;
        min-width: 13cm;
        max-width: 13cm;
        flex-shrink: 0;
        padding-right: 5px;
        border-right: 2px solid #000000;
    }
    
    .questions-section {
        width: 13cm;
        min-width: 13cm;
        max-width: 13cm;
        flex-shrink: 0;
        padding-left: 5px;
    }
    
    /* 해설 섹션 */
    .explanation-section {
        width: 100%;
        max-width: 20cm;
        margin: 0 auto;
        padding: 20px;
    }
    
    .explanation-item-block {
        margin-bottom: 30px;
    }
    
    .explanation-section .question-font {
        width: 100%;
        max-width: none;
    }
    
    /* 스피너 애니메이션 */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .spinner {
        display: inline-block;
        width: 14px;
        height: 14px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #1976d2;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin-right: 8px;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)

# 백엔드 API URL (Streamlit Secrets 사용, 없으면 로컬 기본값)
try:
    BACKEND_URL = st.secrets.get("BACKEND_URL")
except Exception as e:
    BACKEND_URL = "http://localhost:8000"

# 세션 상태 초기화
if 'generated_result' not in st.session_state:
    st.session_state.generated_result = None
if 'progress_tasks' not in st.session_state:
    st.session_state.progress_tasks = []
if 'is_generating' not in st.session_state:
    st.session_state.is_generating = False
if 'selected_output_file' not in st.session_state:
    st.session_state.selected_output_file = None


def init_progress_tasks(num_questions: int):
    """진행 상황 태스크 초기화"""
    tasks = [
        {'label': '논리 구조 설계', 'status': 'pending'},
        {'label': '지문 생성', 'status': 'pending'},
    ]
    for i in range(num_questions):
        tasks.append({'label': f'{i+1}번 문항 생성', 'status': 'pending'})
    st.session_state.progress_tasks = tasks

def update_task_status(task_label: str, status: str):
    """특정 태스크 상태 업데이트"""
    for task in st.session_state.progress_tasks:
        if task['label'] == task_label:
            task['status'] = status
            break


def render_progress_panel():
    """진행 상황 패널 렌더링 (Streamlit 네이티브 컴포넌트 사용)"""
    # 헤더는 항상 표시
    st.markdown("#### 🔄 진행 현황")
    
    # progress_tasks가 있을 때만 내부 컨테이너에 진행 상황 표시
    if st.session_state.get('progress_tasks'):
        # 내부 컨테이너로 진행 상황 감싸기
        with st.container():
            # 전체 진행률 계산
            total_tasks = len(st.session_state.progress_tasks)
            completed_tasks = sum(1 for task in st.session_state.progress_tasks if task['status'] == 'complete')
            in_progress_tasks = sum(1 for task in st.session_state.progress_tasks if task['status'] == 'in_progress')
            progress_percentage = completed_tasks / total_tasks if total_tasks > 0 else 0
            
            # 전체 프로그레스 바
            st.progress(progress_percentage, text=f"전체 진행률: {completed_tasks}/{total_tasks}")
            
            # 각 태스크 상태 표시 (배지 스타일 + 스피너)
            for idx, task in enumerate(st.session_state.progress_tasks):
                status = task['status']
                label = task['label']
                
                # 스피너 및 배지 스타일 정의
                if status == 'pending':
                    spinner_html = ''
                    badge_html = '<span style="background-color: #e0e0e0; color: #666; padding: 2px 8px; border-radius: 10px; font-size: 0.85em; font-weight: 500;">대기</span>'
                    text_style = 'font-size: 0.95em;'
                elif status == 'in_progress':
                    spinner_html = '<span class="spinner"></span>'
                    badge_html = '<span style="background-color: #1976d2; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.85em; font-weight: 600;">진행중</span>'
                    text_style = 'font-size: 0.95em; font-weight: 500;'
                elif status == 'complete':
                    spinner_html = ''
                    badge_html = '<span style="background-color: #4caf50; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.85em; font-weight: 500;">완료</span>'
                    text_style = 'font-size: 0.95em; color: #999;'
                
                # 행 표시 (스피너 + 레이블 + 배지)
                st.markdown(
                    f'<div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; '
                    f'border-bottom: 1px solid #f0f0f0;">'
                    f'<div style="display: flex; align-items: center;">'
                    f'{spinner_html}'
                    f'<span style="{text_style}">{label}</span>'
                    f'</div>'
                    f'{badge_html}'
                    f'</div>',
                    unsafe_allow_html=True
                )
    else:
        # 생성 전에는 빈 메시지 표시
        st.info("생성 버튼을 클릭하면 진행 상황이 표시됩니다.")


def render_passage(passage_dict: dict):
    """지문 렌더링 (viewer_streamlit.py와 동일)"""
    import re
    # passage_dict는 Passage 객체의 dict 형태
    # 'passage', 'content', 'passage_text' 중 하나를 사용
    text = passage_dict.get('passage', passage_dict.get('content', passage_dict.get('passage_text', '')))
    
    # (가), (나) 분리형 지문 처리
    if re.search(r'^\s*\(가\)', text, re.MULTILINE):
        parts = re.split(r'(\((?:가|나)\))', text)
        html = ""
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part in ['(가)', '(나)']:
                html += f"<p class='section-label'>{part}</p>"
            else:
                paragraphs = [p.strip() for p in part.split("\n") if p.strip()]
                html += "".join(f"<p>{p}</p>" for p in paragraphs)
    else:
        # 일반 지문
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        html = "".join(f"<p>{p}</p>" for p in paragraphs)
    
    st.markdown(f"<div class='passage-font'>{html}</div>", unsafe_allow_html=True)


def render_questions(questions: list):
    """문항 렌더링 (해설 제외)"""
    questions_html = ""
    for q in questions:
        # 발문에서 '않은' 밑줄 처리
        question_text = q.get('question', '')
        question_text = question_text.replace('않은', '<u>않은</u>')
        
        # 문항 HTML 생성
        questions_html += (
            f"<div class='question-font question-block'>"
            f"<div class='q-header'>{q.get('question_number')}. {question_text}</div>"
            + (f"<div class='q-material'><div class='passage-font'>{q.get('material','')}</div></div>" if q.get('material') else "")
            + (
                "<div class='q-choices'>"
                f"<p>① {q.get('choices_1','')}</p>"
                f"<p>② {q.get('choices_2','')}</p>"
                f"<p>③ {q.get('choices_3','')}</p>"
                f"<p>④ {q.get('choices_4','')}</p>"
                f"<p>⑤ {q.get('choices_5','')}</p>"
                "</div>"
            )
            + "</div>"
        )
    
    return questions_html


def render_explanations(questions: list):
    """해설 렌더링 - 모든 해설을 하나로 이어서 표시"""
    # 모든 해설을 하나의 HTML 문자열로 구성
    all_explanations_html = "<div class='explanation-section'>"
    
    for q in questions:
        answer_symbol = q.get('answer', '①')
        num_to_symbol = {1: '①', 2: '②', 3: '③', 4: '④', 5: '⑤'}
        answer_num = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}.get(answer_symbol, 1)
        
        # 각 문항 해설 구성
        all_explanations_html += f"<div class='explanation-item-block'>"
        all_explanations_html += f"<h4>{q.get('question_number')}번 문항</h4>"
        all_explanations_html += f"<div class='question-font'>"
        all_explanations_html += f"<strong>정답. {num_to_symbol[answer_num]}</strong><br/><br/>"
        
        # [정답 풀이]
        correct_explanation = q.get(f'explanation_{answer_num}', '')
        all_explanations_html += f"<strong>[정답 풀이]</strong><br/>"
        all_explanations_html += f"{correct_explanation}<br/><br/>"
        
        # [오답 해설]
        all_explanations_html += f"<strong>[오답 해설]</strong><br/>"
        for i in range(1, 6):
            if i != answer_num:
                wrong_explanation = q.get(f'explanation_{i}', '')
                all_explanations_html += f"<p class='explanation-item'>{num_to_symbol[i]} {wrong_explanation}</p>"
        
        all_explanations_html += "</div></div>"
    
    all_explanations_html += "</div>"
    
    # 한 번에 모든 해설 렌더링
    st.markdown(all_explanations_html, unsafe_allow_html=True)


@st.dialog("⚙️ 신규 생성 상세 설정", width="medium")
def show_generation_dialog():
    """생성 설정 다이얼로그"""
    
    # 분야 선택
    st.markdown("#### 분야 선택")
    
    subfield_options = {
        "인문예술": ["동양철학", "서양철학", "논리학", "예술"],
        "법": ["정치/제도/행정", "법규"],
        "경제": ["경제현상", "제도/규제"],
        "과학기술": ["과학/기술", "정보통신", "기계장치", "생명과학", "자연현상"]
    }
    
    field = st.selectbox(
        "분야",
        options=["인문예술", "법", "경제", "과학기술"],
        index=0,
        label_visibility="collapsed",
        key="dialog_field_select"
    )
    
    subfield = st.selectbox(
        "세부 분야",
        options=subfield_options[field],
        index=0,
        label_visibility="collapsed",
        key="dialog_subfield_select"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 유형 선택
    st.markdown("#### 유형 선택")
    type_input = st.radio(
        "유형",
        options=["단일형", "(가),(나) 분리형"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="dialog_type_input"
    )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 주제 입력
    st.markdown("#### 주제")
    subject_mode = st.selectbox(
        "주제 설정 방식",
        options=["자동", "수동"],
        index=0,
        label_visibility="collapsed",
        key="dialog_subject_mode"
    )
    subject = st.text_input(
        "주제",
        placeholder="예: 플라톤의 이데아론",
        label_visibility="collapsed",
        disabled=(subject_mode == "자동"),
        key="dialog_subject_input"
    )
    if subject_mode == "자동":
        subject = None
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 핵심 출제 포인트
    st.markdown("#### 핵심 출제 포인트")
    
    points_options = [
        "자동",
        "변수 간의 관계 이해하기",
        "단계에 따른 구성요소의 역할과 상태 변화 추적하기",
        "특성과 원리 이해하기",
        "조건의 중첩과 예외 구조 파악하기",
        "논리적 규칙 파악하기",
        "공통점/차이점 파악하기"
    ]
    
    points = st.selectbox(
        "핵심 출제 포인트",
        options=points_options,
        index=0,
        label_visibility="collapsed",
        key="dialog_points_select"
    )
    
    if points == "자동":
        points = None
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 문항 구성
    st.markdown("#### 문항 구성")
    num_questions = st.number_input("문항 개수", min_value=1, max_value=6, value=3, step=1, key="dialog_num_questions")
    
    questions_input = []
    for i in range(num_questions):
        with st.expander(f"**{i+1}번 문항**", expanded=(i == 0)):
            q_type = st.selectbox(
                "문항 유형",
                options=['보기형', '추론형', '지시형', '동의형', '빈칸형', '내용일치형', '전개방식형', '어휘형'],
                key=f"dialog_q_type_{i}"
            )
            
            q_style = st.radio(
                "문항 스타일",
                options=['긍정형', '부정형'],
                key=f"dialog_q_style_{i}",
                horizontal=True
            )
            
            q_answer = st.selectbox(
                "정답",
                options=['①', '②', '③', '④', '⑤'],
                key=f"dialog_q_answer_{i}"
            )
            
            questions_input.append({
                "question_number": i + 1,
                "question_type": q_type,
                "question_style": q_style,
                "answer": q_answer
            })
    
    # 생성 시작 버튼
    if st.button("🚀 생성 시작", width="stretch", type="primary", key="dialog_submit"):
        # 설정 저장
        user_input_dict = {
            "field_input": field,
            "subfield_input": subfield,
            "type_input": type_input,
            "subject_input": subject,
            "points_input": points,
            "questions_input": questions_input
        }
        
        # 진행 상황 초기화
        num_questions = len(questions_input)
        st.session_state.progress_tasks = [
            {"label": "논리 구조 설계", "status": "pending"},
            {"label": "지문 생성", "status": "pending"},
        ]
        for i in range(num_questions):
            st.session_state.progress_tasks.append({
                "label": f"{i+1}번 문항 생성",
                "status": "pending"
            })
        
        # 다이얼로그 내부에서 진행 상황 표시
        with st.container(border=True):
            # st.markdown("#### 🔄 진행 현황")
            progress_container = st.empty()
        
        try:
            # SSE 스트림 수신
            with requests.post(
                f"{BACKEND_URL}/api/generate/stream",
                json={"user_input": user_input_dict},
                stream=True,
                timeout=600
            ) as response:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            
                            if data['type'] == 'progress':
                                step = data['step']
                                status = data['status']
                                
                                # 태스크 상태 업데이트
                                if step == 'card':
                                    label = '논리 구조 설계'
                                elif step == 'passage':
                                    label = '지문 생성'
                                elif step == 'question':
                                    q_num = data['question_number']
                                    label = f'{q_num}번 문항 생성'
                                
                                if status == 'start':
                                    for task in st.session_state.progress_tasks:
                                        if task['status'] == 'in_progress':
                                            task['status'] = 'complete'
                                    for task in st.session_state.progress_tasks:
                                        if task['label'] == label:
                                            task['status'] = 'in_progress'
                                            break
                                elif status == 'complete':
                                    for task in st.session_state.progress_tasks:
                                        if task['label'] == label:
                                            task['status'] = 'complete'
                                            break
                                
                                # 진행 상황 표시
                                with progress_container.container():
                                    render_progress_panel()
                            
                            elif data['type'] == 'complete':
                                st.session_state.generated_result = data['result']
                                for task in st.session_state.progress_tasks:
                                    task['status'] = 'complete'
                                with progress_container.container():
                                    render_progress_panel()
                            
                            elif data['type'] == 'error':
                                st.error(f"생성 중 오류: {data['message']}")
        
        except Exception as e:
            st.error(f"백엔드 서버와 연결할 수 없습니다: {str(e)}")
        
        # 완료 후 다이얼로그 닫기
        st.rerun()


# 로고 이미지 로드 및 base64 인코딩
logo_path = Path(__file__).parent / "logo_kangnam_202111.png"
if logo_path.exists():
    with open(logo_path, "rb") as f:
        img_bytes = f.read()
    img_base64 = base64.b64encode(img_bytes).decode()
else:
    img_base64 = ""

# 메인 레이아웃
# 2열 레이아웃 (좌측: 로그/입력, 우측: 결과)
col1, col2 = st.columns([1, 2], gap="medium")

# 좌측 컬럼
with col1:
    # 로고 + 타이틀
    with st.container(border=False, height=160):
        if img_base64:
            st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; align-items: center; margin-bottom: 10px;">
                <img src="data:image/png;base64,{img_base64}" 
                     style="width: 110px; height: auto; pointer-events: none; user-select: none; margin-right: 15px;" 
                     alt="강남대성수능연구소 로고">
                <div style="margin: 0; padding: 0; font-size: 40px; font-weight: 800; font-family: 'Nanum Myeongjo', serif;">
                    KSAT Agent
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.header("KSAT Agent")
        st.markdown('Model ver : KSAT-Pro-10-19 <br> Last updated : 2025.10.26 (beta) <br> Issue report : 권준희 (wnsgml9807@naver.com)', unsafe_allow_html=True)
    
    # Output 파일 불러오기 패널 (맨 위로)
    with st.container(border=True, height=600):
        st.markdown("#### 📁 저장된 결과")
        
        # 백엔드 API로부터 파일 목록 가져오기
        try:
            response = requests.get(f"{BACKEND_URL}/api/outputs", timeout=5)
            if response.status_code == 200:
                files_metadata = response.json().get('files', [])
                
                if files_metadata:
                    import pandas as pd
                    
                    # DataFrame 생성 (filename 제외)
                    df = pd.DataFrame(files_metadata)
                    display_df = df[['생성일자', '대분야', '주제', '문항 수']].copy()
                    
                    # 인덱스를 1부터 시작하도록 설정
                    display_df.index = range(1, len(display_df) + 1)
                    
                    # 데이터 테이블 표시
                    st.dataframe(
                        display_df,
                        width="stretch",
                        hide_index=False,
                        height=400
                    )
                    
                    # 행 선택 (라디오 버튼 또는 숫자 입력)
                    col_select, col_load = st.columns([3, 1])
                    
                    with col_select:
                        selected_idx = st.number_input(
                            "불러올 파일 번호",
                            min_value=1,
                            max_value=len(files_metadata),
                            value=1,
                            step=1,
                            label_visibility="collapsed"
                        )
                    
                    with col_load:
                        if st.button("불러오기", width="stretch"):
                            selected_file = files_metadata[selected_idx - 1]['filename']
                            try:
                                # 백엔드 API로부터 파일 내용 가져오기
                                file_response = requests.get(
                                    f"{BACKEND_URL}/api/outputs/{selected_file}",
                                    timeout=10
                                )
                                if file_response.status_code == 200:
                                    loaded_data = file_response.json()
                                    st.session_state.generated_result = loaded_data
                                    st.success(f"✅ 불러오기 완료!")
                                    st.rerun()
                                else:
                                    st.error(f"파일 불러오기 실패: {file_response.status_code}")
                            except Exception as e:
                                st.error(f"파일 불러오기 실패: {str(e)}")
                else:
                    st.info("저장된 결과 파일이 없습니다.")
            else:
                st.error(f"파일 목록 조회 실패: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.warning("백엔드 서버와 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        
        # 신규 생성 버튼 (패널 맨 아래)
        if st.button("➕ 신규 생성", width="stretch", type="primary", key="open_dialog"):
            show_generation_dialog()  # 다이얼로그 직접 호출

# 우측 컬럼: 결과 표시
with col2:
    with st.container(border=True, height=1500):
        if st.session_state.generated_result:
            result = st.session_state.generated_result
            
            # 주제 헤더 표시
            card = result.get('card', {})
            subject = card.get('subject', '생성된 지문')
            st.markdown(f"### {subject}")
            
            # 탭 생성
            tab1, tab2 = st.tabs(["📄 지문 & 문항", "💡 해설"])
            
            with tab1:
                # 지문 HTML 생성
                import re
                text = result['passage'].get('passage', result['passage'].get('content', result['passage'].get('passage_text', '')))
                
                # (가), (나) 분리형 지문 처리
                if re.search(r'^\s*\(가\)', text, re.MULTILINE):
                    parts = re.split(r'(\((?:가|나)\))', text)
                    passage_html = ""
                    for part in parts:
                        part = part.strip()
                        if not part:
                            continue
                        if part in ['(가)', '(나)']:
                            passage_html += f"<p class='section-label'>{part}</p>"
                        else:
                            paragraphs = [p.strip() for p in part.split("\n") if p.strip()]
                            passage_html += "".join(f"<p>{p}</p>" for p in paragraphs)
                else:
                    # 일반 지문
                    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
                    passage_html = "".join(f"<p>{p}</p>" for p in paragraphs)
                
                passage_html = f"<div class='passage-font'>{passage_html}</div>"
                
                # 문항 HTML 생성
                questions_html = render_questions(result['questions'])
                
                # 지문+문항 통합 HTML
                combined_html = f"""
                <div class="content-wrapper">
                    <div class="content-container">
                        <div class="passage-section">
                            {passage_html}
                        </div>
                        <div class="questions-section">
                            {questions_html}
                        </div>
                    </div>
                </div>
                """
                
                st.markdown(combined_html, unsafe_allow_html=True)
            
            with tab2:
                # 해설 표시
                render_explanations(result['questions'])
        
        else:
            st.info("좌측 패널에서 결과물을 선택하거나, 신규 생성 버튼을 클릭하세요. 지문과 문항이 표시되는 부분입니다.")

