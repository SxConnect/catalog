import axios from "axios";

// Usar a URL da API do ambiente ou fallback para produção
const apiUrl = typeof window !== 'undefined'
    ? (window as any).__API_URL__ || "https://catalog-api.sxconnect.com.br"
    : "https://catalog-api.sxconnect.com.br";

console.log("API URL:", apiUrl);

const api = axios.create({
    baseURL: apiUrl,
    headers: {
        "Content-Type": "application/json",
    },
});

export default api;
