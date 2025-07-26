# app.py
import streamlit as st
import requests
from web3 import Web3

ETHERSCAN_API_KEY = "XSUUHZ6HN6ED625QCRD6DK2UBFBKT65G"
rpc_url = "https://eth.llamarpc.com"
web3 = Web3(Web3.HTTPProvider(rpc_url))

st.set_page_config(page_title="SniperBase", layout="wide")

# ===== 🎨 СТИЛІ =====
st.markdown("""
    <style>
        html, body, .block-container {
            background-color: #000000;
            color: #f0b90b;
            font-family: 'Segoe UI', sans-serif;
        }
        .stTextInput>div>div>input {
            background-color: #121212;
            color: white;
            border: 1px solid #2f2f2f;
            border-radius: 8px;
        }
        .stMetric {
            background-color: #121212;
            border-radius: 10px;
            padding: 15px;
            margin-top: 10px;
            color: #f0b90b;
            font-weight: 600;
            text-align: center;
        }
        h1, h2, h3 {
            color: #f0b90b;
        }
        .stAlert, .stMarkdown {
            background-color: #121212;
            padding: 12px;
            border-radius: 8px;
        }
        hr {
            border-top: 1px solid #333;
        }
    </style>
""", unsafe_allow_html=True)

# ===== 🧠 ХЕДЕР =====
st.markdown("<h1>🧠 Введи адресу контракту токена</h1>", unsafe_allow_html=True)
token_address = st.text_input("🔍 ERC-20 адреса контракту:")

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

        st.markdown(f"🔶 <b>Назва токена:</b> <span style='color:#00ff99'>{name}</span>", unsafe_allow_html=True)
        st.markdown(f"🔷 <b>Символ:</b> <span style='color:#00ff99'>{symbol}</span>", unsafe_allow_html=True)
        st.markdown(f"🧮 <b>Деcимали:</b> {decimals}", unsafe_allow_html=True)
        st.markdown(f"📦 <b>Загальна емісія:</b> {total_supply:,.0f} {symbol}", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Помилка при обробці токена: {e}")

    # ===== 🔎 ETHERSCAN =====
    try:
        etherscan_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(etherscan_url)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and "result" in data and len(data["result"]) > 0:
                contract_info = data["result"][0]
                is_verified = contract_info.get("SourceCode", "") != ""
                creator_address = contract_info.get("ContractCreator", "Невідомо")

                st.markdown(f"✅ <b>Контракт верифіковано:</b> {'Так' if is_verified else 'Ні'}", unsafe_allow_html=True)
                st.markdown(f"👤 <b>Адреса власника:</b> `{creator_address}`", unsafe_allow_html=True)
            else:
                st.warning("⚠️ Контракт не верифікований або не знайдено результатів на Etherscan")
        else:
            st.error("❌ Etherscan API не відповідає")

    except Exception as e:
        st.error(f"❌ Помилка Etherscan: {e}")

    # ===== 📊 DEXSCREENER =====
    try:
        dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        response = requests.get(dex_url)

        if response.status_code == 200:
            data = response.json()
            if "pairs" in data and data["pairs"]:
                pair = data["pairs"][0]
                price = pair.get("priceUsd", "N/A")
                liquidity_usd = pair.get("liquidity", {}).get("usd", "N/A")
                fdv = pair.get("fdv", "N/A")
                volume = pair.get("volume", {}).get("h24", "N/A")

                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("### 📊 Дані з DexScreener")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💰 Ціна", f"${float(price):,.6f}" if price != "N/A" else "N/A")
                col2.metric("💧 Ліквідність", f"${float(liquidity_usd):,.2f}" if liquidity_usd != "N/A" else "N/A")
                col3.metric("📦 Обʼєм (24h)", f"${float(volume):,.2f}" if volume != "N/A" else "N/A")
                col4.metric("🏷️ FDV", f"${int(fdv):,}" if fdv != "N/A" else "N/A")
            else:
                st.warning("⚠️ Не знайдено пару для цього токена в DexScreener.")
        else:
            st.warning("⚠️ Не вдалося отримати дані з DexScreener.")

    except Exception as e:
        st.error(f"❌ DexScreener помилка: {e}")
