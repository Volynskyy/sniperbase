# app.py
# Requires: streamlit, requests, web3

try:
    import streamlit as st
except ModuleNotFoundError:
    raise ModuleNotFoundError("Streamlit is not installed. Please install it with: pip install streamlit")

import requests
from web3 import Web3

ETHERSCAN_API_KEY = "XSUUHZ6HN6ED625QCRD6DK2UBFBKT65G"

st.set_page_config(page_title="SniperBase", layout="wide")
st.title("🚀 SniperBase")
st.markdown("Твій асистент для аналізу пампів, снайпінгу мем-токенів та швидкого входу в угоди. Тут буде 🔥.")
st.info("🔧 MVP у процесі. Функціонал скоро буде розширено.")
st.subheader("🧠 Введи адресу контракту токена")

token_address = st.text_input("Адреса контракту (ERC-20):")
rpc_url = "https://eth.llamarpc.com"
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

        st.success(f"📘 Назва токена: {name}")
        st.success(f"🧾 Символ: {symbol}")
        st.info(f"📐 Деcимали: {decimals}")
        st.info(f"📦 Загальна емісія: {total_supply:,.0f} {symbol}")

    except Exception as e:
        st.error(f"❌ Помилка при обробці токена: {e}")

    # Etherscan перевірка
    try:
        etherscan_url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={token_address}&apikey={ETHERSCAN_API_KEY}"
        response = requests.get(etherscan_url)

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1" and "result" in data and len(data["result"]) > 0:
                contract_info = data["result"][0]
                is_verified = contract_info.get("SourceCode", "") != ""
                creator_address = contract_info.get("ContractCreator", "Невідомо")

                st.markdown(f"✅ Верифікація контракту: {'✔️ Так' if is_verified else '❌ Ні'}")
                st.markdown(f"📍 Адреса власника контракту: `{creator_address}`")
            else:
                st.warning("⚠️ Контракт не верифікований або не знайдено результатів на Etherscan")
        else:
            st.error("❌ Etherscan API не відповідає")

    except Exception as e:
        st.error(f"❌ Помилка Etherscan: {e}")

    # DexScreener
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

                st.divider()
                st.subheader("📊 Дані з DexScreener")
                st.metric("💲 Ціна", f"{price}")
                st.metric("💧 Ліквідність", f"${liquidity_usd}")
                st.metric("📦 Об’єм (24h)", f"${volume}")
                st.metric("FDV", f"${int(fdv):,}" if fdv != "N/A" else "N/A")
            else:
                st.warning("⚠️ Не знайдено пару для цього токена в DexScreener.")
        else:
            st.warning("⚠️ Не вдалося отримати дані з DexScreener.")

    except Exception as e:
        st.error(f"❌ DexScreener помилка: {e}")
