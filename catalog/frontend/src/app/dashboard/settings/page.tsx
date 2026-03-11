"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Save, Key, Globe, Zap, AlertCircle } from "lucide-react";
import api from "@/lib/api";
import { useForm } from "react-hook-form";

type SettingsForm = {
    groq_api_keys: string;
    extractions_per_second: number;
    scraping_url: string;
    scraping_enabled: boolean;
    max_concurrent_catalogs: number;
    enable_deduplication: boolean;
    similarity_threshold: number;
};

export default function SettingsPage() {
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<"api" | "scraping" | "processing">("api");

    const { data: settings, isLoading } = useQuery("settings", async () => {
        const res = await api.get("/api/admin/settings");
        return res.data;
    });

    const {
        register,
        handleSubmit,
        formState: { errors },
        reset,
    } = useForm<SettingsForm>({
        values: settings,
    });

    const saveMutation = useMutation(
        async (data: SettingsForm) => {
            const res = await api.put("/api/admin/settings", data);
            return res.data;
        },
        {
            onSuccess: () => {
                queryClient.invalidateQueries("settings");
                alert("Configurações salvas com sucesso!");
            },
            onError: (error: any) => {
                alert(`Erro ao salvar: ${error.response?.data?.detail || error.message}`);
            },
        }
    );

    const onSubmit = (data: SettingsForm) => {
        saveMutation.mutate(data);
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    const tabs = [
        { id: "api", name: "API Keys", icon: Key },
        { id: "scraping", name: "Web Scraping", icon: Globe },
        { id: "processing", name: "Processamento", icon: Zap },
    ];

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
                <p className="mt-1 text-sm text-gray-600">
                    Configure o comportamento do sistema
                </p>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-200">
                <nav className="-mb-px flex space-x-8">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`
                flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab.id
                                    ? "border-primary-500 text-primary-600"
                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                }
              `}
                        >
                            <tab.icon className="h-5 w-5" />
                            {tab.name}
                        </button>
                    ))}
                </nav>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* API Keys Tab */}
                {activeTab === "api" && (
                    <div className="bg-white shadow rounded-lg p-6 space-y-6">
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">
                                Chaves de API Groq
                            </h2>
                            <p className="text-sm text-gray-600 mb-4">
                                Configure as chaves de API para processamento de IA. Separe múltiplas chaves com vírgula para rotação automática.
                            </p>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Chaves de API (separadas por vírgula)
                                </label>
                                <textarea
                                    {...register("groq_api_keys", {
                                        required: "Pelo menos uma chave é obrigatória",
                                    })}
                                    rows={4}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 font-mono text-sm"
                                    placeholder="gsk_key1,gsk_key2,gsk_key3"
                                />
                                {errors.groq_api_keys && (
                                    <p className="mt-1 text-sm text-red-600">{errors.groq_api_keys.message}</p>
                                )}
                                <p className="mt-2 text-xs text-gray-500">
                                    Obtenha suas chaves em: https://console.groq.com/keys
                                </p>
                            </div>
                        </div>

                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                            <div className="flex gap-3">
                                <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                                <div className="text-sm text-yellow-800">
                                    <p className="font-medium mb-1">Importante:</p>
                                    <ul className="list-disc list-inside space-y-1">
                                        <li>Mantenha suas chaves seguras</li>
                                        <li>Use múltiplas chaves para evitar rate limits</li>
                                        <li>O sistema rotaciona automaticamente entre as chaves</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Web Scraping Tab */}
                {activeTab === "scraping" && (
                    <div className="bg-white shadow rounded-lg p-6 space-y-6">
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">
                                Configurações de Web Scraping
                            </h2>
                            <p className="text-sm text-gray-600 mb-6">
                                Configure como o sistema busca informações adicionais na web
                            </p>

                            <div className="space-y-6">
                                {/* Enable Scraping */}
                                <div className="flex items-center justify-between">
                                    <div>
                                        <label className="text-sm font-medium text-gray-900">
                                            Habilitar Web Scraping
                                        </label>
                                        <p className="text-sm text-gray-500">
                                            Buscar dados faltantes automaticamente
                                        </p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            {...register("scraping_enabled")}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                                    </label>
                                </div>

                                {/* Extractions per second */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Extrações por Segundo
                                    </label>
                                    <input
                                        type="number"
                                        {...register("extractions_per_second", {
                                            required: "Campo obrigatório",
                                            min: { value: 1, message: "Mínimo 1" },
                                            max: { value: 100, message: "Máximo 100" },
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                                        placeholder="10"
                                    />
                                    {errors.extractions_per_second && (
                                        <p className="mt-1 text-sm text-red-600">
                                            {errors.extractions_per_second.message}
                                        </p>
                                    )}
                                    <p className="mt-1 text-xs text-gray-500">
                                        Controla a velocidade de requisições para evitar bloqueios
                                    </p>
                                </div>

                                {/* Scraping URL */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        URL Base para Scraping
                                    </label>
                                    <input
                                        type="url"
                                        {...register("scraping_url", {
                                            pattern: {
                                                value: /^https?:\/\/.+/,
                                                message: "URL inválida",
                                            },
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                                        placeholder="https://exemplo.com/api/products"
                                    />
                                    {errors.scraping_url && (
                                        <p className="mt-1 text-sm text-red-600">{errors.scraping_url.message}</p>
                                    )}
                                    <p className="mt-1 text-xs text-gray-500">
                                        Endpoint ou site de onde buscar informações dos produtos
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="flex gap-3">
                                <Globe className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                                <div className="text-sm text-blue-800">
                                    <p className="font-medium mb-1">Como funciona:</p>
                                    <ul className="list-disc list-inside space-y-1">
                                        <li>Sistema busca dados faltantes usando EAN ou nome do produto</li>
                                        <li>Respeita rate limits configurados</li>
                                        <li>Atualiza apenas campos marcados no upload</li>
                                        <li>Mantém histórico de enriquecimento</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Processing Tab */}
                {activeTab === "processing" && (
                    <div className="bg-white shadow rounded-lg p-6 space-y-6">
                        <div>
                            <h2 className="text-lg font-semibold text-gray-900 mb-4">
                                Configurações de Processamento
                            </h2>
                            <p className="text-sm text-gray-600 mb-6">
                                Ajuste o comportamento do processamento de catálogos
                            </p>

                            <div className="space-y-6">
                                {/* Max Concurrent Catalogs */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Catálogos Simultâneos
                                    </label>
                                    <input
                                        type="number"
                                        {...register("max_concurrent_catalogs", {
                                            required: "Campo obrigatório",
                                            min: { value: 1, message: "Mínimo 1" },
                                            max: { value: 10, message: "Máximo 10" },
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                                        placeholder="4"
                                    />
                                    {errors.max_concurrent_catalogs && (
                                        <p className="mt-1 text-sm text-red-600">
                                            {errors.max_concurrent_catalogs.message}
                                        </p>
                                    )}
                                    <p className="mt-1 text-xs text-gray-500">
                                        Número máximo de catálogos processados ao mesmo tempo
                                    </p>
                                </div>

                                {/* Enable Deduplication */}
                                <div className="flex items-center justify-between">
                                    <div>
                                        <label className="text-sm font-medium text-gray-900">
                                            Deduplicação Automática
                                        </label>
                                        <p className="text-sm text-gray-500">
                                            Detectar e mesclar produtos duplicados
                                        </p>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input
                                            type="checkbox"
                                            {...register("enable_deduplication")}
                                            className="sr-only peer"
                                        />
                                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                                    </label>
                                </div>

                                {/* Similarity Threshold */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-2">
                                        Limite de Similaridade
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        {...register("similarity_threshold", {
                                            required: "Campo obrigatório",
                                            min: { value: 0.5, message: "Mínimo 0.5" },
                                            max: { value: 1.0, message: "Máximo 1.0" },
                                        })}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
                                        placeholder="0.85"
                                    />
                                    {errors.similarity_threshold && (
                                        <p className="mt-1 text-sm text-red-600">
                                            {errors.similarity_threshold.message}
                                        </p>
                                    )}
                                    <p className="mt-1 text-xs text-gray-500">
                                        Produtos com similaridade acima deste valor são considerados duplicados (0.5 a 1.0)
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Save Button */}
                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={saveMutation.isLoading}
                        className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                        {saveMutation.isLoading ? (
                            <>
                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                                Salvando...
                            </>
                        ) : (
                            <>
                                <Save className="h-5 w-5" />
                                Salvar Configurações
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}
