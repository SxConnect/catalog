"use client";

import { useState, useEffect } from "react";
import {
    X,
    Package,
    Tag,
    Barcode,
    Calendar,
    Star,
    Edit3,
    Save,
    Eye,
    Image as ImageIcon,
    Palette,
    Weight,
    Ruler,
    DollarSign,
    FileText,
    Beaker,
    List
} from "lucide-react";

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

type ProductModalProps = {
    product: Product;
    isOpen: boolean;
    onClose: () => void;
    mode: "view" | "edit";
    onSave: (product: Product) => void;
    isLoading?: boolean;
};

export default function ProductModal({
    product,
    isOpen,
    onClose,
    mode,
    onSave,
    isLoading = false
}: ProductModalProps) {
    const [editedProduct, setEditedProduct] = useState<Product>(product);
    const [activeTab, setActiveTab] = useState<"basic" | "attributes" | "nutrition" | "ingredients">("basic");

    useEffect(() => {
        setEditedProduct(product);
    }, [product]);

    if (!isOpen) return null;

    const handleSave = () => {
        onSave(editedProduct);
    };

    const updateField = (field: keyof Product, value: any) => {
        setEditedProduct(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const updateAttribute = (key: string, value: any) => {
        setEditedProduct(prev => ({
            ...prev,
            attributes: {
                ...prev.attributes,
                [key]: value
            }
        }));
    };

    const updateNutrition = (key: string, value: number) => {
        setEditedProduct(prev => ({
            ...prev,
            nutritional_info: {
                ...prev.nutritional_info,
                [key]: value
            }
        }));
    };

    const addIngredient = (ingredient: string) => {
        if (ingredient.trim()) {
            setEditedProduct(prev => ({
                ...prev,
                ingredients: [...(prev.ingredients || []), ingredient.trim()]
            }));
        }
    };

    const removeIngredient = (index: number) => {
        setEditedProduct(prev => ({
            ...prev,
            ingredients: prev.ingredients?.filter((_, i) => i !== index) || []
        }));
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

    const tabs = [
        { id: "basic", label: "Informações Básicas", icon: Package },
        { id: "attributes", label: "Atributos", icon: Tag },
        { id: "nutrition", label: "Nutrição", icon: Beaker },
        { id: "ingredients", label: "Ingredientes", icon: List }
    ];

    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                {/* Overlay */}
                <div
                    className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
                    onClick={onClose}
                />

                {/* Modal */}
                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
                    {/* Header */}
                    <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <div className="flex-shrink-0">
                                    {editedProduct.images && editedProduct.images.length > 0 ? (
                                        <img
                                            className="h-12 w-12 rounded-lg object-cover"
                                            src={editedProduct.images[0]}
                                            alt={editedProduct.name}
                                            onError={(e) => {
                                                e.currentTarget.style.display = 'none';
                                            }}
                                        />
                                    ) : (
                                        <div className="h-12 w-12 rounded-lg bg-gray-200 flex items-center justify-center">
                                            <Package className="h-6 w-6 text-gray-400" />
                                        </div>
                                    )}
                                </div>
                                <div>
                                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                                        {mode === "edit" ? "Editar Produto" : "Visualizar Produto"}
                                    </h3>
                                    <p className="text-sm text-gray-500">
                                        ID: {editedProduct.id} • {editedProduct.brand}
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center space-x-2">
                                {mode === "view" && (
                                    <button
                                        onClick={() => window.location.href = `#edit-${editedProduct.id}`}
                                        className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                                    >
                                        <Edit3 className="h-4 w-4 mr-1" />
                                        Editar
                                    </button>
                                )}
                                <button
                                    onClick={onClose}
                                    className="bg-white rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                                >
                                    <X className="h-6 w-6" />
                                </button>
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="mt-6">
                            <div className="border-b border-gray-200">
                                <nav className="-mb-px flex space-x-8">
                                    {tabs.map((tab) => (
                                        <button
                                            key={tab.id}
                                            onClick={() => setActiveTab(tab.id as any)}
                                            className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${activeTab === tab.id
                                                ? "border-primary-500 text-primary-600"
                                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                                }`}
                                        >
                                            <tab.icon className="h-4 w-4 mr-2" />
                                            {tab.label}
                                        </button>
                                    ))}
                                </nav>
                            </div>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="px-4 pb-4 sm:px-6 sm:pb-6 max-h-96 overflow-y-auto">
                        {/* Tab: Informações Básicas */}
                        {activeTab === "basic" && (
                            <div className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {/* Nome */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Nome do Produto
                                        </label>
                                        {mode === "edit" ? (
                                            <input
                                                type="text"
                                                value={editedProduct.name}
                                                onChange={(e) => updateField("name", e.target.value)}
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                            />
                                        ) : (
                                            <p className="text-sm text-gray-900">{editedProduct.name}</p>
                                        )}
                                    </div>

                                    {/* Marca */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Marca
                                        </label>
                                        {mode === "edit" ? (
                                            <input
                                                type="text"
                                                value={editedProduct.brand}
                                                onChange={(e) => updateField("brand", e.target.value)}
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                            />
                                        ) : (
                                            <p className="text-sm text-gray-900">{editedProduct.brand}</p>
                                        )}
                                    </div>

                                    {/* EAN */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            <Barcode className="inline h-4 w-4 mr-1" />
                                            Código EAN
                                        </label>
                                        {mode === "edit" ? (
                                            <input
                                                type="text"
                                                value={editedProduct.ean || ""}
                                                onChange={(e) => updateField("ean", e.target.value)}
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                            />
                                        ) : (
                                            <p className="text-sm text-gray-900">{editedProduct.ean || "-"}</p>
                                        )}
                                    </div>

                                    {/* Categoria */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            Categoria
                                        </label>
                                        {mode === "edit" ? (
                                            <input
                                                type="text"
                                                value={editedProduct.category || ""}
                                                onChange={(e) => updateField("category", e.target.value)}
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                            />
                                        ) : (
                                            <p className="text-sm text-gray-900">{editedProduct.category || "-"}</p>
                                        )}
                                    </div>
                                </div>

                                {/* Descrição */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Descrição
                                    </label>
                                    {mode === "edit" ? (
                                        <textarea
                                            value={editedProduct.description || ""}
                                            onChange={(e) => updateField("description", e.target.value)}
                                            rows={3}
                                            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                        />
                                    ) : (
                                        <p className="text-sm text-gray-900">{editedProduct.description || "-"}</p>
                                    )}
                                </div>

                                {/* Informações do sistema */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            <Star className="inline h-4 w-4 mr-1" />
                                            Confiança
                                        </label>
                                        <p className={`text-sm ${getConfidenceColor(editedProduct.confidence_score)}`}>
                                            {editedProduct.confidence_score ? `${Math.round(editedProduct.confidence_score * 100)}%` : '-'}
                                        </p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            <FileText className="inline h-4 w-4 mr-1" />
                                            Catálogo
                                        </label>
                                        <p className="text-sm text-gray-900">{editedProduct.source_catalog || "-"}</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            <Calendar className="inline h-4 w-4 mr-1" />
                                            Criado em
                                        </label>
                                        <p className="text-sm text-gray-900">{formatDate(editedProduct.created_at)}</p>
                                    </div>
                                </div>

                                {/* Imagens */}
                                {editedProduct.images && editedProduct.images.length > 0 && (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            <ImageIcon className="inline h-4 w-4 mr-1" />
                                            Imagens ({editedProduct.images.length})
                                        </label>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                            {editedProduct.images.map((image, index) => (
                                                <img
                                                    key={index}
                                                    src={image}
                                                    alt={`${editedProduct.name} - ${index + 1}`}
                                                    className="w-full h-20 object-cover rounded-md border border-gray-200"
                                                    onError={(e) => {
                                                        e.currentTarget.style.display = 'none';
                                                    }}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Tab: Atributos */}
                        {activeTab === "attributes" && (
                            <div className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {/* Preço */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            <DollarSign className="inline h-4 w-4 mr-1" />
                                            Preço (R$)
                                        </label>
                                        {mode === "edit" ? (
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={editedProduct.attributes?.price_avg || ""}
                                                onChange={(e) => updateAttribute("price_avg", parseFloat(e.target.value) || 0)}
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                            />
                                        ) : (
                                            <p className="text-sm text-gray-900">
                                                {editedProduct.attributes?.price_avg ? `R$ ${editedProduct.attributes.price_avg.toFixed(2)}` : "-"}
                                            </p>
                                        )}
                                    </div>

                                    {/* Peso */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            <Weight className="inline h-4 w-4 mr-1" />
                                            Peso
                                        </label>
                                        {mode === "edit" ? (
                                            <input
                                                type="text"
                                                value={editedProduct.attributes?.weight || ""}
                                                onChange={(e) => updateAttribute("weight", e.target.value)}
                                                placeholder="Ex: 1kg, 500g"
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                            />
                                        ) : (
                                            <p className="text-sm text-gray-900">{editedProduct.attributes?.weight || "-"}</p>
                                        )}
                                    </div>

                                    {/* Cor */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            <Palette className="inline h-4 w-4 mr-1" />
                                            Cor
                                        </label>
                                        {mode === "edit" ? (
                                            <input
                                                type="text"
                                                value={editedProduct.attributes?.color || ""}
                                                onChange={(e) => updateAttribute("color", e.target.value)}
                                                placeholder="Ex: Marrom, Multicolor"
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                            />
                                        ) : (
                                            <p className="text-sm text-gray-900">{editedProduct.attributes?.color || "-"}</p>
                                        )}
                                    </div>

                                    {/* Dimensões */}
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            <Ruler className="inline h-4 w-4 mr-1" />
                                            Dimensões
                                        </label>
                                        {mode === "edit" ? (
                                            <input
                                                type="text"
                                                value={editedProduct.attributes?.dimensions || ""}
                                                onChange={(e) => updateAttribute("dimensions", e.target.value)}
                                                placeholder="Ex: 30x20x10cm"
                                                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                            />
                                        ) : (
                                            <p className="text-sm text-gray-900">{editedProduct.attributes?.dimensions || "-"}</p>
                                        )}
                                    </div>
                                </div>

                                {/* Outros atributos */}
                                {editedProduct.attributes && Object.keys(editedProduct.attributes).length > 0 && (
                                    <div className="pt-4 border-t border-gray-200">
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Outros Atributos
                                        </label>
                                        <div className="space-y-2">
                                            {Object.entries(editedProduct.attributes).map(([key, value]) => {
                                                if (["price_avg", "weight", "color", "dimensions"].includes(key)) return null;
                                                return (
                                                    <div key={key} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-md">
                                                        <span className="text-sm font-medium text-gray-700 capitalize">
                                                            {key.replace(/_/g, " ")}:
                                                        </span>
                                                        <span className="text-sm text-gray-900">
                                                            {typeof value === "object" ? JSON.stringify(value) : String(value)}
                                                        </span>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Tab: Nutrição */}
                        {activeTab === "nutrition" && (
                            <div className="space-y-4">
                                {editedProduct.nutritional_info && Object.keys(editedProduct.nutritional_info).length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {Object.entries(editedProduct.nutritional_info).map(([key, value]) => (
                                            <div key={key}>
                                                <label className="block text-sm font-medium text-gray-700 mb-1 capitalize">
                                                    {key === "protein" ? "Proteína" :
                                                        key === "fat" ? "Gordura" :
                                                            key === "fiber" ? "Fibra" :
                                                                key === "moisture" ? "Umidade" :
                                                                    key === "ash" ? "Cinzas" :
                                                                        key === "energy" ? "Energia (kcal)" :
                                                                            key.replace(/_/g, " ")}
                                                    {key !== "energy" && " (%)"}
                                                </label>
                                                {mode === "edit" ? (
                                                    <input
                                                        type="number"
                                                        step="0.1"
                                                        value={value || ""}
                                                        onChange={(e) => updateNutrition(key, parseFloat(e.target.value) || 0)}
                                                        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                                    />
                                                ) : (
                                                    <p className="text-sm text-gray-900">
                                                        {value}{key === "energy" ? " kcal" : "%"}
                                                    </p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-8">
                                        <Beaker className="mx-auto h-12 w-12 text-gray-400" />
                                        <h3 className="mt-2 text-sm font-medium text-gray-900">
                                            Nenhuma informação nutricional
                                        </h3>
                                        <p className="mt-1 text-sm text-gray-500">
                                            Informações nutricionais não foram extraídas para este produto.
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Tab: Ingredientes */}
                        {activeTab === "ingredients" && (
                            <div className="space-y-4">
                                {editedProduct.ingredients && editedProduct.ingredients.length > 0 ? (
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-2">
                                            Lista de Ingredientes ({editedProduct.ingredients.length})
                                        </label>
                                        <div className="space-y-2">
                                            {editedProduct.ingredients.map((ingredient, index) => (
                                                <div key={index} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-md">
                                                    <span className="text-sm text-gray-900 capitalize">
                                                        {ingredient}
                                                    </span>
                                                    {mode === "edit" && (
                                                        <button
                                                            onClick={() => removeIngredient(index)}
                                                            className="text-red-600 hover:text-red-800"
                                                        >
                                                            <X className="h-4 w-4" />
                                                        </button>
                                                    )}
                                                </div>
                                            ))}
                                        </div>

                                        {mode === "edit" && (
                                            <div className="mt-4">
                                                <input
                                                    type="text"
                                                    placeholder="Adicionar ingrediente..."
                                                    onKeyPress={(e) => {
                                                        if (e.key === "Enter") {
                                                            addIngredient(e.currentTarget.value);
                                                            e.currentTarget.value = "";
                                                        }
                                                    }}
                                                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                                                />
                                                <p className="mt-1 text-xs text-gray-500">
                                                    Pressione Enter para adicionar
                                                </p>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="text-center py-8">
                                        <List className="mx-auto h-12 w-12 text-gray-400" />
                                        <h3 className="mt-2 text-sm font-medium text-gray-900">
                                            Nenhum ingrediente
                                        </h3>
                                        <p className="mt-1 text-sm text-gray-500">
                                            Ingredientes não foram extraídos para este produto.
                                        </p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    {mode === "edit" && (
                        <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                            <button
                                onClick={handleSave}
                                disabled={isLoading}
                                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                        Salvando...
                                    </>
                                ) : (
                                    <>
                                        <Save className="h-4 w-4 mr-2" />
                                        Salvar
                                    </>
                                )}
                            </button>
                            <button
                                onClick={onClose}
                                disabled={isLoading}
                                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                            >
                                Cancelar
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}