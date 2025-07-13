# app.py
# Requires: streamlit, requests, web3

try:
    import streamlit as st
except ModuleNotFoundError:
    raise ModuleNotFoundError("Streamlit is not installed. Please install it with: pip install streamlit")

import requests
from web3 import Web3

ETHERSCAN_API_KEY = "XSUUHZ6HN6ED625QCRD6DK2UBFBKT65G"
rpc_url = "https://eth.llamarpc.com"

st.set_page_config(page_title="SniperBase", layout="wide")

# ==== СТИЛІ ====
st.markdown("""
    <style>
        body {
            background-color: #0b0f1a;
            color: #eaecef;
        }
        .block-container {
            padding-top: 2rem;
        }
        .stTextInput > div > div > input {
            background-color: #1c1f2b;
            color: white;
            border: 1px solid #2a2e3d;
        }
        .stMetric {
            background-color: #1c1f2b;
            border-radius: 8px;
            padding: 16px;
            margin: 8px;
            color: white;
            font-weight: 600;
        }
        .stMarkdown h2, .stMarkdown h3, .stMarkdown h1 {
            color: #f0b90b;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("### 🧠 Введи адресу контракту токена")
token_address = st.text_input("Адреса контракту (ERC-20):")

web3 = Web3(Web3.HTTPProvider(rpc_url))

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

        st.success(f"🟩 Назва токена: **{name}**")
        st.success(f"🟨 Символ: **{symbol}**")
        st.info(f"🧮 Деcимали: **{decimals}**")
        st.info(f"📦 Загальна емісія: **{total_supply:,.0f} {symbol}**")

    except Exception as e:
        st.error(f"❌ Помилка при обробці токена: {e}")

    # ==== ETHERSCAN ====
    try:
        etherscan_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(etherscan_url)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and "result" in data and len(data["result"]) > 0:
                contract_info = data["result"][0]
                is_verified = contract_info.get("SourceCode", "") != ""
                creator_address = contract_info.get("ContractCreator", "Невідомо")

                st.markdown(f"🟢 Верифікація контракту: {'✔️ Так' if is_verified else '❌ Ні'}")
                st.markdown(f"👤 Адреса власника контракту: `{creator_address}`")
            else:
                st.warning("⚠️ Контракт не верифікований або не знайдено результатів на Etherscan")
        else:
            st.error("❌ Etherscan API не відповідає")

    except Exception as e:
        st.error(f"❌ Помилка Etherscan: {e}")

    # ==== DEXSCREENER ====
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

                st.markdown("---")
                st.markdown("### 📊 Дані з DexScreener")

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💲 Ціна", f"${float(price):,.6f}" if price != "N/A" else "N/A")
                col2.metric("💧 Ліквідність", f"${float(liquidity_usd):,.2f}" if liquidity_usd != "N/A" else "N/A")
                col3.metric("📦 Обʼєм (24h)", f"${float(volume):,.2f}" if volume != "N/A" else "N/A")
                col4.metric("🏷️ FDV", f"${int(fdv):,}" if fdv != "N/A" else "N/A")
            else:
                st.warning("⚠️ Не знайдено пару для цього токена в DexScreener.")
        else:
            st.warning("⚠️ Не вдалося отримати дані з DexScreener.")

    except Exception as e:
        st.error(f"❌ DexScreener помилка: {e}")
