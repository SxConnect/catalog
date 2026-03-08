import axios from "axios";

// A URL da API será https://catalog-api.sxconnect.com.br em produção
const apiUrl = typeof window !== 'undefined'
    ? (window as any).__API_URL__ || "https://catalog-api.sxconnect.com.br"
    : process.env.NEXT_PUBLIC_API_URL || "https://catalog-api.sxconnect.com.br";

console.log("API URL:", apiUrl);

const api = axios.create({
    baseURL: apiUrl,
    headers: {
        "Content-Type": "application/json",
    },
});

export default api;
