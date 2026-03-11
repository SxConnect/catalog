"use client";

import { useState } from "react";
import { Globe, Link as LinkIcon, Search, Download, Loader, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import api from "@/lib/api";
import { useMutation, useQuery } from "react-query";

type SitemapUrl = {
    url: string;
    lastmod?: string;
    priority?: string;
    changefreq?: string;
};

type ProductData = {
    source_url: string;
    name: string;
    brand?: string;
    ean?: string;
    price?: number;
    description?: string;
    category?: string;
    images: string[];
    specifications?: Record<string, string>;
};

export default function SitemapImportPage() {
    const [sitemapUrl, setSitemapUrl] = useState("");
    const [urlFilter, setUrlFilter] = useState("/produto/");
    const [maxProducts, setMaxProducts] = useState(50);
    const [catalogId, setCatalogId] = useState(1);
    const [previewUrls, setPreviewUrls] = useState<SitemapUrl[]>([]);
    const [testProduct, setTestProduct] = useState<ProductData | null>(null);
    const [testUrl, setTestUrl] = useState("");

    // Preview sitemap
    const previewMutation = useMutation(
        async () => {
            const res = await api.post("/api/sitemap/preview", {
                sitemap_url: sitemapUrl,
                url_filter: urlFilter || undefined,
                max_urls: 10,
            });
            return res.data;
        },
        {
            onSuccess: (data) => {
                setPreviewUrls(data.sample_urls);
            },
            onError: (error: any) => {
                alert(`Erro ao buscar sitemap: ${error.response?.data?.detail || error.message}`);
            },
        }
    );

    // Test scrape
    const testScrapeMutation = useMutation(
        async (url: string) => {
            const res = await api.post("/api/sitemap/test-scrape", { url });
            return res.data;
        },
        {
            onSuccess: (data) => {
                setTestProduct(data.product_data);
            },
            onError: (error: any) => {
                alert(`Erro ao testar URL: ${error.response?.data?.detail || error.message}`);
            },
        }
    );

    // Import products
    const importMutation = useMutation(
        async () => {
            const res = await api.post("/api/sitemap/import", {
                sitemap_url: sitemapUrl,
                catalog_id: catalogId,
                url_filter: urlFilter || undefined,
                max_products: maxProducts,
                auto_save: true,
            });
            return res.data;
        },
        {
            onSuccess: (data) => {
                alert(`Sucesso! ${data.products_saved} produtos importados.`);
            },
            onError: (error: any) => {
                alert(`Erro ao importar: ${error.response?.data?.detail || error.message}`);
            },
        }
    );

    const handlePreview = () => {
        if (!sitemapUrl) {
            alert("Digite a URL do sitemap");
            return;
        }
        previewMutation.mutate();
    };

    const handleTestScrape = (url?: string) => {
        const urlToTest = url || testUrl;
        if (!urlToTest) {
            alert("Digite uma URL para testar");
            return;
        }
        testScrapeMutation.mutate(urlToTest);
    };

    const handleImport = () => {
        if (!sitemapUrl) {
            alert("Digite a URL do sitemap");
            return;
        }
        if (confirm(`Importar até ${maxProducts} produtos do sitemap?`)) {
            importMutation.mutate();
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Importar via Sitemap</h1>
                <p className="mt-1 text-sm text-gray-600">
                    Extraia produtos automaticamente de sitemaps XML de e-commerce
                </p>
            </div>

            {/* Configuração */}
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Configuração</h2>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            URL do Sitemap
                        </label>
                        <div className="flex gap-2">
                            <input
                                type="url"
                                value={sitemapUrl}
                                onChange={(e) => setSitemapUrl(e.target.value)}
                                placeholder="https://www.exemplo.com.br/sitemap.xml"
                                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            />
                            <button
                                onClick={handlePreview}
                                disabled={previewMutation.isLoading}
                                className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
                            >
                                {previewMutation.isLoading ? (
                                    <Loader className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Search className="h-4 w-4" />
                                )}
                                Preview
                            </button>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Filtro de URL (regex)
                            </label>
                            <input
                                type="text"
                                value={urlFilter}
                                onChange={(e) => setUrlFilter(e.target.value)}
                                placeholder="/produto/"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Ex: /produto/, /item/, .*-\d+$
                            </p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Máximo de Produtos
                            </label>
                            <input
                                type="number"
                                value={maxProducts}
                                onChange={(e) => setMaxProducts(parseInt(e.target.value))}
                                min="1"
                                max="1000"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                ID do Catálogo
                            </label>
                            <input
                                type="number"
                                value={catalogId}
                                onChange={(e) => setCatalogId(parseInt(e.target.value))}
                                min="1"
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Preview URLs */}
            {previewUrls.length > 0 && (
                <div className="bg-white shadow rounded-lg p-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">
                        Preview - {previewUrls.length} URLs encontradas
                    </h2>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {previewUrls.map((item, idx) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-gray-900 truncate">{item.url}</p>
                                    <div className="flex gap-4 text-xs text-gray-500 mt-1">
                                        {item.lastmod && <span>Atualizado: {item.lastmod}</span>}
                                        {item.priority && <span>Prioridade: {item.priority}</span>}
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleTestScrape(item.url)}
                                    className="ml-4 text-sm text-primary-600 hover:text-primary-700"
                                >
                                    Testar
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Test Scrape */}
            <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Testar Extração</h2>

                <div className="flex gap-2 mb-4">
                    <input
                        type="url"
                        value={testUrl}
                        onChange={(e) => setTestUrl(e.target.value)}
                        placeholder="https://www.exemplo.com.br/produto/123"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    />
                    <button
                        onClick={() => handleTestScrape()}
                        disabled={testScrapeMutation.isLoading}
                        className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                    >
                        {testScrapeMutation.isLoading ? (
                            <Loader className="h-4 w-4 animate-spin" />
                        ) : (
                            <Search className="h-4 w-4" />
                        )}
                        Testar
                    </button>
                </div>

                {testProduct && (
                    <div className="border border-gray-200 rounded-lg p-4 space-y-3">
                        <div className="flex items-start justify-between">
                            <div className="flex-1">
                                <h3 className="font-semibold text-gray-900">{testProduct.name}</h3>
                                {testProduct.brand && (
                                    <p className="text-sm text-gray-600">Marca: {testProduct.brand}</p>
                                )}
                            </div>
                            {testProduct.price && (
                                <span className="text-lg font-bold text-green-600">
                                    R$ {testProduct.price.toFixed(2)}
                                </span>
                            )}
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                            {testProduct.ean && (
                                <div>
                                    <span className="text-gray-600">EAN:</span>
                                    <span className="ml-2 font-medium">{testProduct.ean}</span>
                                </div>
                            )}
                            {testProduct.category && (
                                <div>
                                    <span className="text-gray-600">Categoria:</span>
                                    <span className="ml-2 font-medium">{testProduct.category}</span>
                                </div>
                            )}
                        </div>

                        {testProduct.description && (
                            <div>
                                <p className="text-sm text-gray-600 mb-1">Descrição:</p>
                                <p className="text-sm text-gray-800">{testProduct.description}</p>
                            </div>
                        )}

                        {testProduct.images.length > 0 && (
                            <div>
                                <p className="text-sm text-gray-600 mb-2">Imagens ({testProduct.images.length}):</p>
                                <div className="flex gap-2 overflow-x-auto">
                                    {testProduct.images.map((img, idx) => (
                                        <img
                                            key={idx}
                                            src={img}
                                            alt={`Produto ${idx + 1}`}
                                            className="h-20 w-20 object-cover rounded border"
                                        />
                                    ))}
                                </div>
                            </div>
                        )}

                        {testProduct.specifications && Object.keys(testProduct.specifications).length > 0 && (
                            <div>
                                <p className="text-sm text-gray-600 mb-1">Especificações:</p>
                                <div className="text-sm space-y-1">
                                    {Object.entries(testProduct.specifications).map(([key, value]) => (
                                        <div key={key}>
                                            <span className="text-gray-600 capitalize">{key}:</span>
                                            <span className="ml-2">{value}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Import Button */}
            <div className="flex justify-end gap-4">
                <button
                    onClick={handleImport}
                    disabled={!sitemapUrl || importMutation.isLoading}
                    className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {importMutation.isLoading ? (
                        <>
                            <Loader className="h-5 w-5 animate-spin" />
                            Importando...
                        </>
                    ) : (
                        <>
                            <Download className="h-5 w-5" />
                            Importar Produtos
                        </>
                    )}
                </button>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex gap-3">
                    <AlertCircle className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-800">
                        <p className="font-semibold mb-1">Como funciona:</p>
                        <ol className="list-decimal list-inside space-y-1">
                            <li>Cole a URL do sitemap.xml do site</li>
                            <li>Use o filtro para selecionar apenas URLs de produtos</li>
                            <li>Teste uma URL para ver os dados extraídos</li>
                            <li>Clique em "Importar Produtos" para processar todos</li>
                        </ol>
                        <p className="mt-2">
                            O sistema extrai automaticamente: nome, marca, EAN, preço, descrição, categoria, imagens e especificações.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
