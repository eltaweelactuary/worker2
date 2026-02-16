"use client"
import './globals.css'
import { useState } from 'react'
import { LayoutDashboard, ShieldAlert, BarChart3, Bot, Settings, FileText } from 'lucide-react'

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
                {children}
            </body>
        </html>
    )
}
