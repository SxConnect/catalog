"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
    LayoutDashboard,
    Package,
    Upload,
    Settings,
    Key,
    Globe,
    Menu,
    X
} from "lucide-react";

const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Produtos", href: "/dashboard/products", icon: Package },
    { name: "Upload PDF", href: "/dashboard/upload", icon: Upload },
    { name: "Importar Sitemap", href: "/dashboard/sitemap", icon: Globe },
    { name: "API Keys", href: "/dashboard/api-keys", icon: Key },
    { name: "Configurações", href: "/dashboard/settings", icon: Settings },
];

export default function Sidebar() {
    const pathname = usePathname();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <>
            {/* Mobile menu button */}
            <div className="lg:hidden">
                <button
                    type="button"
                    className="fixed top-4 left-4 z-50 inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500 bg-white dark:bg-gray-800 shadow-lg"
                    onClick={() => setSidebarOpen(true)}
                >
                    <span className="sr-only">Open sidebar</span>
                    <Menu className="h-6 w-6" aria-hidden="true" />
                </button>
            </div>

            {/* Mobile sidebar overlay */}
            {sidebarOpen && (
                <div className="fixed inset-0 z-40 lg:hidden">
                    <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
                    <div className="fixed inset-y-0 left-0 flex w-full max-w-xs flex-col bg-white dark:bg-gray-800 shadow-xl">
                        <div className="flex h-16 shrink-0 items-center justify-between px-6 border-b border-gray-200 dark:border-gray-700">
                            <h1 className="text-2xl font-bold text-primary-600 dark:text-primary-400">SixPet</h1>
                            <button
                                type="button"
                                className="ml-1 flex h-10 w-10 items-center justify-center rounded-md focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                                onClick={() => setSidebarOpen(false)}
                            >
                                <span className="sr-only">Close sidebar</span>
                                <X className="h-6 w-6 text-gray-400 dark:text-gray-300" aria-hidden="true" />
                            </button>
                        </div>
                        <nav className="flex flex-1 flex-col px-6 pb-4 pt-5">
                            <ul role="list" className="flex flex-1 flex-col gap-y-7">
                                <li>
                                    <ul role="list" className="-mx-2 space-y-1">
                                        {navigation.map((item) => {
                                            const isActive = pathname === item.href;
                                            return (
                                                <li key={item.name}>
                                                    <Link
                                                        href={item.href}
                                                        onClick={() => setSidebarOpen(false)}
                                                        className={`
                                                            group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold
                                                            ${isActive
                                                                ? "bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400"
                                                                : "text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700"
                                                            }
                                                        `}
                                                    >
                                                        <item.icon
                                                            className={`h-6 w-6 shrink-0 ${isActive
                                                                ? "text-primary-600 dark:text-primary-400"
                                                                : "text-gray-400 dark:text-gray-500 group-hover:text-primary-600 dark:group-hover:text-primary-400"
                                                                }`}
                                                        />
                                                        {item.name}
                                                    </Link>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>
            )}

            {/* Desktop sidebar */}
            <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 px-6 pb-4">
                    <div className="flex h-16 shrink-0 items-center">
                        <h1 className="text-2xl font-bold text-primary-600 dark:text-primary-400">SixPet</h1>
                    </div>
                    <nav className="flex flex-1 flex-col">
                        <ul role="list" className="flex flex-1 flex-col gap-y-7">
                            <li>
                                <ul role="list" className="-mx-2 space-y-1">
                                    {navigation.map((item) => {
                                        const isActive = pathname === item.href;
                                        return (
                                            <li key={item.name}>
                                                <Link
                                                    href={item.href}
                                                    className={`
                                                        group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold
                                                        ${isActive
                                                            ? "bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400"
                                                            : "text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700"
                                                        }
                                                    `}
                                                >
                                                    <item.icon
                                                        className={`h-6 w-6 shrink-0 ${isActive
                                                            ? "text-primary-600 dark:text-primary-400"
                                                            : "text-gray-400 dark:text-gray-500 group-hover:text-primary-600 dark:group-hover:text-primary-400"
                                                            }`}
                                                    />
                                                    {item.name}
                                                </Link>
                                            </li>
                                        );
                                    })}
                                </ul>
                            </li>
                        </ul>
                    </nav>
                </div>
            </div>
        </>
    );
}