"use client";

import { signOut, useSession } from "next-auth/react";
import { LogOut, User, Moon, Sun } from "lucide-react";
import { useTheme } from "./ThemeProvider";

export default function Header() {
    const { data: session } = useSession();
    const { theme, toggleTheme } = useTheme();

    return (
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
            <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
                <div className="flex flex-1"></div>
                <div className="flex items-center gap-x-4 lg:gap-x-6">
                    <button
                        onClick={toggleTheme}
                        className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        title={theme === "dark" ? "Modo Claro" : "Modo Escuro"}
                    >
                        {theme === "dark" ? (
                            <Sun className="h-5 w-5 text-yellow-500" />
                        ) : (
                            <Moon className="h-5 w-5 text-gray-600" />
                        )}
                    </button>
                    <div className="flex items-center gap-x-3">
                        <div className="flex items-center gap-x-2">
                            <User className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                {session?.user?.name || session?.user?.email}
                            </span>
                        </div>
                        <button
                            onClick={() => signOut({ callbackUrl: "/login" })}
                            className="flex items-center gap-x-2 rounded-md px-3 py-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                            <LogOut className="h-5 w-5" />
                            Sair
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
