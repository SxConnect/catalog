"use client";

import { useState, useEffect } from "react";
import { useDropzone } from "react-dropzone";
import { Upload, FileText, CheckCircle, XCircle, Loader, Clock, Package } from "lucide-react";
import api from "@/lib/api";
import { useMutation, useQuery } from "react-query";

type EnrichmentField = {
    id: string;
    label: string;
    description: string;
    required: boolean;
};

type CatalogStatus = {
    id: number;
    filename: string;
    status: string;
    total_pages: number;
    processed_pages: number;
    products_found: number;
    created_at: string;
};

const ENRICHMENT_FIELDS: EnrichmentField[] = [
    { id: "name", label: "Nome do Produto", description: "Nome completo e descritivo", required: true },
    { id: "brand", label: "Marca", description: "Fabricante do produto", required: true },
    { id: "ean", label: "Código EAN", description: "Código de barras", required: true },
    { id: "category", label: "Categoria", description: "Classificação do produto", required: false },
    { id: "description", label: "Descrição", description: "Descrição detalhada", required: false },
    { id: "price", label: "Preço", description: "Valor de venda", required: false },
    { id: "weight", label: "Peso", description: "Peso do produto", required: false },
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
    const [uploadProgress, setUploadProgress] = useState(0);
    const [processingCatalogId, setProcessingCatalogId] = useState<number | null>(null);

    const { data: settings } = useQuery("settings", async () => {
        const res = await api.get("/api/admin/settings");
        return res.data;
    });

    // Polling para status do catálogo em processamento
    const { data: catalogStatus } = useQuery(
        ["catalog-status", processingCatalogId],
        async () => {
            if (!processingCatalogId) return null;
            const res = await api.get(`/api/catalog/${processingCatalogId}`);
            return res.data;
        },
        {
            enabled: !!processingCatalogId,
            refetchInterval: (data) => {
                if (data?.status === "completed" || data?.status === "failed") {
                    return false;
                }
                return 2000;
            },
        }
    );

    // Buscar uploads recentes
    const { data: recentUploads } = useQuery("recent-uploads", async () => {
        const res = await api.get("/api/catalog/list?limit=5");
        return res.data.catalogs || [];
    });

    useEffect(() => {
        if (catalogStatus?.status === "completed") {
            setTimeout(() => {
                setProcessingCatalogId(null);
                setUploadProgress(0);
            }, 3000);
        }
    }, [catalogStatus?.status]);

    const uploadMutation = useMutation(
        async (data: FormData) => {
            const res = await api.post("/api/catalog/upload", data, {
                headers: { "Content-Type": "multipart/form-data" },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round(
                        (progressEvent.loaded * 100) / (progressEvent.total || 100)
                    );
                    setUploadProgress(percentCompleted);
                },
            });
            return res.data;
        },
        {
            onSuccess: (data) => {
                setSelectedFile(null);
                setProcessingCatalogId(data.catalog_id);
                alert("Catálogo enviado com sucesso! O processamento começará em breve.");
            },
            onError: (error: any) => {
                setUploadProgress(0);
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
                setUploadProgress(0);
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

    const getStatusColor = (status: string) => {
        switch (status) {
            case "completed": return "text-green-600 dark:text-green-400";
            case "processing": return "text-blue-600 dark:text-blue-400";
            case "failed": return "text-red-600 dark:text-red-400";
            default: return "text-gray-600 dark:text-gray-400";
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "completed": return <CheckCircle className="h-5 w-5" />;
            case "processing": return <Loader className="h-5 w-5 animate-spin" />;
            case "failed": return <XCircle className="h-5 w-5" />;
            default: return <Clock className="h-5 w-5" />;
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-foreground">Upload de Catálogo</h1>
                <p className="mt-1 text-sm text-foreground/60">
                    Envie um catálogo em PDF para processamento automático
                </p>
            </div>

            {/* Upload Area */}
            <div className="bg-card shadow rounded-lg p-6">
                <div
                    {...getRootProps()}
                    className={`
            border-2 border-dashed rounded-lg p-12 text-center cursor-pointer
            transition-colors
            ${isDragActive ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20" : "border-border hover:border-primary-400"}
            ${selectedFile ? "bg-green-50 dark:bg-green-900/20 border-green-500" : ""}
          `}
                >
                    <input {...getInputProps()} />
                    <div className="flex flex-col items-center">
                        {selectedFile ? (
                            <>
                                <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
                                <p className="text-lg font-medium text-foreground">{selectedFile.name}</p>
                                <p className="text-sm text-foreground/60 mt-1">
                                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                </p>
                            </>
                        ) : (
                            <>
                                <Upload className="h-12 w-12 text-foreground/40 mb-4" />
                                <p className="text-lg font-medium text-foreground">
                                    {isDragActive ? "Solte o arquivo aqui" : "Arraste um PDF ou clique para selecionar"}
                                </p>
                                <p className="text-sm text-foreground/60 mt-1">
                                    Apenas arquivos PDF são aceitos
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

                {/* Upload Progress */}
                {uploadProgress > 0 && uploadProgress < 100 && (
                    <div className="mt-4">
                        <div className="flex items-center justify-between text-sm mb-2">
                            <span className="text-foreground/60">Enviando...</span>
                            <span className="font-semibold text-foreground">{uploadProgress}%</span>
                        </div>
                        <div className="w-full bg-background rounded-full h-2">
                            <div
                                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                                style={{ width: `${uploadProgress}%` }}
                            ></div>
                        </div>
                    </div>
                )}

                {/* Processing Status */}
                {catalogStatus && catalogStatus.status === "processing" && (
                    <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                        <div className="flex items-center gap-3 mb-3">
                            <Loader className="h-5 w-5 text-blue-600 dark:text-blue-400 animate-spin" />
                            <div>
                                <p className="font-medium text-blue-900 dark:text-blue-100">
                                    Processando catálogo...
                                </p>
                                <p className="text-sm text-blue-700 dark:text-blue-300">
                                    {catalogStatus.filename}
                                </p>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-blue-700 dark:text-blue-300">
                                    Páginas processadas
                                </span>
                                <span className="font-semibold text-blue-900 dark:text-blue-100">
                                    {catalogStatus.processed_pages} / {catalogStatus.total_pages}
                                </span>
                            </div>
                            <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                                <div
                                    className="bg-blue-600 dark:bg-blue-400 h-2 rounded-full transition-all duration-300"
                                    style={{
                                        width: `${(catalogStatus.processed_pages / catalogStatus.total_pages) * 100}%`
                                    }}
                                ></div>
                            </div>
                            <p className="text-sm text-blue-700 dark:text-blue-300">
                                {catalogStatus.products_found} produtos encontrados
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Enrichment Options */}
            <div className="bg-card shadow rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h2 className="text-lg font-semibold text-foreground">
                            Enriquecimento de Dados
                        </h2>
                        <p className="text-sm text-foreground/60">
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
                        <div className="w-11 h-6 bg-gray-200 dark:bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                </div>

                {enrichmentEnabled && (
                    <div className="space-y-3">
                        <p className="text-sm text-foreground/60 mb-4">
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
                                            ? "border-primary-500 bg-primary-50 dark:bg-primary-900/20"
                                            : "border-border hover:border-border/80"
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
                                            <span className="text-sm font-medium text-foreground">
                                                {field.label}
                                            </span>
                                            {field.required && (
                                                <span className="text-xs text-red-600">*</span>
                                            )}
                                        </div>
                                        <p className="text-xs text-foreground/60 mt-0.5">
                                            {field.description}
                                        </p>
                                    </div>
                                </label>
                            ))}
                        </div>

                        {settings?.scraping_enabled && (
                            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                                <p className="text-sm text-blue-800 dark:text-blue-200">
                                    <strong>Configuração atual:</strong> {settings.extractions_per_second} extrações/segundo
                                    {settings.scraping_url && ` • Fonte: ${settings.scraping_url}`}
                                </p>
                            </div>
                        )}
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
                            Processando...
                        </>
                    ) : (
                        <>
                            <Upload className="h-5 w-5" />
                            Enviar Catálogo
                        </>
                    )}
                </button>
            </div>

            {/* Recent Uploads */}
            <div className="bg-card shadow rounded-lg p-6">
                <h2 className="text-lg font-semibold text-foreground mb-4">
                    Uploads Recentes
                </h2>
                {recentUploads && recentUploads.length > 0 ? (
                    <div className="space-y-3">
                        {recentUploads.map((catalog: CatalogStatus) => (
                            <div
                                key={catalog.id}
                                className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-background/50 transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`${getStatusColor(catalog.status)}`}>
                                        {getStatusIcon(catalog.status)}
                                    </div>
                                    <div>
                                        <p className="font-medium text-foreground">{catalog.filename}</p>
                                        <p className="text-sm text-foreground/60">
                                            {catalog.products_found} produtos • {catalog.processed_pages}/{catalog.total_pages} páginas
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className={`text-sm font-medium ${getStatusColor(catalog.status)}`}>
                                        {catalog.status === "completed" ? "Concluído" :
                                            catalog.status === "processing" ? "Processando" :
                                                catalog.status === "failed" ? "Falhou" : "Aguardando"}
                                    </p>
                                    <p className="text-xs text-foreground/60">
                                        {new Date(catalog.created_at).toLocaleString()}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8">
                        <Package className="h-12 w-12 text-foreground/40 mx-auto mb-3" />
                        <p className="text-foreground/60">Nenhum upload recente</p>
                    </div>
                )}
            </div>
        </div>
    );
}
