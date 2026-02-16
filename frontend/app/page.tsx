"use client"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, Users, AlertTriangle, Coins } from 'lucide-react';

const data = [
    { name: 'Year 1', revenue: 4000, expenditure: 2400 },
    { name: 'Year 2', revenue: 3000, expenditure: 1398 },
    { name: 'Year 3', revenue: 2000, expenditure: 9800 },
    { name: 'Year 4', revenue: 2780, expenditure: 3908 },
    { name: 'Year 5', revenue: 1890, expenditure: 4800 },
];

export default function Dashboard() {
    return (
        <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard title="Total Reserve" value="5.2B" sub="EGP" trend="+12%" icon={<Coins className="text-actuary-primary" />} />
                <StatCard title="Solvency Ratio" value="1.84" sub="x" trend="Healthy" icon={<TrendingUp className="text-actuary-secondary" />} />
                <StatCard title="Active Members" value="4.1M" sub="People" trend="+0.4%" icon={<Users className="text-blue-400" />} />
                <StatCard title="Risk Alert" value="2" sub="Critical" trend="Action Needed" icon={<AlertTriangle className="text-actuary-risk" />} danger />
            </div>

            {/* Main Charts Area */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card p-6 h-96">
                    <h3 className="text-lg font-medium mb-6">Revenue vs Expenditure (5Y Projection)</h3>
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
                    <h3 className="text-lg font-medium mb-6">Population Risk Maturity</h3>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} />
                            <YAxis stroke="#94a3b8" fontSize={12} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                            />
                            <Bar dataKey="revenue" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={40} />
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
