import axios from "axios";

// Função para obter a URL da API
const getApiUrl = () => {
    // No servidor (SSR), usar URL interna se disponível
    if (typeof window === 'undefined') {
        return process.env.NEXT_PUBLIC_API_URL || 'https://catalog-api.sxconnect.com.br';
    }

    // No cliente, usar a URL pública
    return process.env.NEXT_PUBLIC_API_URL || 'https://catalog-api.sxconnect.com.br';
};

const api = axios.create({
    baseURL: getApiUrl(),
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 10000, // 10 segundos de timeout
});

// Interceptor para log de erros
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', {
            url: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            message: error.message,
            baseURL: error.config?.baseURL
        });
        return Promise.reject(error);
    }
);

export default api;
