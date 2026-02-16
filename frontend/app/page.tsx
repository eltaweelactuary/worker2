"use client"
import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, LineChart, Line } from 'recharts';
import { TrendingUp, Users, AlertTriangle, Coins, RefreshCcw, LayoutDashboard, ShieldAlert, BarChart3, Bot, Settings, FileText, Send, Loader2, Download } from 'lucide-react';
import ChatBox from '../components/ChatBox';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://egypt-actuarial-api-v4-112458895076.europe-west1.run.app';

type TabId = 'overview' | 'solvency' | 'risk' | 'actuary' | 'reports';

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState<TabId>('overview');
    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [apiOnline, setApiOnline] = useState(false);
    const [metrics, setMetrics] = useState({
        reserve: "0", solvencyRatio: "0", riskCount: 0
    });

    // Monte Carlo state
    const [mcData, setMcData] = useState<any>(null);
    const [mcLoading, setMcLoading] = useState(false);

    // ML Risk state
    const [mlData, setMlData] = useState<any>(null);
    const [mlLoading, setMlLoading] = useState(false);

    // Report state
    const [report, setReport] = useState<any>(null);
    const [reportLoading, setReportLoading] = useState(false);

    // --- Data Fetching ---
    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_URL}/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    wage_inflation: 0.07, medical_inflation: 0.12,
                    investment_return_rate: 0.10, admin_expense_pct: 0.04,
                    projection_years: 10, population_size: 1000
                })
            });
            const result = await res.json();
            const projections = result.projections.map((p: any) => ({
                name: `Year ${p.Year}`, revenue: p.Total_Revenue,
                expenditure: p.Total_Expenditure, reserve: p.Reserve_Fund
            }));
            setData(projections);
            const last = result.projections[result.projections.length - 1];
            setMetrics({
                reserve: (last.Reserve_Fund / 1e9).toFixed(1) + "B",
                solvencyRatio: (last.Total_Revenue / last.Total_Expenditure).toFixed(2),
                riskCount: last.Risk_Flags.length
            });
            setApiOnline(true);
        } catch (err: any) {
            setError(`API Error: ${err.message}`);
            setApiOnline(false);
        } finally {
            setLoading(false);
        }
    };

    const fetchMonteCarlo = async () => {
        setMcLoading(true);
        try {
            const res = await fetch(`${API_URL}/monte-carlo`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ projection_years: 10, population_size: 500 })
            });
            setMcData(await res.json());
        } catch (err) { setError("Monte Carlo fetch failed"); }
        finally { setMcLoading(false); }
    };

    const fetchMLAnalysis = async () => {
        setMlLoading(true);
        try {
            const res = await fetch(`${API_URL}/ml/analysis?population_size=1000`, { method: 'POST' });
            setMlData(await res.json());
        } catch (err) { setError("ML Analysis fetch failed"); }
        finally { setMlLoading(false); }
    };

    const fetchReport = async () => {
        setReportLoading(true);
        try {
            const res = await fetch(`${API_URL}/report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ projection_years: 10, population_size: 1000 })
            });
            setReport(await res.json());
        } catch (err) { setError("Report generation failed"); }
        finally { setReportLoading(false); }
    };

    useEffect(() => { fetchData(); }, []);
    useEffect(() => {
        if (activeTab === 'solvency' && !mcData) fetchMonteCarlo();
        if (activeTab === 'risk' && !mlData) fetchMLAnalysis();
        if (activeTab === 'reports' && !report) fetchReport();
    }, [activeTab]);

    const tabs: { id: TabId; label: string; icon: any }[] = [
        { id: 'overview', label: 'Executive Overview', icon: <LayoutDashboard size={20} /> },
        { id: 'solvency', label: 'Solvency Analytics', icon: <BarChart3 size={20} /> },
        { id: 'risk', label: 'Risk Monitoring', icon: <ShieldAlert size={20} /> },
        { id: 'actuary', label: 'Gemini Actuary', icon: <Bot size={20} /> },
        { id: 'reports', label: 'Reports', icon: <FileText size={20} /> },
    ];

    return (
        <div className="flex h-screen overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 glass-card m-4 mr-0 flex flex-col p-6">
                <div className="mb-10">
                    <h1 className="text-xl font-bold gradient-text">UHI PORTAL</h1>
                    <p className="text-xs text-slate-400 mt-1">Actuarial Dashboard v4.0</p>
                </div>
                <nav className="flex-1 space-y-2">
                    {tabs.map(tab => (
                        <div key={tab.id} onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all cursor-pointer hover:bg-white/5 ${activeTab === tab.id ? 'bg-white/10 text-actuary-primary border-r-4 border-actuary-primary' : 'text-slate-400'}`}>
                            {tab.icon}
                            <span className="font-medium text-sm">{tab.label}</span>
                        </div>
                    ))}
                </nav>
                <div className="mt-auto pt-6 border-t border-white/10">
                    <div className="flex items-center gap-3 px-4 py-3 rounded-xl text-slate-400 cursor-pointer hover:bg-white/5">
                        <Settings size={20} /><span className="font-medium text-sm">System Config</span>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-8">
                <header className="flex justify-between items-center mb-8">
                    <div>
                        <h2 className="text-3xl font-semibold tracking-tight">
                            {tabs.find(t => t.id === activeTab)?.label}
                        </h2>
                        <p className="text-slate-400">Projected Reserves & Solvency Metrics</p>
                    </div>
                    <div className="flex gap-4">
                        <div className="glass-card px-4 py-2 text-sm flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${apiOnline ? 'bg-actuary-primary' : 'bg-actuary-risk'} animate-pulse`}></div>
                            API: {apiOnline ? 'Online' : 'Offline'}
                        </div>
                    </div>
                </header>

                {error && (
                    <div className="glass-card p-4 mb-6 border-actuary-risk/30 bg-actuary-risk/10 text-actuary-risk text-sm">
                        ⚠️ {error}
                        <button onClick={fetchData} className="ml-4 underline">Retry</button>
                    </div>
                )}

                {/* === TAB: Executive Overview === */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            <StatCard title="Total Reserve" value={metrics.reserve} sub="EGP" trend="+12%" icon={<Coins className="text-actuary-primary" />} />
                            <StatCard title="Solvency Ratio" value={metrics.solvencyRatio} sub="x" trend={parseFloat(metrics.solvencyRatio) > 1 ? "Healthy" : "Deficit"} icon={<TrendingUp className="text-actuary-secondary" />} />
                            <StatCard title="Active Members" value="4.1M" sub="People" trend="+0.4%" icon={<Users className="text-blue-400" />} />
                            <StatCard title="Risk Alert" value={metrics.riskCount} sub="Flags" trend={metrics.riskCount > 0 ? "Action Needed" : "Stable"} icon={<AlertTriangle className="text-actuary-risk" />} danger={metrics.riskCount > 0} />
                        </div>
                        {loading && <div className="flex justify-center p-12"><RefreshCcw className="animate-spin text-actuary-primary" size={32} /></div>}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <div className="glass-card p-6 h-96">
                                <h3 className="text-lg font-medium mb-6">Revenue vs Expenditure (10Y)</h3>
                                <ResponsiveContainer width="100%" height="85%">
                                    <AreaChart data={data}>
                                        <defs><linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.3} /><stop offset="95%" stopColor="#10b981" stopOpacity={0} /></linearGradient></defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                        <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} /><YAxis stroke="#94a3b8" fontSize={12} />
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} itemStyle={{ color: '#fff' }} />
                                        <Area type="monotone" dataKey="revenue" stroke="#10b981" fillOpacity={1} fill="url(#colorRev)" strokeWidth={3} />
                                        <Area type="monotone" dataKey="expenditure" stroke="#f43f5e" fillOpacity={0} strokeWidth={2} strokeDasharray="5 5" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="glass-card p-6 h-96">
                                <h3 className="text-lg font-medium mb-6">Reserve Accumulation Trend</h3>
                                <ResponsiveContainer width="100%" height="85%">
                                    <BarChart data={data}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                        <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} /><YAxis stroke="#94a3b8" fontSize={12} />
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                                        <Bar dataKey="reserve" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={40} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    </div>
                )}

                {/* === TAB: Solvency Analytics (Monte Carlo) === */}
                {activeTab === 'solvency' && (
                    <div className="space-y-6">
                        {mcLoading && <div className="flex justify-center p-12"><RefreshCcw className="animate-spin text-actuary-primary" size={32} /></div>}
                        {mcData && (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <StatCard title="Mean Reserve" value={mcData.statistics?.mean_reserve ? (mcData.statistics.mean_reserve / 1e9).toFixed(2) + "B" : "N/A"} sub="EGP" trend="Monte Carlo" icon={<BarChart3 className="text-actuary-secondary" />} />
                                    <StatCard title="Std Deviation" value={mcData.statistics?.std_reserve ? (mcData.statistics.std_reserve / 1e9).toFixed(2) + "B" : "N/A"} sub="EGP" trend="Volatility" icon={<TrendingUp className="text-actuary-risk" />} />
                                    <StatCard title="Simulations" value={mcData.statistics?.n_simulations || 100} sub="runs" trend="Stochastic" icon={<RefreshCcw className="text-actuary-primary" />} />
                                </div>
                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-medium mb-4">Monte Carlo Simulation Results</h3>
                                    <p className="text-sm text-slate-400 mb-4">1,000 stochastic scenarios projecting solvency under randomized assumptions.</p>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-white/5 rounded-xl p-4">
                                            <p className="text-xs text-slate-400 mb-1">5th Percentile (Worst Case)</p>
                                            <p className="text-xl font-bold text-actuary-risk">{mcData.statistics?.p5_reserve ? (mcData.statistics.p5_reserve / 1e9).toFixed(2) + "B EGP" : "N/A"}</p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4">
                                            <p className="text-xs text-slate-400 mb-1">95th Percentile (Best Case)</p>
                                            <p className="text-xl font-bold text-actuary-primary">{mcData.statistics?.p95_reserve ? (mcData.statistics.p95_reserve / 1e9).toFixed(2) + "B EGP" : "N/A"}</p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4">
                                            <p className="text-xs text-slate-400 mb-1">Probability of Deficit</p>
                                            <p className="text-xl font-bold text-yellow-400">{mcData.statistics?.prob_deficit != null ? (mcData.statistics.prob_deficit * 100).toFixed(1) + "%" : "N/A"}</p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4">
                                            <p className="text-xs text-slate-400 mb-1">Median Reserve</p>
                                            <p className="text-xl font-bold text-actuary-secondary">{mcData.statistics?.median_reserve ? (mcData.statistics.median_reserve / 1e9).toFixed(2) + "B EGP" : "N/A"}</p>
                                        </div>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* === TAB: Risk Monitoring (ML) === */}
                {activeTab === 'risk' && (
                    <div className="space-y-6">
                        {mlLoading && <div className="flex justify-center p-12"><RefreshCcw className="animate-spin text-actuary-primary" size={32} /></div>}
                        {mlData && (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <StatCard title="ML Status" value={mlData.ml_status} sub="" trend="Active" icon={<ShieldAlert className="text-actuary-primary" />} />
                                    <StatCard title="High Risk Count" value={mlData.insights?.high_risk_count || 0} sub="members" trend="Top 10%" icon={<AlertTriangle className="text-actuary-risk" />} danger />
                                    <StatCard title="High Risk Threshold" value={mlData.insights?.high_risk_threshold ? Math.round(mlData.insights.high_risk_threshold).toLocaleString() : "N/A"} sub="EGP" trend="Annual Cost" icon={<Coins className="text-yellow-400" />} />
                                </div>
                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-medium mb-4">Risk Segmentation Analysis</h3>
                                    <p className="text-sm text-slate-400 mb-4">K-Means clustering of population into risk segments with Random Forest cost prediction.</p>
                                    <div className="space-y-4">
                                        {mlData.insights?.avg_cost_by_segment && Object.entries(mlData.insights.avg_cost_by_segment).map(([seg, cost]: any) => (
                                            <div key={seg} className="flex items-center justify-between bg-white/5 rounded-xl p-4">
                                                <div>
                                                    <p className="text-sm font-medium">Segment {seg}</p>
                                                    <p className="text-xs text-slate-400">Severity: {mlData.insights.segment_severity?.[seg]?.toFixed(2) || "N/A"}x</p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="text-lg font-bold">{Math.round(cost).toLocaleString()} EGP</p>
                                                    <p className="text-xs text-slate-400">Avg Annual Cost</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                {mlData.insights?.risk_distribution && (
                                    <div className="glass-card p-6">
                                        <h3 className="text-lg font-medium mb-4">Population Distribution</h3>
                                        <div className="grid grid-cols-3 gap-4">
                                            {Object.entries(mlData.insights.risk_distribution).map(([seg, count]: any) => (
                                                <div key={seg} className="bg-white/5 rounded-xl p-4 text-center">
                                                    <p className="text-2xl font-bold text-actuary-secondary">{count}</p>
                                                    <p className="text-xs text-slate-400 mt-1">Segment {seg}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                )}

                {/* === TAB: Gemini Actuary === */}
                {activeTab === 'actuary' && (
                    <div className="max-w-4xl mx-auto">
                        <ChatBox />
                    </div>
                )}

                {/* === TAB: Reports (Law 2/2018) === */}
                {activeTab === 'reports' && (
                    <div className="space-y-6">
                        {reportLoading && <div className="flex justify-center p-12"><RefreshCcw className="animate-spin text-actuary-primary" size={32} /></div>}
                        {report && (
                            <>
                                {/* Report Header */}
                                <div className="glass-card p-8">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="text-xl font-bold gradient-text">{report.report_title}</h3>
                                            <p className="text-sm text-slate-400 mt-1">{report.legal_reference}</p>
                                            <p className="text-xs text-slate-500 mt-1">Version: {report.report_version}</p>
                                        </div>
                                        <button onClick={() => {
                                            const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
                                            const url = URL.createObjectURL(blob);
                                            const a = document.createElement('a'); a.href = url; a.download = 'actuarial_report_law2_2018.json'; a.click();
                                        }} className="flex items-center gap-2 bg-actuary-primary px-4 py-2 rounded-lg text-sm hover:opacity-80 transition-opacity">
                                            <Download size={16} /> Export JSON
                                        </button>
                                    </div>
                                </div>

                                {/* Executive Summary */}
                                <div className="glass-card p-6">
                                    <h4 className="text-lg font-semibold mb-4 text-actuary-primary">📋 Executive Summary</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <div className="bg-white/5 rounded-xl p-4">
                                            <p className="text-xs text-slate-400">Assessment Period</p>
                                            <p className="text-lg font-bold">{report.executive_summary.assessment_period}</p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4">
                                            <p className="text-xs text-slate-400">Population</p>
                                            <p className="text-lg font-bold">{report.executive_summary.population_covered}</p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4">
                                            <p className="text-xs text-slate-400">Solvency Ratio</p>
                                            <p className={`text-lg font-bold ${report.executive_summary.final_solvency_ratio >= 1 ? 'text-actuary-primary' : 'text-actuary-risk'}`}>
                                                {report.executive_summary.final_solvency_ratio}x
                                            </p>
                                        </div>
                                        <div className="bg-white/5 rounded-xl p-4">
                                            <p className="text-xs text-slate-400">Compliance</p>
                                            <p className={`text-sm font-bold ${report.executive_summary.compliance_status.includes('COMPLIANT') && !report.executive_summary.compliance_status.includes('NON') ? 'text-actuary-primary' : 'text-actuary-risk'}`}>
                                                {report.executive_summary.compliance_status}
                                            </p>
                                        </div>
                                    </div>
                                </div>

                                {/* Assumptions */}
                                <div className="glass-card p-6">
                                    <h4 className="text-lg font-semibold mb-4 text-actuary-secondary">⚙️ Actuarial Assumptions</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        {Object.entries(report.assumptions).map(([key, val]: any) => (
                                            <div key={key} className="bg-white/5 rounded-xl p-3 text-center">
                                                <p className="text-xs text-slate-400">{key.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())}</p>
                                                <p className="text-lg font-bold mt-1">{val}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Financial Projections Table */}
                                <div className="glass-card p-6 overflow-x-auto">
                                    <h4 className="text-lg font-semibold mb-4 text-yellow-400">📊 Financial Projections</h4>
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="text-left text-slate-400 border-b border-white/10">
                                                <th className="p-3">Year</th>
                                                <th className="p-3">Revenue (EGP)</th>
                                                <th className="p-3">Expenditure (EGP)</th>
                                                <th className="p-3">Reserve (EGP)</th>
                                                <th className="p-3">Solvency</th>
                                                <th className="p-3">Flags</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {report.financial_projections.map((row: any) => (
                                                <tr key={row.year} className="border-b border-white/5 hover:bg-white/5">
                                                    <td className="p-3 font-medium">{row.year}</td>
                                                    <td className="p-3 text-actuary-primary">{row.total_revenue.toLocaleString()}</td>
                                                    <td className="p-3 text-actuary-risk">{row.total_expenditure.toLocaleString()}</td>
                                                    <td className="p-3">{row.reserve_fund.toLocaleString()}</td>
                                                    <td className={`p-3 font-bold ${row.solvency_ratio >= 1 ? 'text-actuary-primary' : 'text-actuary-risk'}`}>{row.solvency_ratio}x</td>
                                                    <td className="p-3">{row.risk_flags.length > 0 ? `⚠️ ${row.risk_flags.length}` : '✅'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>

                                {/* Narrative Explanation */}
                                <div className="glass-card p-6">
                                    <h4 className="text-lg font-semibold mb-4 text-blue-400">📝 Narrative Explanation</h4>
                                    <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{report.narrative_explanation}</p>
                                </div>

                                {/* Agentic Audit */}
                                {report.agentic_audit && (
                                    <div className="glass-card p-6">
                                        <h4 className="text-lg font-semibold mb-4 text-purple-400">🤖 AI Agentic Audit</h4>
                                        <div className="space-y-3">
                                            {report.agentic_audit.findings && report.agentic_audit.findings.map((f: any, i: number) => (
                                                <div key={i} className="bg-white/5 rounded-xl p-4">
                                                    <p className="text-sm font-medium">{f.agent || `Agent ${i + 1}`}</p>
                                                    <p className="text-xs text-slate-400 mt-1">{f.finding || f.recommendation || JSON.stringify(f)}</p>
                                                </div>
                                            ))}
                                            {!report.agentic_audit.findings && (
                                                <pre className="text-xs text-slate-300 bg-white/5 p-4 rounded-xl overflow-auto">{JSON.stringify(report.agentic_audit, null, 2)}</pre>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Recommendations */}
                                <div className="glass-card p-6">
                                    <h4 className="text-lg font-semibold mb-4 text-actuary-primary">🎯 Recommendations</h4>
                                    <ul className="space-y-3">
                                        {report.recommendations.map((rec: string, i: number) => (
                                            <li key={i} className="flex items-start gap-3 bg-white/5 rounded-xl p-4">
                                                <span className="text-actuary-primary font-bold">{i + 1}.</span>
                                                <span className="text-sm text-slate-300">{rec}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>

                                {/* Regenerate Button */}
                                <div className="flex justify-center">
                                    <button onClick={() => { setReport(null); fetchReport(); }}
                                        className="flex items-center gap-2 bg-actuary-secondary px-6 py-3 rounded-xl text-sm font-medium hover:opacity-80 transition-opacity">
                                        <RefreshCcw size={16} /> Regenerate Report
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                )}
            </main>
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
                <p className={`text-xs mt-2 font-medium ${danger ? 'text-actuary-risk' : 'text-actuary-primary'}`}>{trend}</p>
            </div>
            <div className="p-3 bg-white/5 rounded-xl">{icon}</div>
        </div>
    )
}
