"use client";

import { SessionProvider } from "next-auth/react";
import { QueryClient, QueryClientProvider } from "react-query";
import { useState } from "react";
import { ThemeProvider } from "./ThemeProvider";

export function Providers({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient());

    return (
        <SessionProvider>
            <QueryClientProvider client={queryClient}>
                <ThemeProvider>
                    {children}
                </ThemeProvider>
            </QueryClientProvider>
        </SessionProvider>
    );
}
