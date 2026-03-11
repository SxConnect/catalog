"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "react-query";
import {
    Package,
    Search,
    Filter,
    Edit3,
    Eye,
    Calendar,
    Star,
    Tag,
    Barcode
} from "lucide-react";
import api from "@/lib/api";
import ProductModal from "@/components/ProductModal";

type Product = {
    id: number;
    ean?: string;
    name: string;
    brand: string;
    category?: string;
    description?: string;
    images?: string[];
    attributes?: {
        price_avg?: number;
        weight?: string;
        color?: string;
        dimensions?: string;
        [key: string]: any;
    };
    ingredients?: string[];
    nutritional_info?: {
        protein?: number;
        fat?: number;
        fiber?: number;
        moisture?: number;
        ash?: number;
        energy?: number;
        [key: string]: number | undefined;
    };
    source_catalog?: string;
    confidence_score?: number;
    created_at: string;
    updated_at?: string;
};

export default function ProductsPage() {
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedBrand, setSelectedBrand] = useState("");
    const [selectedCategory, setSelectedCategory] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalMode, setModalMode] = useState<"view" | "edit">("view");

    const queryClient = useQueryClient();
    const limit = 20;

    // Buscar produtos
    const { data: productsData, isLoading } = useQuery(
        ["products", searchQuery, selectedBrand, selectedCategory, currentPage],
        async () => {
            const params = new URLSearchParams({
                skip: ((currentPage - 1) * limit).toString(),
                limit: limit.toString(),
                sort_by: "created_at",
                sort_order: "desc"
            });

            if (searchQuery) params.append("q", searchQuery);
            if (selectedBrand) params.append("brand", selectedBrand);
            if (selectedCategory) params.append("category", selectedCategory);

            const response = await api.get(`/api/products/search?${params}`);
            return response.data;
        },
        {
            keepPreviousData: true
        }
    );

    // Buscar marcas para filtro
    const { data: brands } = useQuery("brands", async () => {
        const response = await api.get("/api/products/search?limit=1000");
        const products = response.data.products || [];
        const uniqueBrands = [...new Set(products.map((p: Product) => p.brand).filter(Boolean))] as string[];
        return uniqueBrands.sort();
    });

    // Buscar categorias para filtro
    const { data: categories } = useQuery("categories", async () => {
        const response = await api.get("/api/products/search?limit=1000");
        const products = response.data.products || [];
        const uniqueCategories = [...new Set(products.map((p: Product) => p.category).filter(Boolean))] as string[];
        return uniqueCategories.sort();
    });

    // Mutation para atualizar produto
    const updateProductMutation = useMutation(
        async (updatedProduct: Partial<Product> & { id: number }) => {
            const response = await api.put(`/api/products/${updatedProduct.id}`, updatedProduct);
            return response.data;
        },
        {
            onSuccess: () => {
                queryClient.invalidateQueries("products");
                setIsModalOpen(false);
                setSelectedProduct(null);
            }
        }
    );

    const openModal = (product: Product, mode: "view" | "edit") => {
        setSelectedProduct(product);
        setModalMode(mode);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setSelectedProduct(null);
    };

    const handleSaveProduct = (updatedProduct: Product) => {
        updateProductMutation.mutate(updatedProduct);
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

    const getConfidenceColor = (score?: number) => {
        if (!score) return "text-gray-400";
        if (score >= 0.8) return "text-green-600";
        if (score >= 0.6) return "text-yellow-600";
        return "text-red-600";
    };

    const products = productsData?.products || [];
    const total = productsData?.total || 0;
    const totalPages = Math.ceil(total / limit);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Produtos</h1>
                    <p className="text-gray-600">
                        {total} produtos encontrados
                    </p>
                </div>
            </div>

            {/* Filtros */}
            <div className="bg-white shadow rounded-lg p-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {/* Busca */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                        <input
                            type="text"
                            placeholder="Buscar produtos..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                        />
                    </div>

                    {/* Filtro por marca */}
                    <select
                        value={selectedBrand}
                        onChange={(e) => setSelectedBrand(e.target.value)}
                        className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    >
                        <option value="">Todas as marcas</option>
                        {brands?.map((brand: string) => (
                            <option key={brand} value={brand}>
                                {brand}
                            </option>
                        ))}
                    </select>

                    {/* Filtro por categoria */}
                    <select
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                        className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                    >
                        <option value="">Todas as categorias</option>
                        {categories?.map((category: string) => (
                            <option key={category} value={category}>
                                {category}
                            </option>
                        ))}
                    </select>

                    {/* Botão limpar filtros */}
                    <button
                        onClick={() => {
                            setSearchQuery("");
                            setSelectedBrand("");
                            setSelectedCategory("");
                            setCurrentPage(1);
                        }}
                        className="flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                        <Filter className="h-4 w-4" />
                        Limpar
                    </button>
                </div>
            </div>

            {/* Lista de produtos */}
            <div className="bg-white shadow rounded-lg overflow-hidden">
                {isLoading ? (
                    <div className="p-8 text-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                        <p className="mt-2 text-gray-600">Carregando produtos...</p>
                    </div>
                ) : products.length === 0 ? (
                    <div className="p-8 text-center">
                        <Package className="mx-auto h-12 w-12 text-gray-400" />
                        <h3 className="mt-2 text-sm font-medium text-gray-900">Nenhum produto encontrado</h3>
                        <p className="mt-1 text-sm text-gray-500">
                            Tente ajustar os filtros ou fazer upload de um catálogo.
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Produto
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Marca
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Categoria
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        EAN
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Confiança
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Data
                                    </th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Ações
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {products.map((product: Product) => (
                                    <tr
                                        key={product.id}
                                        className="hover:bg-gray-50 cursor-pointer"
                                        onClick={() => openModal(product, "view")}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                {product.images && product.images.length > 0 ? (
                                                    <img
                                                        className="h-10 w-10 rounded-lg object-cover mr-3"
                                                        src={product.images[0]}
                                                        alt={product.name}
                                                        onError={(e) => {
                                                            e.currentTarget.style.display = 'none';
                                                        }}
                                                    />
                                                ) : (
                                                    <div className="h-10 w-10 rounded-lg bg-gray-200 flex items-center justify-center mr-3">
                                                        <Package className="h-5 w-5 text-gray-400" />
                                                    </div>
                                                )}
                                                <div>
                                                    <div className="text-sm font-medium text-gray-900 max-w-xs truncate">
                                                        {product.name}
                                                    </div>
                                                    {product.attributes?.weight && (
                                                        <div className="text-xs text-gray-500">
                                                            {product.attributes.weight}
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {product.brand}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            {product.category ? (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                    {product.category}
                                                </span>
                                            ) : (
                                                <span className="text-gray-400 text-sm">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {product.ean ? (
                                                <div className="flex items-center">
                                                    <Barcode className="h-4 w-4 text-gray-400 mr-1" />
                                                    {product.ean}
                                                </div>
                                            ) : (
                                                <span className="text-gray-400">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <Star className={`h-4 w-4 mr-1 ${getConfidenceColor(product.confidence_score)}`} />
                                                <span className={`text-sm ${getConfidenceColor(product.confidence_score)}`}>
                                                    {product.confidence_score ? `${Math.round(product.confidence_score * 100)}%` : '-'}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            <div className="flex items-center">
                                                <Calendar className="h-4 w-4 mr-1" />
                                                {formatDate(product.created_at)}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <div className="flex items-center justify-end space-x-2">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        openModal(product, "view");
                                                    }}
                                                    className="text-primary-600 hover:text-primary-900"
                                                    title="Visualizar"
                                                >
                                                    <Eye className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        openModal(product, "edit");
                                                    }}
                                                    className="text-gray-600 hover:text-gray-900"
                                                    title="Editar"
                                                >
                                                    <Edit3 className="h-4 w-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Paginação */}
                {totalPages > 1 && (
                    <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                        <div className="flex-1 flex justify-between sm:hidden">
                            <button
                                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                disabled={currentPage === 1}
                                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Anterior
                            </button>
                            <button
                                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                disabled={currentPage === totalPages}
                                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Próximo
                            </button>
                        </div>
                        <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                            <div>
                                <p className="text-sm text-gray-700">
                                    Mostrando{" "}
                                    <span className="font-medium">{(currentPage - 1) * limit + 1}</span>
                                    {" "}até{" "}
                                    <span className="font-medium">
                                        {Math.min(currentPage * limit, total)}
                                    </span>
                                    {" "}de{" "}
                                    <span className="font-medium">{total}</span>
                                    {" "}resultados
                                </p>
                            </div>
                            <div>
                                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                                    <button
                                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                        disabled={currentPage === 1}
                                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Anterior
                                    </button>

                                    {/* Páginas */}
                                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                        const page = i + 1;
                                        return (
                                            <button
                                                key={page}
                                                onClick={() => setCurrentPage(page)}
                                                className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${currentPage === page
                                                    ? "z-10 bg-primary-50 border-primary-500 text-primary-600"
                                                    : "bg-white border-gray-300 text-gray-500 hover:bg-gray-50"
                                                    }`}
                                            >
                                                {page}
                                            </button>
                                        );
                                    })}

                                    <button
                                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                        disabled={currentPage === totalPages}
                                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Próximo
                                    </button>
                                </nav>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Modal de produto */}
            {selectedProduct && (
                <ProductModal
                    product={selectedProduct}
                    isOpen={isModalOpen}
                    onClose={closeModal}
                    mode={modalMode}
                    onSave={handleSaveProduct}
                    isLoading={updateProductMutation.isLoading}
                />
            )}
        </div>
    );
}