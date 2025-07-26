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

    # === ETHERSCAN ===
    contract_info = None
    is_verified = False
    try:
        etherscan_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(etherscan_url, timeout=10)
        data = response.json()

        if data.get("status") == "1" and data.get("result"):
            contract_info = data["result"][0]
            is_verified = contract_info.get("SourceCode", "").strip() != ""
            creator_address = contract_info.get("ContractCreator", "Невідомо")

            if is_verified:
                st.success("✅ Контракт верифікований")
            else:
                st.warning("⚠️ Контракт не верифікований")
            st.markdown(f"👤 **Творець контракту:** `{creator_address}`")
        else:
            st.warning("⚠️ Не вдалося отримати дані з Etherscan")
    except Exception as e:
        st.error(f"❌ Etherscan API помилка: {e}")

    # === DEXSCREENER ===
    try:
        dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        response = requests.get(dex_url)
        data = response.json()
        if "pairs" in data and data["pairs"]:
            pair = data["pairs"][0]
            price = float(pair.get("priceUsd", 0))
            liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0))
            volume = float(pair.get("volume", {}).get("h24", 0))
            fdv = float(pair.get("fdv", 0))

            # === STORE PRICE HISTORY ===
            history_file = f"history_{token_address}.csv"
            if os.path.exists(history_file):
                history_df = pd.read_csv(history_file, parse_dates=["timestamp"])
            else:
                history_df = pd.DataFrame(columns=["timestamp", "priceUsd"])

            new_row = {"timestamp": datetime.utcnow(), "priceUsd": price}
            history_df = pd.concat([history_df, pd.DataFrame([new_row])], ignore_index=True)
            history_df.to_csv(history_file, index=False)

            st.markdown("## 📊 DexScreener")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Ціна", f"${price:,.6f}")
            col2.metric("💧 Ліквідність", f"${liquidity_usd:,.2f}")
            col3.metric("📦 Обʼєм (24h)", f"${volume:,.2f}")
            col4.metric("🏷️ FDV", f"${fdv:,.0f}")

            # === ГРАФІК ЦІНИ ===
            price_data = pair.get("priceNativeHistory", [])
            if price_data:
                timestamps = [datetime.fromtimestamp(p["timestamp"]) for p in price_data]
                prices = [float(p["price"]) for p in price_data]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=timestamps, y=prices, mode="lines+markers", name="Ціна"))
                fig.update_layout(title="📈 Графік ціни", xaxis_title="Час", yaxis_title="Ціна (native)", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

            # === ГРАФІК ІСТОРІЇ ===
            if not history_df.empty:
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Scatter(x=history_df["timestamp"], y=history_df["priceUsd"], mode="lines+markers", name="Price USD"))
                fig_hist.update_layout(title="📈 Історія ціни (USD)", xaxis_title="Час", yaxis_title="Ціна (USD)", template="plotly_dark")
                st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.warning("❌ Пара токена не знайдена на DexScreener")
    except Exception as e:
        st.error(f"❌ DexScreener помилка: {e}")

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
