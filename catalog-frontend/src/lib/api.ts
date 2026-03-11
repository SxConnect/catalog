import axios from "axios";

// Função para obter a URL da API
const getApiUrl = () => {
    // No servidor (SSR), usar URL interna do container
    if (typeof window === 'undefined') {
        return 'http://sixpet-catalog-api:8000';
    }

    // No cliente, usar proxy do Next.js (baseURL vazia = URL relativa)
    return '';
};

const api = axios.create({
    baseURL: getApiUrl(),
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 120000, // 2 minutos para uploads grandes
    withCredentials: false,
});

// Interceptor para log de erros
api.interceptors.response.use(
    (response) => response,
    async (error) => {
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

// Interceptor para adicionar headers necessários
api.interceptors.request.use(
    (config) => {
        // Log da requisição para debug
        console.log('API Request:', {
            url: config.url,
            method: config.method,
            baseURL: config.baseURL
        });
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default api;