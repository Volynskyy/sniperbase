import os
import streamlit as st
import requests
from web3 import Web3
import plotly.graph_objs as go
import pandas as pd
from datetime import datetime

# === SETUP ===
ETHERSCAN_API_KEY = "XSUUHZ6HN6ED625QCRD6DK2UBFBKT65G"
rpc_url = "https://eth.llamarpc.com"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# === PAGE CONFIG ===
st.set_page_config(page_title="SniperBase", layout="wide")

# === STYLES ===
st.markdown("""
    <style>
        body {
            background-color: #000000;
            color: #f0f0f0;
        }
        .block-container {
            padding-top: 2rem;
        }
        .stTextInput>div>div>input {
            background-color: #1c1c1c;
            color: #f0f0f0;
            border: 1px solid #f0b90b;
        }
        .stMetric {
            background-color: #1c1c1c;
            border-radius: 10px;
            padding: 12px;
            color: #f0b90b;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #f0b90b;
        }
        .stAlert, .stError, .stSuccess {
            border-radius: 8px;
        }
        .stMarkdown a {
            color: #f0b90b;
        }
    </style>
""", unsafe_allow_html=True)

# === TITLE ===
st.title("🚀 SniperBase")
st.markdown("Аналітика токенів: контракт, ліквідність, холдери, графік і анти-бот перевірка.")

# === TOKEN INPUT ===
token_address = st.text_input("🔍 Введи адресу контракту ERC-20 токена:")

erc20_abi = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

if token_address:
    try:
        contract = web3.eth.contract(address=web3.to_checksum_address(token_address), abi=erc20_abi)
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        total_supply = contract.functions.totalSupply().call() / (10 ** decimals)

        st.success(f"🪙 **Назва токена:** {name}")
        st.success(f"💱 **Символ:** {symbol}")
        st.info(f"🔢 **Деcимали:** {decimals}")
        st.info(f"📦 **Загальна емісія:** {total_supply:,.0f} {symbol}")
    except Exception as e:
        st.error(f"❌ Помилка при читанні контракту: {e}")

    # === HOLDERS ===
    try:
        st.markdown("## 🧍‍♂️ Холдери")
        holders_url = f"https://api.ethplorer.io/getTokenInfo/{token_address}?apiKey=freekey"
        resp = requests.get(holders_url)
        if resp.status_code == 200:
            data = resp.json()
            holders = data.get("holdersCount", "N/A")
            st.success(f"👥 Кількість холдерів: {holders}")
        else:
            st.warning("⚠️ Неможливо отримати список холдерів")
    except Exception as e:
        st.error(f"❌ Холдери помилка: {e}")

    # === ANTI-BOT ===
    try:
        st.subheader("🛡️ Anti-Bot / MEV Аналіз", divider="orange")
        is_verified = False  # тимчасово
        contract_info = {}  # тимчасово
        if not is_verified:
            st.warning("⚠️ Неможливо провести аналіз — контракт не верифікований")
        else:
            source_code = contract_info.get("SourceCode", "")
            suspicious_patterns = ["blacklist", "sniper", "tradingEnabled", "maxTxAmount"]
            warnings = [f"🔍 Виявлено `{pat}` у коді" for pat in suspicious_patterns if pat in source_code]
            if warnings:
                for warn in warnings:
                    st.warning(warn)
            else:
                st.success("✅ Ознак анти-бот або MEV захисту не виявлено")
    except Exception as e:
        st.error(f"❌ Anti-Bot помилка: {e}")
