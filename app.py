import streamlit as st
import requests
from web3 import Web3
import pandas as pd
import plotly.graph_objs as go

ETHERSCAN_API_KEY = "XSUUHZ6HN6ED625QCRD6DK2UBFBKT65G"
rpc_url = "https://eth.llamarpc.com"

# === Page config ===
st.set_page_config(page_title="SniperBase", layout="wide")

# === Styles ===
st.markdown("""
    <style>
        body {
            background-color: #000000;
            color: #f0f0f0;
        }
        .stTextInput>div>div>input {
            background-color: #1c1c1c;
            color: #fff;
            border: 1px solid #f0b90b;
        }
        .stMetric {
            background-color: #1c1c1c;
            padding: 12px;
            border-radius: 10px;
            margin: 6px;
            color: #f0b90b;
        }
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            color: #f0b90b;
        }
    </style>
""", unsafe_allow_html=True)

# === Title ===
st.markdown("## 🧠 Введи адресу контракту токена")
token_address = st.text_input("🔍 ERC-20 адреса контракту:")

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

        st.success(f"🟨 **Назва токена**: {name}")
        st.success(f"🟨 **Символ**: {symbol}")
        st.info(f"🧮 Деcимали: {decimals}")
        st.info(f"📦 Загальна емісія: {total_supply:,.0f} {symbol}")

    except Exception as e:
        st.error(f"❌ Помилка при обробці токена: {e}")

    # === ETHERSCAN VERIFICATION ===
    try:
        etherscan_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={ETHERSCAN_API_KEY}"
        res = requests.get(etherscan_url).json()

        if res["status"] == "1" and res["result"]:
            code_data = res["result"][0]
            verified = bool(code_data.get("SourceCode"))
            creator = code_data.get("ContractCreator", "Невідомо")
            st.markdown(f"🟡 **Контракт верифікований:** {'✅ Так' if verified else '❌ Ні'}")
            st.markdown(f"👤 Власник контракту: `{creator}`")
        else:
            st.warning("⚠️ Контракт не верифікований або не знайдено результатів на Etherscan")

    except Exception as e:
        st.error(f"❌ Помилка перевірки: {e}")

    # === DEXSCREENER DATA ===
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        res = requests.get(url).json()

        if "pairs" in res and res["pairs"]:
            pair = res["pairs"][0]
            price = float(pair["priceUsd"])
            liquidity = float(pair["liquidity"]["usd"])
            volume = float(pair["volume"]["h24"])
            fdv = int(pair["fdv"])
            price_data = pair.get("priceNative", None)

            st.markdown("### 📊 Дані з DexScreener")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💰 Ціна", f"${price:,.6f}")
            c2.metric("💧 Ліквідність", f"${liquidity:,.2f}")
            c3.metric("📦 Обʼєм (24h)", f"${volume:,.2f}")
            c4.metric("🏷️ FDV", f"${fdv:,}")

            # Графік ціни
            if "chart" in pair:
                price_points = pair["chart"]
                timestamps = [p["timestamp"] for p in price_points]
                prices = [float(p["priceUsd"]) for p in price_points]

                df = pd.DataFrame({"Timestamp": pd.to_datetime(timestamps, unit='s'), "Price": prices})
                fig = go.Figure(go.Scatter(x=df["Timestamp"], y=df["Price"], mode='lines', name='Ціна'))
                fig.update_layout(title="📈 Історія ціни", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ DexScreener помилка: {e}")

    # === ТОП ХОЛДЕРИ ===
    try:
        holders_url = f"https://api.etherscan.io/api?module=token&action=tokenholderlist&contractaddress={token_address}&page=1&offset=5&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(holders_url).json()
        if response["status"] == "1":
            st.markdown("### 👥 Топ 5 холдерів")
            for holder in response["result"]:
                addr = holder["HolderAddress"]
                balance = int(holder["TokenHolderQuantity"]) / (10 ** decimals)
                st.write(f"🔸 `{addr}`: **{balance:,.2f} {symbol}**")
        else:
            st.warning("⚠️ Неможливо отримати список холдерів.")

    except Exception as e:
        st.error(f"❌ Помилка холдерів: {e}")

    # === Anti-MEV/Anti-Bot Аналіз ===
    st.markdown("### 🛡️ Anti-Bot / MEV аналіз")
    try:
        if verified and "SourceCode" in code_data:
            src = code_data["SourceCode"]
            red_flags = []

            if "maxTxAmount" in src.lower() or "maxWallet" in src.lower():
                red_flags.append("📛 Ліміт на кількість токенів у гаманці або транзакції")

            if "blacklist" in src.lower():
                red_flags.append("🚫 Присутній Blacklist механізм")

            if "mev" in src.lower():
                red_flags.append("🤖 Anti-MEV логіка (можливо)")

            if red_flags:
                for item in red_flags:
                    st.warning(item)
            else:
                st.success("✅ Антибот або анти-MEV логіка не виявлена.")
        else:
            st.warning("⚠️ Контракт не верифікований — неможливо перевірити код.")
    except Exception as e:
        st.error(f"❌ Аналіз контракту провалився: {e}")
