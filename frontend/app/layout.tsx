import './globals.css'
import { Inter } from 'next/font/google'
import { LayoutDashboard, ShieldAlert, BarChart3, Bot, Settings } from 'lucide-react'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
    title: 'UHI Actuarial Portal | Egypt',
    description: 'Enterprise Actuarial Oversight System (Law 2/2018)',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <div className="flex h-screen overflow-hidden">
                    {/* Sidebar */}
                    <aside className="w-64 glass-card m-4 mr-0 flex flex-col p-6">
                        <div className="mb-10">
                            <h1 className="text-xl font-bold gradient-text underline decoration-actuary-primary">UHI PORTAL</h1>
                            <p className="text-xs text-slate-400 mt-1">Actuarial Dashboard v4.0</p>
                        </div>

                        <nav className="flex-1 space-y-4">
                            <NavItem icon={<LayoutDashboard size={20} />} label="Executive Overview" active />
                            <NavItem icon={<BarChart3 size={20} />} label="Solvency Analytics" />
                            <NavItem icon={<ShieldAlert size={20} />} label="Risk Monitoring" />
                            <NavItem icon={<Bot size={20} />} label="Gemini Actuary" />
                        </nav>

                        <div className="mt-auto pt-6 border-t border-white/10">
                            <NavItem icon={<Settings size={20} />} label="System Config" />
                        </div>
                    </aside>

                    {/* Main Content */}
                    <main className="flex-1 overflow-y-auto p-8">
                        <header className="flex justify-between items-center mb-8">
                            <div>
                                <h2 className="text-3xl font-semibold tracking-tight">Financial Health</h2>
                                <p className="text-slate-400">Projected Reserves & Solvency Metrics</p>
                            </div>
                            <div className="flex gap-4">
                                <div className="glass-card px-4 py-2 text-sm flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-actuary-primary animate-pulse"></div>
                                    API Sync: Online
                                </div>
                            </div>
                        </header>

                        {children}
                    </main>
                </div>
            </body>
        </html>
    )
}

function NavItem({ icon, label, active = false }: { icon: any, label: string, active?: boolean }) {
    return (
        <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer hover:bg-white/5 ${active ? 'bg-white/10 text-actuary-primary border-r-4 border-actuary-primary' : 'text-slate-400'}`}>
            {icon}
            <span className="font-medium">{label}</span>
        </div>
    )
}
