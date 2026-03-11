"use client";

import { useState, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import {
    Upload,
    FileText,
    CheckCircle,
    XCircle,
    Loader,
    Clock,
    Package,
    Play,
    Pause,
    Square,
    RotateCcw,
    Eye,
    AlertCircle
} from "lucide-react";
import api from "@/lib/api";
import { useMutation, useQuery } from "react-query";

type EnrichmentField = {
    id: string;
    label: string;
    description: string;
    required: boolean;
};

type CatalogStatus = {
    catalog_id: number;
    filename: string;
    status: string;
    total_pages: number;
    processed_pages: number;
    progress_percentage: number;
    products_found: number;
    estimated_time_remaining_seconds: number | null;
    is_processing: boolean;
    is_completed: boolean;
    is_failed: boolean;
};

const ENRICHMENT_FIELDS: EnrichmentField[] = [
    { id: "name", label: "Nome do Produto", description: "Nome completo e descritivo", required: true },
    { id: "brand", label: "Marca", description: "Fabricante do produto", required: true },
    { id: "ean", label: "Código EAN", description: "Código de barras", required: true },
    { id: "category", label: "Categoria", description: "Classificação do produto", required: false },
    { id: "description", label: "Descrição", description: "Descrição detalhada", required: false },
    { id: "price", label: "Preço", description: "Valor de venda", required: false },
    { id: "weight", label: "Peso", description: "Peso do produto (ex: 1kg, 500g)", required: false },
    { id: "color", label: "Cor", description: "Cor principal do produto", required: false },
    { id: "dimensions", label: "Dimensões", description: "Altura x Largura x Profundidade", required: false },
    { id: "ingredients", label: "Ingredientes", description: "Composição do produto", required: false },
    { id: "nutritional_info", label: "Info. Nutricional", description: "Tabela nutricional", required: false },
    { id: "images", label: "Imagens", description: "Fotos do produto", required: false },
    { id: "stock", label: "Estoque", description: "Disponibilidade", required: false },
];

export default function UploadPage() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [enrichmentEnabled, setEnrichmentEnabled] = useState(true);
    const [selectedFields, setSelectedFields] = useState<string[]>(
        ENRICHMENT_FIELDS.filter(f => f.required).map(f => f.id)
    );
    const [processingCatalogId, setProcessingCatalogId] = useState<number | null>(null);

    const { data: settings } = useQuery("settings", async () => {
        const res = await api.get("/api/admin/settings");
        return res.data;
    });

    // Polling do status do catálogo em processamento
    const { data: catalogStatus, refetch: refetchStatus } = useQuery<CatalogStatus>(
        ["catalogStatus", processingCatalogId],
        async () => {
            if (!processingCatalogId) return null;
            const res = await api.get(`/api/status/catalog/${processingCatalogId}/status`);
            return res.data;
        },
        {
            enabled: !!processingCatalogId,
            refetchInterval: (data) => {
                // Parar polling se completou ou falhou
                if (data?.is_completed || data?.is_failed) {
                    return false;
                }
                return 2000; // Poll a cada 2 segundos
            }
        }
    );

    // Buscar catálogos recentes
    const { data: recentCatalogs, refetch: refetchRecent } = useQuery(
        "recentCatalogs",
        async () => {
            const res = await api.get("/api/status/recent?limit=5");
            return res.data.catalogs;
        },
        {
            refetchInterval: 5000 // Atualizar a cada 5 segundos
        }
    );

    // Mutation para controlar processamento
    const controlProcessingMutation = useMutation(
        async ({ catalogId, action }: { catalogId: number; action: 'pause' | 'resume' | 'stop' | 'restart' }) => {
            const res = await api.post(`/api/catalog/${catalogId}/control`, { action });
            return res.data;
        },
        {
            onSuccess: () => {
                refetchRecent();
                refetchStatus();
            }
        }
    );

    const uploadMutation = useMutation(
        async (data: FormData) => {
            const res = await api.post("/api/catalog/upload", data, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            return res.data;
        },
        {
            onSuccess: (data) => {
                setSelectedFile(null);
                setProcessingCatalogId(data.catalog_id);
                refetchRecent();
            },
            onError: (error: any) => {
                alert(`Erro ao enviar: ${error.response?.data?.detail || error.message}`);
            },
        }
    );

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        accept: { "application/pdf": [".pdf"] },
        maxFiles: 1,
        onDrop: (acceptedFiles) => {
            if (acceptedFiles.length > 0) {
                setSelectedFile(acceptedFiles[0]);
            }
        },
    });

    const toggleField = (fieldId: string) => {
        const field = ENRICHMENT_FIELDS.find(f => f.id === fieldId);
        if (field?.required) return;

        setSelectedFields(prev =>
            prev.includes(fieldId)
                ? prev.filter(id => id !== fieldId)
                : [...prev, fieldId]
        );
    };

    const handleUpload = () => {
        if (!selectedFile) return;

        const formData = new FormData();
        formData.append("file", selectedFile);
        formData.append("enrich", enrichmentEnabled.toString());
        formData.append("fields", JSON.stringify(selectedFields));

        uploadMutation.mutate(formData);
    };

    const handleControlProcessing = (catalogId: number, action: 'pause' | 'resume' | 'stop' | 'restart') => {
        controlProcessingMutation.mutate({ catalogId, action });
    };

    const formatTime = (seconds: number | null) => {
        if (!seconds) return "Calculando...";
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}m ${secs}s`;
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case "completed": return "text-green-600 bg-green-50";
            case "processing": return "text-blue-600 bg-blue-50";
            case "paused": return "text-yellow-600 bg-yellow-50";
            case "failed": return "text-red-600 bg-red-50";
            default: return "text-gray-600 bg-gray-50";
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "completed": return <CheckCircle className="h-5 w-5" />;
            case "processing": return <Loader className="h-5 w-5 animate-spin" />;
            case "paused": return <Pause className="h-5 w-5" />;
            case "failed": return <XCircle className="h-5 w-5" />;
            default: return <Clock className="h-5 w-5" />;
        }
    };

    const getProgressColor = (status: string, percentage: number) => {
        if (status === "completed") return "bg-green-500";
        if (status === "failed") return "bg-red-500";
        if (status === "paused") return "bg-yellow-500";
        if (percentage > 0) return "bg-blue-500";
        return "bg-gray-300";
    };

    const getStatusBadgeColor = (status: string) => {
        switch (status) {
            case "completed": return "bg-green-100 text-green-800";
            case "processing": return "bg-blue-100 text-blue-800";
            case "paused": return "bg-yellow-100 text-yellow-800";
            case "failed": return "bg-red-100 text-red-800";
            default: return "bg-gray-100 text-gray-800";
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Upload de Catálogo</h1>
                <p className="mt-1 text-sm text-gray-600">
                    Envie um catálogo em PDF para processamento automático
                </p>
            </div>

            {/* Status do Processamento Atual */}
            {catalogStatus && catalogStatus.is_processing && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                            <Loader className="h-6 w-6 text-blue-600 animate-spin" />
                            <div>
                                <h3 className="font-semibold text-blue-900">Processando: {catalogStatus.filename}</h3>
                                <p className="text-sm text-blue-700">
                                    Página {catalogStatus.processed_pages} de {catalogStatus.total_pages}
                                </p>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-bold text-blue-900">{catalogStatus.progress_percentage}%</div>
                            <div className="text-sm text-blue-700">
                                {catalogStatus.products_found} produtos encontrados
                            </div>
                        </div>
                    </div>

                    {/* Barra de Progresso */}
                    <div className="w-full bg-blue-200 rounded-full h-3 mb-3">
                        <div
                            className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                            style={{ width: `${catalogStatus.progress_percentage}%` }}
                        />
                    </div>

                    <div className="flex items-center justify-between text-sm text-blue-700">
                        <span>Tempo estimado: {formatTime(catalogStatus.estimated_time_remaining_seconds)}</span>
                        <span>Aguarde o processamento terminar...</span>
                    </div>
                </div>
            )}

            {/* Resultado do Processamento */}
            {catalogStatus && catalogStatus.is_completed && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <div className="flex items-center gap-3 mb-3">
                        <CheckCircle className="h-6 w-6 text-green-600" />
                        <div>
                            <h3 className="font-semibold text-green-900">Processamento Concluído!</h3>
                            <p className="text-sm text-green-700">{catalogStatus.filename}</p>
                        </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-center">
                        <div className="bg-white rounded-lg p-3">
                            <div className="text-2xl font-bold text-green-600">{catalogStatus.total_pages}</div>
                            <div className="text-sm text-gray-600">Páginas</div>
                        </div>
                        <div className="bg-white rounded-lg p-3">
                            <div className="text-2xl font-bold text-green-600">{catalogStatus.products_found}</div>
                            <div className="text-sm text-gray-600">Produtos</div>
                        </div>
                        <div className="bg-white rounded-lg p-3">
                            <div className="text-2xl font-bold text-green-600">100%</div>
                            <div className="text-sm text-gray-600">Completo</div>
                        </div>
                    </div>
                    <button
                        onClick={() => setProcessingCatalogId(null)}
                        className="mt-4 w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                        Processar Novo Catálogo
                    </button>
                </div>
            )}

            {/* Upload Area */}
            {!catalogStatus?.is_processing && (
                <>
                    <div className="bg-white shadow rounded-lg p-6">
                        <div
                            {...getRootProps()}
                            className={`
                border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
                transition-colors
                ${isDragActive ? "border-primary-500 bg-primary-50" : "border-gray-300 hover:border-primary-400"}
                ${selectedFile ? "bg-green-50 border-green-500" : ""}
              `}
                        >
                            <input {...getInputProps()} />
                            <div className="flex flex-col items-center">
                                {selectedFile ? (
                                    <>
                                        <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
                                        <p className="text-lg font-medium text-gray-900">{selectedFile.name}</p>
                                        <p className="text-sm text-gray-500 mt-1">
                                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </>
                                ) : (
                                    <>
                                        <Upload className="h-12 w-12 text-gray-400 mb-4" />
                                        <p className="text-lg font-medium text-gray-900">
                                            {isDragActive ? "Solte o arquivo aqui" : "Arraste um PDF ou clique para selecionar"}
                                        </p>
                                        <p className="text-sm text-gray-500 mt-1">
                                            Apenas arquivos PDF são aceitos (máx. 100MB)
                                        </p>
                                    </>
                                )}
                            </div>
                        </div>

                        {selectedFile && (
                            <button
                                onClick={() => setSelectedFile(null)}
                                className="mt-4 text-sm text-red-600 hover:text-red-700"
                            >
                                Remover arquivo
                            </button>
                        )}
                    </div>

                    {/* Enrichment Options */}
                    <div className="bg-white shadow rounded-lg p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h2 className="text-lg font-semibold text-gray-900">
                                    Enriquecimento de Dados
                                </h2>
                                <p className="text-sm text-gray-600">
                                    Buscar informações faltantes via web scraping
                                </p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={enrichmentEnabled}
                                    onChange={(e) => setEnrichmentEnabled(e.target.checked)}
                                    className="sr-only peer"
                                />
                                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                            </label>
                        </div>

                        {enrichmentEnabled && (
                            <div className="space-y-3">
                                <p className="text-sm text-gray-600 mb-4">
                                    Selecione os campos que deseja enriquecer com dados da web:
                                </p>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                    {ENRICHMENT_FIELDS.map((field) => (
                                        <label
                                            key={field.id}
                                            className={`
                        flex items-start p-3 border rounded-lg cursor-pointer
                        transition-colors
                        ${selectedFields.includes(field.id)
                                                    ? "border-primary-500 bg-primary-50"
                                                    : "border-gray-200 hover:border-gray-300"
                                                }
                        ${field.required ? "opacity-75 cursor-not-allowed" : ""}
                      `}
                                        >
                                            <input
                                                type="checkbox"
                                                checked={selectedFields.includes(field.id)}
                                                onChange={() => toggleField(field.id)}
                                                disabled={field.required}
                                                className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                                            />
                                            <div className="ml-3 flex-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm font-medium text-gray-900">
                                                        {field.label}
                                                    </span>
                                                    {field.required && (
                                                        <span className="text-xs text-red-600">*</span>
                                                    )}
                                                </div>
                                                <p className="text-xs text-gray-500 mt-0.5">
                                                    {field.description}
                                                </p>
                                            </div>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Upload Button */}
                    <div className="flex justify-end">
                        <button
                            onClick={handleUpload}
                            disabled={!selectedFile || uploadMutation.isLoading}
                            className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            {uploadMutation.isLoading ? (
                                <>
                                    <Loader className="h-5 w-5 animate-spin" />
                                    Enviando...
                                </>
                            ) : (
                                <>
                                    <Upload className="h-5 w-5" />
                                    Enviar e Processar
                                </>
                            )}
                        </button>
                    </div>
                </>
            )}

            {/* Catálogos Processados */}
            <div className="bg-white shadow rounded-lg p-6">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold text-gray-900">
                        Catálogos Processados
                    </h2>
                    <button
                        onClick={() => refetchRecent()}
                        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
                    >
                        <RotateCcw className="h-4 w-4" />
                        Atualizar
                    </button>
                </div>

                {recentCatalogs && recentCatalogs.length > 0 ? (
                    <div className="space-y-4">
                        {recentCatalogs.map((catalog: any) => (
                            <div
                                key={catalog.id}
                                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
                            >
                                {/* Header do catálogo */}
                                <div className="flex items-center justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2 rounded-lg ${getStatusColor(catalog.status)}`}>
                                            {getStatusIcon(catalog.status)}
                                        </div>
                                        <div>
                                            <h3 className="font-medium text-gray-900">{catalog.filename}</h3>
                                            <p className="text-sm text-gray-500">
                                                ID: {catalog.id} • Criado em {formatDate(catalog.created_at)}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${getStatusBadgeColor(catalog.status)}`}>
                                            {catalog.status === "completed" ? "Concluído" :
                                                catalog.status === "processing" ? "Processando" :
                                                    catalog.status === "paused" ? "Pausado" :
                                                        catalog.status === "failed" ? "Falhou" : catalog.status}
                                        </span>
                                    </div>
                                </div>

                                {/* Barra de progresso */}
                                <div className="mb-3">
                                    <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                                        <span>Progresso: {catalog.progress_percentage}%</span>
                                        <span>
                                            Página {catalog.processed_pages} de {catalog.total_pages}
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all duration-300 ${getProgressColor(catalog.status, catalog.progress_percentage)}`}
                                            style={{ width: `${catalog.progress_percentage}%` }}
                                        />
                                    </div>
                                </div>

                                {/* Estatísticas */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                    <div className="text-center">
                                        <div className="text-lg font-semibold text-gray-900">
                                            {catalog.products_found}
                                        </div>
                                        <div className="text-xs text-gray-500">Produtos</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-lg font-semibold text-gray-900">
                                            {catalog.total_pages}
                                        </div>
                                        <div className="text-xs text-gray-500">Páginas</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-lg font-semibold text-gray-900">
                                            {catalog.processed_pages}
                                        </div>
                                        <div className="text-xs text-gray-500">Processadas</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-lg font-semibold text-gray-900">
                                            {catalog.estimated_time_remaining_seconds ?
                                                formatTime(catalog.estimated_time_remaining_seconds) :
                                                catalog.status === "completed" ? "Concluído" : "-"}
                                        </div>
                                        <div className="text-xs text-gray-500">Tempo restante</div>
                                    </div>
                                </div>

                                {/* Controles de processamento */}
                                <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                                    <div className="flex items-center gap-2">
                                        {catalog.status === "processing" && (
                                            <>
                                                <button
                                                    onClick={() => handleControlProcessing(catalog.id, 'pause')}
                                                    disabled={controlProcessingMutation.isLoading}
                                                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-yellow-700 bg-yellow-100 hover:bg-yellow-200 rounded-md transition-colors disabled:opacity-50"
                                                    title="Pausar processamento"
                                                >
                                                    <Pause className="h-4 w-4" />
                                                    Pausar
                                                </button>
                                                <button
                                                    onClick={() => handleControlProcessing(catalog.id, 'stop')}
                                                    disabled={controlProcessingMutation.isLoading}
                                                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-700 bg-red-100 hover:bg-red-200 rounded-md transition-colors disabled:opacity-50"
                                                    title="Parar processamento"
                                                >
                                                    <Square className="h-4 w-4" />
                                                    Parar
                                                </button>
                                            </>
                                        )}

                                        {catalog.status === "paused" && (
                                            <>
                                                <button
                                                    onClick={() => handleControlProcessing(catalog.id, 'resume')}
                                                    disabled={controlProcessingMutation.isLoading}
                                                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-green-700 bg-green-100 hover:bg-green-200 rounded-md transition-colors disabled:opacity-50"
                                                    title="Retomar processamento"
                                                >
                                                    <Play className="h-4 w-4" />
                                                    Retomar
                                                </button>
                                                <button
                                                    onClick={() => handleControlProcessing(catalog.id, 'stop')}
                                                    disabled={controlProcessingMutation.isLoading}
                                                    className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-700 bg-red-100 hover:bg-red-200 rounded-md transition-colors disabled:opacity-50"
                                                    title="Parar processamento"
                                                >
                                                    <Square className="h-4 w-4" />
                                                    Parar
                                                </button>
                                            </>
                                        )}

                                        {(catalog.status === "failed" || catalog.status === "stopped") && (
                                            <button
                                                onClick={() => handleControlProcessing(catalog.id, 'restart')}
                                                disabled={controlProcessingMutation.isLoading}
                                                className="flex items-center gap-1 px-3 py-1.5 text-sm text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-md transition-colors disabled:opacity-50"
                                                title="Reiniciar processamento"
                                            >
                                                <RotateCcw className="h-4 w-4" />
                                                Reiniciar
                                            </button>
                                        )}

                                        {catalog.status === "completed" && (
                                            <div className="flex items-center gap-1 text-sm text-green-700">
                                                <CheckCircle className="h-4 w-4" />
                                                Processamento concluído
                                            </div>
                                        )}
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => setProcessingCatalogId(catalog.id)}
                                            className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
                                            title="Ver detalhes"
                                        >
                                            <Eye className="h-4 w-4" />
                                            Detalhes
                                        </button>

                                        {catalog.products_found > 0 && (
                                            <a
                                                href="/dashboard/products"
                                                className="flex items-center gap-1 px-3 py-1.5 text-sm text-primary-700 bg-primary-100 hover:bg-primary-200 rounded-md transition-colors"
                                                title="Ver produtos"
                                            >
                                                <Package className="h-4 w-4" />
                                                Ver Produtos
                                            </a>
                                        )}
                                    </div>
                                </div>

                                {/* Alertas e mensagens */}
                                {catalog.status === "failed" && (
                                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                                        <div className="flex items-center gap-2 text-sm text-red-800">
                                            <AlertCircle className="h-4 w-4" />
                                            <span>Processamento falhou. Verifique o arquivo e tente novamente.</span>
                                        </div>
                                    </div>
                                )}

                                {catalog.status === "processing" && catalog.estimated_time_remaining_seconds && (
                                    <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                                        <div className="flex items-center gap-2 text-sm text-blue-800">
                                            <Clock className="h-4 w-4" />
                                            <span>
                                                Tempo estimado restante: {formatTime(catalog.estimated_time_remaining_seconds)}
                                            </span>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12">
                        <FileText className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum catálogo processado</h3>
                        <p className="mt-1 text-sm text-gray-500">
                            Faça upload de um arquivo PDF para começar o processamento.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
