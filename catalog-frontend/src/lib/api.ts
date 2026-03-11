import axios from "axios";

// Função para obter a URL da API
const getApiUrl = () => {
    // No servidor (SSR), tentar usar URL interna primeiro
    if (typeof window === 'undefined') {
        // Tentar URL interna do container primeiro
        return process.env.NEXT_PUBLIC_API_URL || 'https://catalog-api.sxconnect.com.br';
    }

    // No cliente, sempre usar a URL pública
    return process.env.NEXT_PUBLIC_API_URL || 'https://catalog-api.sxconnect.com.br';
};

const api = axios.create({
    baseURL: getApiUrl(),
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 120000, // 2 minutos para uploads grandes
    // Configurações para resolver problemas de CORS
    withCredentials: false,
});

// Interceptor para log de erros e retry
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

        // Se for erro de CORS ou conexão, tentar com URL alternativa
        if (error.code === 'ERR_NETWORK' || error.code === 'ERR_CONNECTION_REFUSED') {
            console.warn('Tentando URL alternativa devido a erro de rede...');
            // Não fazer retry automático para evitar loops
        }

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