"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Package,
    Upload,
    Settings,
    Key
} from "lucide-react";

const navigation = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Produtos", href: "/dashboard/products", icon: Package },
    { name: "Upload", href: "/dashboard/upload", icon: Upload },
    { name: "API Keys", href: "/dashboard/api-keys", icon: Key },
    { name: "Configurações", href: "/dashboard/settings", icon: Settings },
];

export default function Sidebar() {
    const pathname = usePathname();

    return (
        <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
            <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-card border-r border-border px-6 pb-4">
                <div className="flex h-16 shrink-0 items-center">
                    <h1 className="text-2xl font-bold text-primary-600">SixPet</h1>
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
                          group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold transition-colors
                          ${isActive
                                                        ? "bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400"
                                                        : "text-foreground/70 hover:text-primary-600 hover:bg-background"
                                                    }
                        `}
                                            >
                                                <item.icon
                                                    className={`h-6 w-6 shrink-0 ${isActive ? "text-primary-600 dark:text-primary-400" : "text-foreground/40 group-hover:text-primary-600"
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
    );
}
