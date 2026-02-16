"use client"
import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, Users, AlertTriangle, Coins, RefreshCcw } from 'lucide-react';

export default function Dashboard() {
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [metrics, setMetrics] = useState({
        reserve: "0",
        solvencyRatio: "0",
        riskCount: 0
    });

    const fetchData = async () => {
        setLoading(true);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
            const res = await fetch(`${apiUrl}/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wage_inflation: 0.07,
                    medical_inflation: 0.12,
                    investment_return_rate: 0.10,
                    admin_expense_pct: 0.04,
                    projection_years: 10,
                    population_size: 1000
                })
            });
            const result = await res.json();

            const projections = result.projections.map((p: any) => ({
                name: `Year ${p.Year}`,
                revenue: p.Total_Revenue,
                expenditure: p.Total_Expenditure,
                reserve: p.Reserve_Fund
            }));

            setData(projections);

            const last = result.projections[result.projections.length - 1];
            setMetrics({
                reserve: (last.Reserve_Fund / 1e9).toFixed(1) + "B",
                solvencyRatio: (last.Total_Revenue / last.Total_Expenditure).toFixed(2),
                riskCount: last.Risk_Flags.length
            });
        } catch (err) {
            console.error("Fetch error:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard title="Total Reserve" value={metrics.reserve} sub="EGP" trend="+12%" icon={<Coins className="text-actuary-primary" />} />
                <StatCard title="Solvency Ratio" value={metrics.solvencyRatio} sub="x" trend={parseFloat(metrics.solvencyRatio) > 1 ? "Healthy" : "Deficit"} icon={<TrendingUp className="text-actuary-secondary" />} />
                <StatCard title="Active Members" value="4.1M" sub="People" trend="+0.4%" icon={<Users className="text-blue-400" />} />
                <StatCard title="Risk Alert" value={metrics.riskCount} sub="Flags" trend={metrics.riskCount > 0 ? "Action Needed" : "Stable"} icon={<AlertTriangle className="text-actuary-risk" />} danger={metrics.riskCount > 0} />
            </div>

            {loading && (
                <div className="flex justify-center p-12">
                    <RefreshCcw className="animate-spin text-actuary-primary" size={32} />
                </div>
            )}

            {/* Main Charts Area */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card p-6 h-96">
                    <h3 className="text-lg font-medium mb-6">Revenue vs Expenditure (10Y Projection)</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data}>
                            <defs>
                                <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                            <YAxis stroke="#94a3b8" fontSize={12} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Area type="monotone" dataKey="revenue" stroke="#10b981" fillOpacity={1} fill="url(#colorRev)" strokeWidth={3} />
                            <Area type="monotone" dataKey="expenditure" stroke="#f43f5e" fillOpacity={0} strokeWidth={2} strokeDasharray="5 5" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                <div className="glass-card p-6 h-96">
                    <h3 className="text-lg font-medium mb-6">Reserve Accumulation Trend</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                            <YAxis stroke="#94a3b8" fontSize={12} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                            />
                            <Bar dataKey="reserve" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={40} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    )
}

function StatCard({ title, value, sub, trend, icon, danger = false }: any) {
    return (
        <div className="glass-card p-6 flex items-start justify-between">
            <div>
                <p className="text-sm text-slate-400 mb-1">{title}</p>
                <div className="flex items-baseline gap-1">
                    <span className="text-2xl font-bold">{value}</span>
                    <span className="text-xs text-slate-500 font-medium">{sub}</span>
                </div>
                <p className={`text-xs mt-2 font-medium ${danger ? 'text-actuary-risk' : 'text-actuary-primary'}`}>
                    {trend}
                </p>
            </div>
            <div className="p-3 bg-white/5 rounded-xl">
                {icon}
            </div>
        </div>
    )
}
