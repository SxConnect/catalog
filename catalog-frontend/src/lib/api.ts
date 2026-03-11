import axios from "axios";

// URLs da API em ordem de prioridade
const API_URLS = [
    'https://catalog-api.sxconnect.com.br',
    'http://localhost:8000',
    'http://vmi2917323.contaboserver.net:8000'
];

// Função para obter a URL da API
const getApiUrl = () => {
    // No servidor (SSR), usar URL interna do container
    if (typeof window === 'undefined') {
        return 'http://sixpet-catalog-api:8000';
    }

    // No cliente, usar proxy do Next.js
    return '';
};

// No cliente, usar a primeira URL da lista
return process.env.NEXT_PUBLIC_API_URL || API_URLS[0];
};

let currentApiUrlIndex = 0;

const api = axios.create({
    baseURL: getApiUrl(),
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 120000, // 2 minutos para uploads grandes
    withCredentials: false,
});

// Interceptor para log de erros e retry com fallback
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

        // Se for erro de rede e estivermos no cliente, tentar próxima URL
        if (typeof window !== 'undefined' &&
            (error.code === 'ERR_NETWORK' ||
                error.code === 'ERR_CONNECTION_REFUSED' ||
                error.response?.status === 404) &&
            currentApiUrlIndex < API_URLS.length - 1) {

            currentApiUrlIndex++;
            const nextUrl = API_URLS[currentApiUrlIndex];
            console.warn(`Tentando URL alternativa: ${nextUrl}`);

            // Atualizar baseURL e tentar novamente
            api.defaults.baseURL = nextUrl;
            error.config.baseURL = nextUrl;

            return api.request(error.config);
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