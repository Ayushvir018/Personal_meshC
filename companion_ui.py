"""
companion_ui.py — High-Quality Lottie Avatar Controller for Personal Mesh
Manages the Billaa (cat) companion avatar using Lottie animations.
"""

import streamlit as st
import json
import os
from streamlit_lottie import st_lottie
from typing import Literal

AvatarState = Literal["idle", "thinking", "talking"]

# ── Lottie File Paths ────────────────────────────────────────────────────────
LOTTIE_PATHS = {
    "idle":     "lottie_idle.json/Le Petit Chat _Cat_ Noir.json",
    "talking":  "lottie_talking.json/black rainbow cat.json",
    "thinking": "lottie_thinking.json/cat.json",
}

# ── State visual config (Colors & Labels) ────────────────────────────────────
_STATE_CONFIG = {
    "idle": {
        "label": "ONLINE",
        "color": "#00d4aa",
        "glow":  "rgba(0,212,170,0.45)",
    },
    "thinking": {
        "label": "THINKING...",
        "color": "#ffaa00",
        "glow":  "rgba(255,170,0,0.55)",
    },
    "talking": {
        "label": "SPEAKING",
        "color": "#0088ff",
        "glow":  "rgba(0,136,255,0.60)",
    },
}

@st.cache_data
def load_lottie_file(filepath: str):
    """Load a Lottie JSON file from the local filesystem."""
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading Lottie: {e}")
    return None

def inject_avatar_css():
    """
    Inject core status and layout CSS for the companion.
    Now simpler as Lottie handles most of the animation.
    """
    st.markdown("""
<style>
.billaa-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.8rem;
    user-select: none;
    padding: 10px;
    position: sticky;
    top: 2rem;
    z-index: 10;
}

.billaa-container {
    position: relative;
    width: 140px;
    height: 140px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.5s ease;
}
.billaa-status {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    font-weight: 600;
}
.billaa-status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 8px;
    transition: background-color 0.5s ease;
}
</style>
""", unsafe_allow_html=True)

def render_billaa(state: AvatarState = "idle", key: str = "main") -> None:
    """
    Render high-quality Lottie animation for the companion.
    """
    inject_avatar_css()
    cfg = _STATE_CONFIG.get(state, _STATE_CONFIG["idle"])
    
    # Load correct Lottie JSON
    lottie_json = load_lottie_file(LOTTIE_PATHS.get(state, LOTTIE_PATHS["idle"]))
    
    # Wrapper and Container with dynamic glow
    st.markdown(f'''
    <div class="billaa-wrapper">
        <div class="billaa-container" style="box-shadow: 0 0 25px {cfg['glow']}; background: rgba(0,0,0,0.1);">
    ''', unsafe_allow_html=True)
    
    # Render Lottie
    if lottie_json:
        st_lottie(
            lottie_json,
            speed=1,
            reverse=False,
            loop=True,
            quality="high",
            height=130,
            width=130,
            key=f"lottie-{state}-{key}"
        )
    else:
        st.markdown('<div style="font-size:4rem;">🐱</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True) # End of container
    
    # Status bar below
    st.markdown(f'''
        <div class="billaa-status" style="color:{cfg["color"]};">
            <span class="billaa-status-dot" style="background:{cfg["color"]}; box-shadow: 0 0 8px {cfg["color"]};"></span>
            {cfg["label"]}
        </div>
    </div>
    ''', unsafe_allow_html=True)
