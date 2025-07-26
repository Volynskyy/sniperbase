# app.py

import streamlit as st
import requests
from web3 import Web3
import pandas as pd
import plotly.graph_objs as go

ETHERSCAN_API_KEY = "XSUUHZ6HN6ED625QCRD6DK2UBFBKT65G"
rpc_url = "https://eth.llamarpc.com"

web3 = Web3(Web3.HTTPProvider(rpc_url))
st.set_page_config(page_title="SniperBase", layout="wide")

# ======= CUSTOM DARK UI STYLES (BINANCE-STYLE) =======
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

# ====== LANDING INTRO ======
st.markdown("## 🚀 Ласкаво просимо до SniperBase")
st.markdown("Інструмент для швидкої перевірки нових токенів: **аналіз контракту, ліквідність, холдери та MEV-пастки**")

# ======= ВВЕДЕННЯ КОНТРАКТУ =======
st.markdown("### 🧠 Введи адресу контракту токена")
token_address = st.text_input("🔍 ERC-20 адреса контракту:")

erc20_abi = [
    {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"}
]

verified = False

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

    # ======= ETHERSCAN =======
try:
    etherscan_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(etherscan_url, timeout=10)

    if response.status_code == 200:
        data = response.json()

        # Перевірка, чи API повернув успішну відповідь
        if data.get("status") == "1" and data.get("result"):
            contract_info = data["result"][0]

            # Перевірка наявності вихідного коду
            is_verified = contract_info.get("SourceCode", "").strip() != ""
            st.session_state["is_verified"] = is_verified  # Зберігаємо у сесію

            # Отримуємо адресу творця
            creator_address = contract_info.get("ContractCreator", "Невідомо")

            # Виводимо результат
            if is_verified:
                st.markdown("✅ **Контракт верифікований:** Так")
            else:
                st.markdown("⚠️ **Контракт не верифікований або порожній вихідний код**")

            st.markdown(f"📍 **Адреса творця контракту:** `{creator_address}`")

        else:
            # Кейс: API статус не "1", або result порожній
            message = data.get("message", "Невідома помилка")
            st.warning(f"⚠️ Etherscan не зміг обробити запит: {message}")
    else:
        st.error(f"❌ Помилка запиту до Etherscan: Код {response.status_code}")

except requests.exceptions.RequestException as e:
    st.error(f"❌ Запит до Etherscan не вдалось виконати: {e}")
except Exception as e:
    st.error(f"❌ Неочікувана помилка при обробці Etherscan API: {e}")

    # ======= DEXSCREENER =======
    try:
        dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        response = requests.get(dex_url)
        if response.status_code == 200:
            data = response.json()
            if "pairs" in data and data["pairs"]:
                pair = data["pairs"][0]
                price = pair.get("priceUsd", "N/A")
                liquidity_usd = pair.get("liquidity", {}).get("usd", "N/A")
                volume = pair.get("volume", {}).get("h24", "N/A")
                fdv = pair.get("fdv", "N/A")

                st.markdown("## 📊 Дані з DexScreener")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💰 Ціна", f"${float(price):,.6f}" if price != "N/A" else "N/A")
                col2.metric("💧 Ліквідність", f"${float(liquidity_usd):,.2f}" if liquidity_usd != "N/A" else "N/A")
                col3.metric("📦 Обʼєм (24h)", f"${float(volume):,.2f}" if volume != "N/A" else "N/A")
                col4.metric("🏷️ FDV", f"${int(fdv):,}" if fdv != "N/A" else "N/A")
            else:
                st.warning("⚠️ Не знайдено пару для цього токена")
        else:
            st.warning("⚠️ Не вдалося отримати дані з DexScreener")
    except Exception as e:
        st.error(f"❌ DexScreener помилка: {e}")

    # ======= HOLDERS (READ FROM TOKEN CONTRACT) =======
    try:
        st.markdown("## 🧍‍♂️ Холдерам")
        holder_count_url = f"https://api.ethplorer.io/getTokenInfo/{token_address}?apiKey=freekey"
        resp = requests.get(holder_count_url)
        if resp.status_code == 200:
            data = resp.json()
            holders = data.get("holdersCount", "N/A")
            st.success(f"👥 Кількість холдерів: {holders}")
        else:
            st.warning("⚠️ Неможливо отримати список холдерів")
    except Exception as e:
        st.error(f"❌ Холдери помилка: {e}")

  # ======= ANTI-BOT / MEV ANALYSIS =======
try:
    st.subheader("🛡️ Anti-Bot / MEV аналіз", divider="orange")

    if not st.session_state.get("is_verified", False):
        st.warning("⚠️ Контракт не верифікований, неможливо провести повний аналіз")
    else:
        # Example: Simulate anti-bot protection checks (mocked logic for now)
        # You can later expand this with real logic using ABI decoding or Web3 calls

        # Placeholder: Define safe heuristics (can be replaced with real rules)
        anti_bot_flags = []

        # Common indicators of bot protection
        suspicious_functions = ["setBlacklist", "isSniper", "setTradingEnabled", "setMaxTxAmount"]
        for func in suspicious_functions:
            if func.lower() in contract_info.get("SourceCode", "").lower():
                anti_bot_flags.append(f"🔍 Можливо використовується функція `{func}` для захисту від ботів")

        if anti_bot_flags:
            for flag in anti_bot_flags:
                st.warning(flag)
        else:
            st.success("✅ Ознак анти-бот або MEV захисту не виявлено у верифікованому коді контракту")

except Exception as e:
    st.error(f"❌ Помилка при аналізі анти-бот/MEV: {e}")

