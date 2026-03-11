"use client";

import { useState } from "react";
import { useQuery } from "react-query";
import { Package, Search, Filter, Download, Eye } from "lucide-react";
import api from "@/lib/api";

type Product = {
    id: number;
    ean: string;
    name: string;
    brand: string;
    category: string;
    description: string;
    images: string[];
    confidence_score: number;
    source_catalog: string;
    created_at: string;
};

export default function ProductsPage() {
    const [searchTerm, setSearchTerm] = useState("");
    const [filterBrand, setFilterBrand] = useState("");
    const [filterEan, setFilterEan] = useState("");
    const [page, setPage] = useState(0);
    const [limit] = useState(20);
    const [sortBy, setSortBy] = useState<"name" | "brand" | "created_at">("name");
    const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");

    const { data, isLoading, error } = useQuery(
        ["products", page, limit, searchTerm, filterBrand, filterEan, sortBy, sortOrder],
        async () => {
            const params = new URLSearchParams({
                skip: (page * limit).toString(),
                limit: limit.toString(),
            });

            if (searchTerm) params.append("q", searchTerm);
            if (filterBrand) params.append("brand", filterBrand);
            if (filterEan) params.append("ean", filterEan);
            if (sortBy) params.append("sort_by", sortBy);
            if (sortOrder) params.append("sort_order", sortOrder);

            const res = await api.get(`/api/products/search?${params.toString()}`);
            return res.data;
        },
        {
            keepPreviousData: true,
        }
    );

    const handleSort = (field: "name" | "brand" | "created_at") => {
        if (sortBy === field) {
            setSortOrder(sortOrder === "asc" ? "desc" : "asc");
        } else {
            setSortBy(field);
            setSortOrder("asc");
        }
    };

    const exportCSV = async () => {
        try {
            const res = await api.get("/api/products/export/csv", {
                responseType: "blob",
            });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", `products_${new Date().toISOString()}.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();
        } catch (error) {
            alert("Erro ao exportar CSV");
        }
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">Erro ao carregar produtos</p>
            </div>
        );
    }

    const products = data?.products || [];
    const total = data?.total || 0;
    const totalPages = Math.ceil(total / limit);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-foreground">Produtos</h1>
                    <p className="mt-1 text-sm text-foreground/60">
                        {total} produtos cadastrados
                    </p>
                </div>
                <button
                    onClick={exportCSV}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                >
                    <Download className="h-5 w-5" />
                    Exportar CSV
                </button>
            </div>

            {/* Filters */}
            <div className="bg-card shadow rounded-lg p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Search */}
                    <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                            Buscar
                        </label>
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-foreground/40" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => {
                                    setSearchTerm(e.target.value);
                                    setPage(0);
                                }}
                                placeholder="Nome do produto..."
                                className="w-full pl-10 pr-3 py-2 border border-border rounded-md bg-background text-foreground"
                            />
                        </div>
                    </div>

                    {/* Filter Brand */}
                    <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                            Marca
                        </label>
                        <input
                            type="text"
                            value={filterBrand}
                            onChange={(e) => {
                                setFilterBrand(e.target.value);
                                setPage(0);
                            }}
                            placeholder="Filtrar por marca..."
                            className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                        />
                    </div>

                    {/* Filter EAN */}
                    <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                            EAN
                        </label>
                        <input
                            type="text"
                            value={filterEan}
                            onChange={(e) => {
                                setFilterEan(e.target.value);
                                setPage(0);
                            }}
                            placeholder="Código EAN..."
                            className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
                        />
                    </div>
                </div>
            </div>

            {/* Table */}
            <div className="bg-card shadow rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-border">
                        <thead className="bg-card">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-foreground/60 uppercase tracking-wider">
                                    Imagem
                                </th>
                                <th
                                    className="px-6 py-3 text-left text-xs font-medium text-foreground/60 uppercase tracking-wider cursor-pointer hover:text-foreground"
                                    onClick={() => handleSort("name")}
                                >
                                    Nome {sortBy === "name" && (sortOrder === "asc" ? "↑" : "↓")}
                                </th>
                                <th
                                    className="px-6 py-3 text-left text-xs font-medium text-foreground/60 uppercase tracking-wider cursor-pointer hover:text-foreground"
                                    onClick={() => handleSort("brand")}
                                >
                                    Marca {sortBy === "brand" && (sortOrder === "asc" ? "↑" : "↓")}
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-foreground/60 uppercase tracking-wider">
                                    EAN
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-foreground/60 uppercase tracking-wider">
                                    Categoria
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-foreground/60 uppercase tracking-wider">
                                    Confiança
                                </th>
                                <th
                                    className="px-6 py-3 text-left text-xs font-medium text-foreground/60 uppercase tracking-wider cursor-pointer hover:text-foreground"
                                    onClick={() => handleSort("created_at")}
                                >
                                    Data {sortBy === "created_at" && (sortOrder === "asc" ? "↑" : "↓")}
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-foreground/60 uppercase tracking-wider">
                                    Ações
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-card divide-y divide-border">
                            {products.map((product: Product) => (
                                <tr key={product.id} className="hover:bg-background/50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        {product.images && product.images.length > 0 ? (
                                            <img
                                                src={product.images[0]}
                                                alt={product.name}
                                                className="h-12 w-12 object-cover rounded"
                                            />
                                        ) : (
                                            <div className="h-12 w-12 bg-background rounded flex items-center justify-center">
                                                <Package className="h-6 w-6 text-foreground/40" />
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="text-sm font-medium text-foreground">
                                            {product.name}
                                        </div>
                                        {product.description && (
                                            <div className="text-sm text-foreground/60 truncate max-w-xs">
                                                {product.description}
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-foreground">{product.brand}</div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <code className="text-sm font-mono text-foreground/80">
                                            {product.ean || "-"}
                                        </code>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="px-2 py-1 text-xs rounded-full bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200">
                                            {product.category || "Sem categoria"}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <div className="w-16 bg-background rounded-full h-2 mr-2">
                                                <div
                                                    className="bg-green-500 h-2 rounded-full"
                                                    style={{
                                                        width: `${(product.confidence_score || 0) * 100}%`,
                                                    }}
                                                ></div>
                                            </div>
                                            <span className="text-sm text-foreground/60">
                                                {((product.confidence_score || 0) * 100).toFixed(0)}%
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-foreground/60">
                                        {new Date(product.created_at).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <button
                                            onClick={() => alert(`Ver detalhes do produto ${product.id}`)}
                                            className="text-primary-600 hover:text-primary-700"
                                        >
                                            <Eye className="h-5 w-5" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {products.length === 0 && (
                    <div className="text-center py-12">
                        <Package className="h-12 w-12 text-foreground/40 mx-auto mb-4" />
                        <p className="text-foreground/60">Nenhum produto encontrado</p>
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="bg-card px-6 py-4 flex items-center justify-between border-t border-border">
                        <div className="text-sm text-foreground/60">
                            Mostrando {page * limit + 1} a {Math.min((page + 1) * limit, total)} de{" "}
                            {total} produtos
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage(Math.max(0, page - 1))}
                                disabled={page === 0}
                                className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Anterior
                            </button>
                            <div className="flex items-center gap-2">
                                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                    const pageNum = Math.max(
                                        0,
                                        Math.min(page - 2 + i, totalPages - 1)
                                    );
                                    return (
                                        <button
                                            key={pageNum}
                                            onClick={() => setPage(pageNum)}
                                            className={`px-4 py-2 border rounded-md text-sm font-medium ${page === pageNum
                                                    ? "bg-primary-600 text-white border-primary-600"
                                                    : "border-border text-foreground hover:bg-background"
                                                }`}
                                        >
                                            {pageNum + 1}
                                        </button>
                                    );
                                })}
                            </div>
                            <button
                                onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                                disabled={page >= totalPages - 1}
                                className="px-4 py-2 border border-border rounded-md text-sm font-medium text-foreground hover:bg-background disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Próxima
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
