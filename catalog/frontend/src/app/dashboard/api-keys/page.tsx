"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import { Plus, Trash2, Key, TrendingUp, Activity } from "lucide-react";
import api from "@/lib/api";

type ApiKey = {
    id: number;
    key: string;
    provider: string;
    daily_limit: number;
    used_today: number;
    status: boolean;
    last_used: string;
};

export default function ApiKeysPage() {
    const queryClient = useQueryClient();
    const [newKey, setNewKey] = useState("");
    const [showAddForm, setShowAddForm] = useState(false);

    const { data: keys, isLoading } = useQuery<ApiKey[]>("api-keys", async () => {
        const res = await api.get("/api/admin/api-keys");
        return res.data;
    });

    const addMutation = useMutation(
        async (key: string) => {
            const res = await api.post("/api/admin/api-keys", {
                key,
                provider: "groq",
                daily_limit: 14400,
            });
            return res.data;
        },
        {
            onSuccess: () => {
                queryClient.invalidateQueries("api-keys");
                setNewKey("");
                setShowAddForm(false);
            },
        }
    );

    const deleteMutation = useMutation(
        async (keyId: number) => {
            await api.delete(`/api/admin/api-keys/${keyId}`);
        },
        {
            onSuccess: () => {
                queryClient.invalidateQueries("api-keys");
            },
        }
    );

    const getProgressColor = (percentage: number) => {
        if (percentage < 50) return "bg-green-500";
        if (percentage < 80) return "bg-yellow-500";
        return "bg-red-500";
    };

    const getProgressGradient = (percentage: number) => {
        if (percentage < 50) return "from-green-400 to-green-600";
        if (percentage < 80) return "from-yellow-400 to-orange-500";
        return "from-red-400 to-pink-600";
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">API Keys Groq</h1>
                    <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                        Gerencie suas chaves de API com monitoramento de uso em tempo real
                    </p>
                </div>
                <button
                    onClick={() => setShowAddForm(!showAddForm)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                    <Plus className="h-5 w-5" />
                    Adicionar Chave
                </button>
            </div>

            {showAddForm && (
                <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                        Nova Chave API
                    </h3>
                    <div className="flex gap-3">
                        <input
                            type="text"
                            value={newKey}
                            onChange={(e) => setNewKey(e.target.value)}
                            placeholder="gsk_..."
                            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                        <button
                            onClick={() => addMutation.mutate(newKey)}
                            disabled={!newKey || addMutation.isLoading}
                            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                        >
                            {addMutation.isLoading ? "Adicionando..." : "Adicionar"}
                        </button>
                    </div>
                </div>
            )}

            <div className="grid gap-6">
                {keys?.map((apiKey) => {
                    const usagePercentage = (apiKey.used_today / apiKey.daily_limit) * 100;
                    const remaining = apiKey.daily_limit - apiKey.used_today;

                    return (
                        <div
                            key={apiKey.id}
                            className="bg-white dark:bg-gray-800 shadow rounded-lg p-6 border border-gray-200 dark:border-gray-700"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-lg">
                                        <Key className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <code className="text-sm font-mono text-gray-900 dark:text-white">
                                                {apiKey.key.substring(0, 20)}...
                                            </code>
                                            <span
                                                className={`px-2 py-1 text-xs rounded-full ${apiKey.status
                                                        ? "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200"
                                                        : "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200"
                                                    }`}
                                            >
                                                {apiKey.status ? "Ativa" : "Inativa"}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                                            Último uso: {apiKey.last_used ? new Date(apiKey.last_used).toLocaleString() : "Nunca"}
                                        </p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => deleteMutation.mutate(apiKey.id)}
                                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                >
                                    <Trash2 className="h-5 w-5" />
                                </button>
                            </div>

                            {/* Progress Bar Estilizada */}
                            <div className="space-y-3">
                                <div className="flex items-center justify-between text-sm">
                                    <div className="flex items-center gap-2">
                                        <Activity className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                                        <span className="font-medium text-gray-700 dark:text-gray-300">
                                            Uso Hoje
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-gray-600 dark:text-gray-400">
                                            {apiKey.used_today.toLocaleString()} / {apiKey.daily_limit.toLocaleString()}
                                        </span>
                                        <span className="font-semibold text-gray-900 dark:text-white">
                                            {usagePercentage.toFixed(1)}%
                                        </span>
                                    </div>
                                </div>

                                {/* Barra de Progresso com Gradiente */}
                                <div className="relative h-8 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden shadow-inner">
                                    <div
                                        className={`h-full bg-gradient-to-r ${getProgressGradient(usagePercentage)} transition-all duration-500 ease-out relative`}
                                        style={{ width: `${Math.min(usagePercentage, 100)}%` }}
                                    >
                                        {/* Efeito de brilho animado */}
                                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>

                                        {/* Padrão de listras */}
                                        <div className="absolute inset-0 opacity-20"
                                            style={{
                                                backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,.1) 10px, rgba(255,255,255,.1) 20px)'
                                            }}
                                        ></div>
                                    </div>

                                    {/* Texto dentro da barra */}
                                    {usagePercentage > 10 && (
                                        <div className="absolute inset-0 flex items-center px-4">
                                            <span className="text-xs font-bold text-white drop-shadow-lg">
                                                {apiKey.used_today.toLocaleString()} requisições
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {/* Estatísticas */}
                                <div className="grid grid-cols-3 gap-4 pt-2">
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                                            {remaining.toLocaleString()}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400">Restantes</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                                            {apiKey.used_today.toLocaleString()}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400">Usadas</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                                            {apiKey.daily_limit.toLocaleString()}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400">Limite</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}

                {(!keys || keys.length === 0) && (
                    <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-600">
                        <Key className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-600 dark:text-gray-400">Nenhuma chave API cadastrada</p>
                        <button
                            onClick={() => setShowAddForm(true)}
                            className="mt-4 text-primary-600 dark:text-primary-400 hover:underline"
                        >
                            Adicionar primeira chave
                        </button>
                    </div>
                )}
            </div>

            <style jsx>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
        </div>
    );
}
