import streamlit as st
import pandas as pd
from datetime import datetime
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.engine import DiagnosticEngine

# Initialize Theme State
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Initialize Console Status
if "console_status" not in st.session_state:
    st.session_state.console_status = "READY"

def toggle_theme():
    st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

IS_DARK = st.session_state.theme == "dark"

# Set Page Config
st.set_page_config(
    page_title="NetSage AI: Operations Gateway",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Injection for 10/10 SaaS-grade Zinc Design System
css = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap');

:root {{
    --bg: {"#09090b" if IS_DARK else "#ffffff"};
    --bg-subtle: {"#0c0c0f" if IS_DARK else "#f9fafb"};
    --card: {"#0c0c0f" if IS_DARK else "#ffffff"};
    --card-hover: {"#131316" if IS_DARK else "#f4f4f5"};
    --border: {"#1e1e24" if IS_DARK else "#e4e4e7"};
    --border-subtle: {"#16161a" if IS_DARK else "#f0f0f2"};
    --text: {"#fafafa" if IS_DARK else "#09090b"};
    --text-muted: #71717a;
    --text-dim: {"#52525b" if IS_DARK else "#a1a1aa"};
    --accent: #2563eb;
    --accent-muted: #1d4ed8;
    --green: {"#22c55e" if IS_DARK else "#16a34a"};
    --green-muted: {"rgba(34,197,94,0.12)" if IS_DARK else "rgba(22,163,74,0.08)"};
    --red: {"#ef4444" if IS_DARK else "#dc2626"};
    --red-muted: {"rgba(239,68,68,0.12)" if IS_DARK else "rgba(220,38,38,0.08)"};
    --amber: {"#f59e0b" if IS_DARK else "#d97706"};
    --amber-muted: {"rgba(245,158,11,0.12)" if IS_DARK else "rgba(217,119,6,0.08)"};
    --shadow: {"none" if IS_DARK else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"};
    --radius: 12px;
}}

/* Hide Default Streamlit Chrome */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton {{
    display: none !important;
}}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}

.block-container {{
    padding: 1.5rem 2rem 2.5rem !important;
    max-width: 1360px !important;
}}

/* Sidebar Styling */
section[data-testid="stSidebar"] {{
    background-color: var(--bg-subtle) !important;
    border-right: 1px solid var(--border) !important;
}}

/* Streamlit Native Buttons Customization */
div.stButton > button {{
    background-color: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: var(--shadow) !important;
    width: 100%;
}}
div.stButton > button:hover {{
    background-color: var(--card-hover) !important;
    border-color: var(--text-muted) !important;
    transform: translateY(-1px) !important;
}}
div.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* Highlight Primary buttons */
div.stButton > button[data-testid="baseButton-primary"] {{
    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-muted) 100%) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}}
div.stButton > button[data-testid="baseButton-primary"]:hover {{
    box-shadow: 0 4px 12px rgba(37,99,235,0.3) !important;
    transform: translateY(-1px) !important;
}}

/* Custom Tabs Layout */
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.2rem !important;
    border: 1px solid transparent !important;
    border-radius: 8px !important;
    transition: all 0.2s ease-in-out !important;
    margin-right: 4px !important;
}}
button[data-baseweb="tab"]:hover {{
    color: var(--text) !important;
    background: var(--card-hover) !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--text) !important;
    background: var(--card) !important;
    border-color: var(--border) !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-baseweb="tab-list"] {{
    gap: 4px !important;
    background: var(--bg-subtle) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 4px;
    margin-bottom: 1.5rem !important;
}}

/* Custom Card Layout */
.zinc-card {{
    background-color: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1.25rem 1.5rem !important;
    box-shadow: var(--shadow) !important;
    margin-bottom: 1.25rem !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}}
.zinc-card:hover {{
    border-color: var(--text-dim) !important;
    transform: translateY(-1px) !important;
}}

/* Pulsing Status Bar Animation */
@keyframes pulse-status {{
    0% {{ opacity: 1; }}
    50% {{ opacity: 0.6; }}
    100% {{ opacity: 1; }}
}}
.pulse-indicator {{
    animation: pulse-status 2s infinite ease-in-out;
}}

/* KPI Metric Cards */
.metric-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem 1.4rem;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    height: 100%;
    transition: transform 0.2s;
}}
.metric-card:hover {{
    transform: translateY(-2px);
}}
.metric-label {{
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 600;
    margin-bottom: 0.35rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.metric-value {{
    font-size: 1.95rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.03em;
    line-height: 1;
}}
.metric-delta {{
    font-size: 0.72rem;
    font-weight: 500;
    margin-top: 0.5rem;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    gap: 3px;
    width: fit-content;
}}
.delta-up {{ color: var(--green); background: var(--green-muted); }}
.delta-down {{ color: var(--red); background: var(--red-muted); }}
.delta-warn {{ color: var(--amber); background: var(--amber-muted); }}

/* Circular Conic Gauge Chart */
.gauge-container {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1rem;
}}
.gauge-circle {{
    position: relative;
    width: 140px;
    height: 140px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow);
}}
.gauge-inner {{
    width: 110px;
    height: 110px;
    border-radius: 50%;
    background-color: var(--card);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.06);
}}

/* Custom Tables */
.data-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.82rem;
    margin-top: 0.5rem;
}}
.data-table th {{
    text-align: left;
    padding: 0.75rem 1rem;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid var(--border);
    background-color: var(--bg-subtle);
}}
.data-table td {{
    padding: 0.75rem 1rem;
    color: var(--text);
    border-bottom: 1px solid var(--border-subtle);
    font-family: 'DM Sans', sans-serif;
}}
.data-table tr:last-child td {{
    border-bottom: none;
}}
.data-table tr:hover td {{
    background-color: var(--card-hover);
}}

/* Custom Status Badges */
.badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}}
.badge-high {{ color: var(--red); background: var(--red-muted); }}
.badge-medium {{ color: var(--amber); background: var(--amber-muted); }}
.badge-low {{ color: var(--accent); background: rgba(37, 99, 235, 0.1); }}
.badge-layer {{ color: var(--accent); background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.2); }}

.badge-approved {{ color: var(--green); background: var(--green-muted); }}
.badge-edited {{ color: var(--amber); background: var(--amber-muted); }}
.badge-rejected {{ color: var(--red); background: var(--red-muted); }}

.badge-ready {{ color: var(--accent); background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.3); }}
.badge-pending {{ color: var(--amber); background: var(--amber-muted); border: 1px solid rgba(245, 158, 11, 0.3); }}
.badge-done {{ color: var(--green); background: var(--green-muted); border: 1px solid rgba(34, 197, 94, 0.3); }}

/* Code blocks */
code, pre {{
    font-family: 'JetBrains Mono', monospace !important;
}}

[data-testid="stHorizontalBlock"] {{
    gap: 1.25rem !important;
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# Helper function to render a KPI metric card
def render_metric_card(label, value, delta=None, delta_type="up"):
    cls = f"delta-{delta_type}"
    arrow = "↑" if delta_type == "up" else ("↓" if delta_type == "down" else "→")
    delta_html = f'<div class="metric-delta {cls}">{arrow} {delta}</div>' if delta else ""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

# Load cases.csv dataset
@st.cache_data
def load_data():
    cases_path = Path("data/cases.csv")
    if cases_path.exists():
        try:
            return pd.read_csv(cases_path)
        except Exception as e:
            st.error(f"Error loading CSV data: {e}")
    return pd.DataFrame()

# Audit Log Parser & Metrics Calculator
def parse_audit_log():
    log_path = Path("docs/model_audit_log.md")
    if not log_path.exists():
        # Initialize default log file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("# Model Audit Log\n\nThis document tracks the agreement metrics and edge cases requiring human override.\n\n| Timestamp | Case ID | Model Diagnosis | Human Override | Final Action | Reason for Override |\n| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        return [], {"total": 0, "approved": 0, "edited": 0, "rejected": 0, "rate": 76.6}
        
    entries = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in lines:
            if "|" in line:
                if "Timestamp" in line or ":---" in line or line.strip() == "":
                    continue
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 5 and parts[0]:
                    entries.append({
                        "timestamp": parts[0],
                        "case_id": parts[1],
                        "diagnosis": parts[2],
                        "override": parts[3],
                        "action": parts[4],
                        "reason": parts[5] if len(parts) > 5 else ""
                    })
    except Exception as e:
        st.error(f"Error reading audit log: {e}")
        
    total = len(entries)
    approved = sum(1 for e in entries if "Approved" in e["action"])
    edited = sum(1 for e in entries if "Edited" in e["action"])
    rejected = sum(1 for e in entries if "Rejected" in e["action"])
    
    rate = (approved / total * 100) if total > 0 else 76.6
    
    return entries, {
        "total": total,
        "approved": approved,
        "edited": edited,
        "rejected": rejected,
        "rate": round(rate, 1)
    }

# Logger to append and rewrite docs/model_audit_log.md
def log_audit(case_id, diagnosis, override, action, reason):
    log_path = Path("docs/model_audit_log.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    diagnosis_str = diagnosis.get("root_cause", "").replace("\n", " ").replace("|", "\\|")
    override_str = "Yes" if override else "No"
    reason_str = reason.replace("\n", " ").replace("|", "\\|") if reason else "N/A"
    
    new_entry = {
        "timestamp": timestamp,
        "case_id": case_id,
        "diagnosis": diagnosis_str,
        "override": override_str,
        "action": action,
        "reason": reason_str
    }
    
    # Read existing entries
    entries, _ = parse_audit_log()
    
    # Check if case_id already logged, if so, we just append a new log entry
    entries.append(new_entry)
    
    # Recalculate metrics
    total = len(entries)
    approved = sum(1 for e in entries if "Approved" in e["action"])
    edited = sum(1 for e in entries if "Edited" in e["action"])
    rejected = sum(1 for e in entries if "Rejected" in e["action"])
    rate = round((approved / total * 100), 1) if total > 0 else 76.6
    
    # Rewrite file
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("# Model Audit Log\n\n")
            f.write("This document tracks the agreement metrics and edge cases requiring human override.\n\n")
            f.write("| Timestamp | Case ID | Model Diagnosis | Human Override | Final Action | Reason for Override |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for e in entries:
                f.write(f"| {e['timestamp']} | {e['case_id']} | {e['diagnosis']} | {e['override']} | {e['action']} | {e['reason']} |\n")
                
            f.write("\n## Agreement Metrics\n")
            f.write(f"*   **Total Cases:** {total}\n")
            f.write(f"*   **Approved As-Is:** {approved}\n")
            f.write(f"*   **Edited Commands:** {edited}\n")
            f.write(f"*   **Rejected (False Positive):** {rejected}\n")
            f.write(f"*   **Overall Agreement Rate:** {rate}% (baseline metric from architecture: 76.6%)\n")
    except Exception as e:
        st.error(f"Error writing to audit log: {e}")

def main():
    # Brand Header / Logo
    head_left, head_right = st.columns([9, 1.2])
    with head_left:
        st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 5px;">
            <span style="font-size: 1.5rem; color: #2563eb; font-weight: 700;">◆</span>
            <span style="font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em;">NetSage AI</span>
            <span style="font-size: 0.72rem; background: rgba(37,99,235,0.08); color: #2563eb; font-weight: 600; padding: 2px 7px; border-radius: 6px; border: 1px solid rgba(37,99,235,0.2);">OPERATIONS GATEWAY</span>
        </div>
        """, unsafe_allow_html=True)
    with head_right:
        theme_label = "☀️ Light Mode" if IS_DARK else "🌙 Dark Mode"
        st.button(theme_label, on_click=toggle_theme, use_container_width=True)
        
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Load case database
    df = load_data()
    if df.empty:
        st.warning("No cases found in data/cases.csv. Please populate the cases file.")
        return
        
    # Read current logs
    log_entries, metrics = parse_audit_log()
    
    # Navigation Tabs
    tab1, tab2, tab3 = st.tabs(["Active Diagnostic Case", "Performance Metrics & Analytics", "Audit History Log"])
    
    # SIDEBAR: Case Selector
    st.sidebar.markdown("""
    <div style='margin-bottom: 0.5rem;'>
        <h4 style='margin: 0; font-weight: 600;'>Network Cases Database</h4>
        <p style='margin: 0; font-size: 0.72rem; color: #71717a;'>Select an active Packet Tracer scenario</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Severity filtering in sidebar
    severity_filter = st.sidebar.multiselect("Filter Severity", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
    concept_filter = st.sidebar.multiselect("Filter Concept", sorted(df['concept_tag'].unique().tolist()), default=df['concept_tag'].unique().tolist())
    
    filtered_df = df[df['severity'].isin(severity_filter) & df['concept_tag'].isin(concept_filter)]
    
    if filtered_df.empty:
        st.sidebar.warning("No cases match the filters.")
        selected_case_id = st.sidebar.selectbox("Select Case ID (All)", df['case_id'].tolist())
        case_data = df[df['case_id'] == selected_case_id].iloc[0]
    else:
        selected_case_id = st.sidebar.selectbox("Select Case ID", filtered_df['case_id'].tolist())
        case_data = filtered_df[filtered_df['case_id'] == selected_case_id].iloc[0]
        
    show_outputs_fmt = str(case_data['show_outputs']).replace('\\n', '\n')
    
    # Reset console status if we change case ID
    if "current_case_id" in st.session_state and st.session_state.current_case_id != case_data['case_id']:
        st.session_state.console_status = "READY"
        
    # ==================== TAB 1: ACTIVE DIAGNOSTIC CASE ====================
    with tab1:
        st.markdown(f"### Diagnostic Workspace &mdash; {selected_case_id}")
        
        # Grid layout: Case details on left, Show command output on right
        col_detail, col_output = st.columns([1, 1])
        
        with col_detail:
            # Active Status Bar with Pulsing Indicator
            status_text = st.session_state.console_status
            status_badge_map = {
                "READY": ("badge-ready", ""),
                "ANALYZING": ("badge-pending pulse-indicator", "pulse"),
                "PENDING REVIEW": ("badge-pending pulse-indicator", "pulse"),
                "REMEDIATION APPROVED": ("badge-done", ""),
                "OVERRIDE DEPLOYED": ("badge-done", ""),
                "REJECTED FALSE POSITIVE": ("badge-rejected", "")
            }
            badge_class, pulse_class = status_badge_map.get(status_text, ("badge-ready", ""))
            
            st.markdown(f"""
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0.75rem; background: var(--bg-subtle); border: 1px solid var(--border); border-radius: 8px; margin-bottom: 1rem;">
                <div style="font-size: 0.72rem; font-weight: 600; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em;">Console State</div>
                <span class="badge {badge_class}">{status_text}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Case details card with dynamic top border color based on Severity
            severity_color = "var(--red)" if case_data['severity'] == "High" else ("var(--amber)" if case_data['severity'] == "Medium" else "var(--accent)")
            severity_class = f"badge-{case_data['severity'].lower()}"
            st.markdown(f"""
            <div class="zinc-card" style="border-top: 4px solid {severity_color} !important;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
                    <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase;">Scenario Metadata</div>
                    <span class="badge {severity_class}">{case_data['severity']} Severity</span>
                </div>
                <h4 style="margin: 0 0 0.5rem 0; font-weight: 600; font-size: 1.15rem; line-height: 1.3;">{case_data['symptom']}</h4>
                <div style="margin-top: 1rem; display: flex; flex-wrap: wrap; gap: 8px;">
                    <span class="badge badge-layer">Concept: {case_data['concept_tag']}</span>
                    <span class="badge badge-layer">Topology: {case_data['topology_note']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action Launcher Card
            st.markdown("""
            <div class="zinc-card">
                <h5 style="margin: 0 0 0.5rem 0; font-weight: 600; font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.03em;">Diagnostics Launcher</h5>
                <p style="margin: 0 0 1rem 0; font-size: 0.78rem; color: var(--text-muted); line-height: 1.4;">Execute static checks and LLM orchestration to determine root cause and evidence.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Run diagnostics button (outside HTML card)
            if st.button("Run Diagnostics", type="primary", use_container_width=True):
                st.session_state.console_status = "ANALYZING"
                with st.spinner("Analyzing network states and configurations..."):
                    engine = DiagnosticEngine()
                    diagnosis = engine.run_diagnostics(
                        symptom=case_data['symptom'],
                        topology_note=case_data['topology_note'],
                        show_outputs=show_outputs_fmt,
                        case_id=case_data['case_id']
                    )
                    st.session_state['current_diagnosis'] = diagnosis
                    st.session_state['current_case_id'] = case_data['case_id']
                    st.session_state.console_status = "PENDING REVIEW"
                st.rerun()
            
        with col_output:
            # Code outputs card
            st.markdown(f"""
            <div class="zinc-card" style="height: 100%; display: flex; flex-direction: column;">
                <div style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; margin-bottom: 0.75rem;">Captured IOS CLI Outputs</div>
                <div style="flex-grow: 1;">
            """, unsafe_allow_html=True)
            st.code(show_outputs_fmt, language="bash")
            st.markdown("</div></div>", unsafe_allow_html=True)
            
        # Diagnosis Results and HITL Gate
        if 'current_diagnosis' in st.session_state and st.session_state.get('current_case_id') == case_data['case_id']:
            st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("### Diagnostic Assessment & HITL Gate")
            
            diag = st.session_state['current_diagnosis']
            
            col_res, col_hitl = st.columns([1.1, 0.9])
            
            with col_res:
                # Diagnosis summary card with left border colored by confidence level
                confidence_val = diag.get("confidence", 0.85)
                confidence_percent = int(confidence_val * 100)
                
                # Check confidence status colors
                progress_color = "var(--green)" if confidence_val >= 0.9 else ("var(--amber)" if confidence_val >= 0.8 else "var(--red)")
                conf_cls = "badge-green" if confidence_val >= 0.9 else ("badge-amber" if confidence_val >= 0.8 else "badge-red")
                
                st.markdown(f"""
                <div class="zinc-card" style="border-left: 4px solid {progress_color} !important;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h4 style="margin: 0; font-weight: 600; font-size: 1.05rem;">Automated Fault Analysis</h4>
                        <div>
                            <span class="badge {conf_cls}" style="margin-right: 5px;">{confidence_percent}% Confidence</span>
                            <span class="badge badge-layer">{diag.get("osi_layer", "Layer 3")}</span>
                        </div>
                    </div>
                    
                    <!-- Confidence Progress Bar -->
                    <div style="margin-bottom: 1.25rem;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">
                            <span>Diagnostic Certainty</span>
                            <span>{confidence_percent}%</span>
                        </div>
                        <div style="margin-top: 0.35rem; background-color: var(--border-subtle); border-radius: 6px; height: 8px; width: 100%; overflow: hidden;">
                            <div style="background-color: {progress_color}; height: 100%; width: {confidence_percent}%; border-radius: 6px;"></div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Diagnosed Root Cause</div>
                        <div style="font-size: 0.95rem; font-weight: 500; margin-top: 0.25rem; line-height: 1.45;">{diag.get("root_cause", "No root cause identified.")}</div>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Diagnostic Evidence Highlight</div>
                        <div style="font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; background-color: var(--bg-subtle); border-left: 3px solid var(--accent); padding: 0.55rem 0.75rem; border-radius: 6px; margin-top: 0.35rem; white-space: pre-wrap; line-height: 1.4;">{diag.get("evidence", "No explicit evidence highlighted.")}</div>
                    </div>
                    
                    <div>
                        <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase;">Recommended Next Command</div>
                        <div style="font-size: 0.82rem; font-family: 'JetBrains Mono', monospace; background-color: var(--bg-subtle); padding: 0.5rem 0.75rem; border-radius: 6px; margin-top: 0.35rem;">{diag.get("next_command", "show running-config")}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_hitl:
                # Remediation deployment card
                st.markdown(f"""
                <div class="zinc-card">
                    <h4 style="margin: 0 0 1rem 0; font-weight: 600; font-size: 1.05rem;">Human-in-the-Loop Verification</h4>
                    <div style="font-size: 0.7rem; color: var(--text-muted); font-weight: 600; text-transform: uppercase; margin-bottom: 0.5rem;">Proposed Remediation Commands</div>
                """, unsafe_allow_html=True)
                
                # Show proposed commands in a clean list
                fix_steps = diag.get("fix_steps", [])
                if fix_steps:
                    st.code("\n".join(fix_steps), language="bash")
                else:
                    st.markdown("<p style='font-size: 0.8rem; color: var(--text-muted); font-style: italic;'>No remediation commands provided.</p>", unsafe_allow_html=True)
                
                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                
                # HITL Controls
                col_h1, col_h2, col_h3 = st.columns(3)
                
                with col_h1:
                    if st.button("Approve & Deploy", key="approve_deploy", use_container_width=True):
                        log_audit(
                            case_id=case_data['case_id'],
                            diagnosis=diag,
                            override=False,
                            action="Approved As-Is",
                            reason="Operator verified diagnosis and verified CLI steps as correct."
                        )
                        st.session_state.console_status = "REMEDIATION APPROVED"
                        st.success("Remediation Approved and Logged!")
                        st.rerun()
                        
                with col_h2:
                    with st.popover("Edit Commands", use_container_width=True):
                        st.markdown("<div style='margin-bottom: 0.5rem;'><strong>Edit CLI Remediations</strong></div>", unsafe_allow_html=True)
                        edited_txt = st.text_area("Modified commands (one per line)", value="\n".join(fix_steps), height=150)
                        edit_reason = st.text_input("Reason for editing configuration", placeholder="e.g. Added correct VLAN tag")
                        if st.button("Deploy Edited", key="submit_edit"):
                            if not edit_reason:
                                st.warning("Please provide a reason for overriding.")
                            else:
                                candidate_steps = [line.strip() for line in edited_txt.split("\n") if line.strip()]
                                is_safe, warnings = engine.safety_validator.validate_fix_steps(candidate_steps)
                                if not is_safe:
                                    st.error("🚨 SAFETY GATE TRIGGERED: " + " ".join(warnings))
                                else:
                                    # Construct updated diagnosis dict for logging
                                    updated_diag = diag.copy()
                                    updated_diag["fix_steps"] = candidate_steps
                                    log_audit(
                                        case_id=case_data['case_id'],
                                        diagnosis=updated_diag,
                                        override=True,
                                        action="Edited Commands",
                                        reason=f"Operator override: {edit_reason}"
                                    )
                                    st.session_state.console_status = "OVERRIDE DEPLOYED"
                                    st.success("Override Deployed & Logged!")
                                    st.rerun()
                                
                with col_h3:
                    with st.popover("Reject Diagnosis", use_container_width=True):
                        st.markdown("<div style='margin-bottom: 0.5rem;'><strong>Reject Assessment</strong></div>", unsafe_allow_html=True)
                        reject_reason = st.text_input("Reason for rejection", placeholder="e.g. Model hallucinated native VLAN")
                        if st.button("Confirm Reject", key="submit_reject"):
                            if not reject_reason:
                                st.warning("Please provide a reason for rejection.")
                            else:
                                log_audit(
                                    case_id=case_data['case_id'],
                                    diagnosis=diag,
                                    override=True,
                                    action="Rejected (False Positive)",
                                    reason=f"Rejection: {reject_reason}"
                                )
                                st.session_state.console_status = "REJECTED FALSE POSITIVE"
                                st.error("Assessment Rejected & Logged!")
                                st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
                
    # ==================== TAB 2: PERFORMANCE METRICS ====================
    with tab2:
        st.markdown("### Diagnostic Performance & Metrics")
        
        # Row 1: KPI Cards
        # Render dynamic metrics from audit log
        agree_rate = metrics["rate"]
        baseline_rate = 76.6
        diff = round(agree_rate - baseline_rate, 1)
        delta_str = f"{'+' if diff >= 0 else ''}{diff}% vs baseline"
        delta_type = "up" if diff >= 0 else "down"
        
        col_kpis, col_gauge = st.columns([3.5, 1.5])
        
        with col_kpis:
            kpi1, kpi2 = st.columns(2)
            with kpi1:
                st.markdown(render_metric_card("Total Diagnoses Run", metrics["total"]), unsafe_allow_html=True)
                st.markdown(render_metric_card("Approved As-Is", metrics["approved"]), unsafe_allow_html=True)
            with kpi2:
                st.markdown(render_metric_card("Edited Commands", metrics["edited"]), unsafe_allow_html=True)
                st.markdown(render_metric_card("Rejected Cases", metrics["rejected"]), unsafe_allow_html=True)
                
        with col_gauge:
            # 10/10 Premium visual UI custom circular gauge in pure CSS conic-gradient
            gauge_border_color = "var(--green)" if agree_rate >= 76.6 else "var(--amber)"
            st.markdown(f"""
            <div class="zinc-card gauge-container">
                <div class="metric-label" style="margin-bottom: 0.75rem;">Operator Agreement Rate</div>
                <div class="gauge-circle" style="background: conic-gradient({gauge_border_color} {agree_rate}%, var(--border-subtle) 0);">
                    <div class="gauge-inner">
                        <span style="font-size: 1.65rem; font-weight: 800; color: var(--text);">{agree_rate}%</span>
                        <span style="font-size: 0.65rem; color: var(--text-muted); font-weight: 500; margin-top: 2px;">Baseline: {baseline_rate}%</span>
                    </div>
                </div>
                <div class="metric-delta delta-{delta_type}" style="margin-top: 0.75rem;">
                    {"↑" if delta_type == "up" else "↓"} {delta_str}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Row 2: Charts (OSI layer breakdown and Severity Breakdown)
        col_chart1, col_chart2 = st.columns(2)
        
        # Safe plotting with Plotly if installed, else fallback to native streamlit
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            
            plotly_available = True
        except ImportError:
            plotly_available = False
            
        with col_chart1:
            st.markdown("""
            <div class="chart-wrap" style="background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; box-shadow: var(--shadow);">
                <div class="chart-title" style="font-size: 0.85rem; font-weight: 600;">OSI Layers Distribution</div>
                <div class="chart-subtitle" style="font-size: 0.72rem; color: var(--text-dim); margin-bottom: 0.8rem;">Breakdown of diagnostics across OSI Layers</div>
            """, unsafe_allow_html=True)
            
            # Aggregate OSI Layers from cases dataset
            osi_counts = df['concept_tag'].value_counts().reset_index()
            # Simple layer mapping for visualization
            osi_mapping = {
                "Routing": "Layer 3 (Network)",
                "VLAN": "Layer 2 (Data Link)",
                "NAT": "Layer 3 (Network)",
                "OSPF": "Layer 3 (Network)",
                "Trunking": "Layer 2 (Data Link)",
                "EtherChannel": "Layer 2 (Data Link)",
                "ACL": "Layer 3 (Network)",
                "EIGRP": "Layer 3 (Network)",
                "DHCP": "Layer 3 (Network)",
                "HSRP": "Layer 3 (Network)",
                "STP": "Layer 2 (Data Link)",
                "BGP": "Layer 3 (Network)",
                "Security": "Layer 7 (Application)"
            }
            df_osi = df.copy()
            df_osi['osi_layer'] = df_osi['concept_tag'].map(osi_mapping)
            osi_dist = df_osi['osi_layer'].value_counts().reset_index()
            osi_dist.columns = ['OSI Layer', 'Count']
            
            if plotly_available:
                fig_osi = px.bar(
                    osi_dist, 
                    x='Count', 
                    y='OSI Layer', 
                    orientation='h',
                    color='OSI Layer',
                    color_discrete_sequence=['#2563eb', '#16a34a', '#d97706', '#dc2626']
                )
                
                # Apply theme-aware layout
                font_color = "#fafafa" if IS_DARK else "#09090b"
                grid_color = "rgba(255,255,255,0.08)" if IS_DARK else "rgba(0,0,0,0.06)"
                
                fig_osi.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="DM Sans, sans-serif", color=font_color, size=11),
                    margin=dict(l=0, r=0, t=10, b=0),
                    showlegend=False,
                    xaxis=dict(gridcolor=grid_color, zerolinecolor=grid_color),
                    yaxis=dict(gridcolor="rgba(0,0,0,0)", zerolinecolor="rgba(0,0,0,0)")
                )
                st.plotly_chart(fig_osi, use_container_width=True, config={"displayModeBar": False})
            else:
                # Streamlit Native Fallback
                st.bar_chart(osi_dist.set_index('OSI Layer'))
                
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_chart2:
            st.markdown("""
            <div class="chart-wrap" style="background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; box-shadow: var(--shadow);">
                <div class="chart-title" style="font-size: 0.85rem; font-weight: 600;">Case Severity Distribution</div>
                <div class="chart-subtitle" style="font-size: 0.72rem; color: var(--text-dim); margin-bottom: 0.8rem;">Proportion of High, Medium, and Low severity cases</div>
            """, unsafe_allow_html=True)
            
            sev_counts = df['severity'].value_counts().reset_index()
            sev_counts.columns = ['Severity', 'Count']
            
            if plotly_available:
                fig_sev = px.pie(
                    sev_counts, 
                    values='Count', 
                    names='Severity',
                    hole=0.45,
                    color='Severity',
                    color_discrete_map={'High': '#ef4444', 'Medium': '#f59e0b', 'Low': '#2563eb'}
                )
                
                font_color = "#fafafa" if IS_DARK else "#09090b"
                fig_sev.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="DM Sans, sans-serif", color=font_color, size=11),
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_sev, use_container_width=True, config={"displayModeBar": False})
            else:
                # Streamlit Native Fallback
                st.bar_chart(sev_counts.set_index('Severity'))
                
            st.markdown("</div>", unsafe_allow_html=True)
            
    # ==================== TAB 3: AUDIT HISTORY LOG ====================
    with tab3:
        st.markdown("### Operator Deployment Audit Logs")
        
        # Search & Filter controls
        col_sf1, col_sf2 = st.columns([1.5, 1])
        with col_sf1:
            search_query = st.text_input("🔍 Search logs by Case ID or Diagnosis content", placeholder="Enter query (e.g. NET-001 or VLAN)")
        with col_sf2:
            action_filter = st.selectbox("Filter by Operator Action", ["All Actions", "Approved As-Is", "Edited Commands", "Rejected (False Positive)"])
            
        # Display Logs Table
        if not log_entries:
            st.info("No audit events have been logged yet. Launch diagnostics and approve/reject steps in the first tab to build history.")
        else:
            # Filter entries
            filtered_entries = log_entries
            if search_query:
                q = search_query.lower()
                filtered_entries = [e for e in filtered_entries if q in e["case_id"].lower() or q in e["diagnosis"].lower() or q in e["reason"].lower()]
            if action_filter != "All Actions":
                filtered_entries = [e for e in filtered_entries if action_filter in e["action"]]
                
            if not filtered_entries:
                st.warning("No audit logs match your search filters.")
            else:
                # Render beautiful custom HTML table
                table_rows = ""
                for e in filtered_entries:
                    badge_cls = "badge-approved" if "Approved" in e["action"] else ("badge-edited" if "Edited" in e["action"] else "badge-rejected")
                    
                    table_rows += f"""
                    <tr>
                        <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--text-dim);">{e['timestamp']}</td>
                        <td style="font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--accent);">{e['case_id']}</td>
                        <td style="line-height: 1.35;">{e['diagnosis']}</td>
                        <td>{e['override']}</td>
                        <td><span class="badge {badge_cls}">{e['action']}</span></td>
                        <td style="font-style: italic; color: var(--text-dim);">{e['reason']}</td>
                    </tr>
                    """
                    
                table_html = f"""
                <div class="zinc-card" style="padding: 0; overflow-x: auto; border-radius: var(--radius);">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Case ID</th>
                                <th>Model Diagnosis</th>
                                <th>Override</th>
                                <th>Action Taken</th>
                                <th>Operator Notes / Reason</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                </div>
                """
                st.markdown(table_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
