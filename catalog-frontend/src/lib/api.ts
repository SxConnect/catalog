import axios from "axios";

// Função para obter a URL da API
const getApiUrl = () => {
    // No servidor (SSR), usar URL interna do container
    if (typeof window === 'undefined') {
        return 'http://sixpet-catalog-api:8000';
    }

    // No cliente, usar porta 8000 diretamente
    return 'http://vmi2917323.contaboserver.net:8000';
};

const api = axios.create({
    baseURL: getApiUrl(),
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 120000, // 2 minutos para uploads grandes
    withCredentials: false,
});

// Interceptor para log de erros e fallback para HTTP
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

        // Se for erro de CORS/SSL no cliente, tentar HTTP
        if (typeof window !== 'undefined' &&
            (error.code === 'ERR_NETWORK' || error.response?.status === 404) &&
            error.config?.baseURL?.includes('https://')) {

            console.warn('HTTPS falhou, tentando HTTP...');
            const httpUrl = error.config.baseURL.replace('https://', 'http://');

            // Criar nova requisição com HTTP
            const newConfig = {
                ...error.config,
                baseURL: httpUrl
            };

            return axios.request(newConfig);
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