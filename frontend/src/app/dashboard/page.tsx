"use client";

import { useQuery } from "react-query";
import { Package, FileText, TrendingUp, Clock } from "lucide-react";
import api from "@/lib/api";

export default function DashboardPage() {
    const { data: stats } = useQuery("stats", async () => {
        const [products, catalogs] = await Promise.all([
            api.get("/api/products/search?limit=1"),
            api.get("/api/catalog/list"),
        ]);
        return {
            totalProducts: products.data.total || 0,
            totalCatalogs: catalogs.data.length || 0,
        };
    });

    const cards = [
        {
            name: "Total de Produtos",
            value: stats?.totalProducts || 0,
            icon: Package,
            color: "bg-blue-500",
        },
        {
            name: "Catálogos Processados",
            value: stats?.totalCatalogs || 0,
            icon: FileText,
            color: "bg-green-500",
        },
        {
            name: "Taxa de Sucesso",
            value: "98%",
            icon: TrendingUp,
            color: "bg-purple-500",
        },
        {
            name: "Última Atualização",
            value: "Hoje",
            icon: Clock,
            color: "bg-orange-500",
        },
    ];

    return (
        <div>
            <h1 className="text-2xl font-bold text-foreground mb-6">Dashboard</h1>

            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                {cards.map((card) => (
                    <div
                        key={card.name}
                        className="bg-card overflow-hidden shadow rounded-lg"
                    >
                        <div className="p-5">
                            <div className="flex items-center">
                                <div className={`flex-shrink-0 ${card.color} rounded-md p-3`}>
                                    <card.icon className="h-6 w-6 text-white" />
                                </div>
                                <div className="ml-5 w-0 flex-1">
                                    <dl>
                                        <dt className="text-sm font-medium text-foreground/60 truncate">
                                            {card.name}
                                        </dt>
                                        <dd className="text-2xl font-semibold text-foreground">
                                            {card.value}
                                        </dd>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-8 bg-card shadow rounded-lg p-6">
                <h2 className="text-lg font-semibold text-foreground mb-4">
                    Bem-vindo ao SixPet Catalog Manager
                </h2>
                <p className="text-foreground/70">
                    Sistema de gerenciamento de catálogos de produtos pet com processamento
                    automático via IA.
                </p>
            </div>
        </div>
    );
}
