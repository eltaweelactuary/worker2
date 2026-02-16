"use client"
import { useState, useEffect, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, Users, AlertTriangle, Coins, RefreshCcw, LayoutDashboard, ShieldAlert, BarChart3, Bot, Settings, FileText, Download, Play, Upload, Database, CheckCircle } from 'lucide-react';
import ChatBox from '../components/ChatBox';
import * as XLSX from 'xlsx';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://egypt-actuarial-api-v4-112458895076.europe-west1.run.app';

type TabId = 'import' | 'overview' | 'solvency' | 'risk' | 'actuary' | 'reports' | 'config';

const DEFAULT_CONFIG = {
    wage_inflation: 0.07, medical_inflation: 0.12,
    investment_return_rate: 0.10, admin_expense_pct: 0.04,
    projection_years: 10, population_size: 1000
};

export default function Dashboard() {
    const [activeTab, setActiveTab] = useState<TabId>('import');
    const [config, setConfig] = useState({ ...DEFAULT_CONFIG });
    const [dataLoaded, setDataLoaded] = useState(false);
    const [dataStats, setDataStats] = useState<any>(null);
    const [dataSample, setDataSample] = useState<any[]>([]);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [data, setData] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [apiOnline, setApiOnline] = useState(false);
    const [metrics, setMetrics] = useState({ reserve: "—", solvencyRatio: "—", riskCount: 0 });

    const [mcData, setMcData] = useState<any>(null);
    const [mcLoading, setMcLoading] = useState(false);
    const [mlData, setMlData] = useState<any>(null);
    const [mlLoading, setMlLoading] = useState(false);
    const [report, setReport] = useState<any>(null);
    const [reportLoading, setReportLoading] = useState(false);

    // ─── Data Import ───
    const loadSampleData = async (size = 1000) => {
        setLoading(true); setError(null);
        try {
            const res = await fetch(`${API_URL}/sample-data?size=${size}`);
            const result = await res.json();
            setDataStats(result.statistics);
            setDataSample(result.sample);
            setConfig(c => ({ ...c, population_size: result.rows }));
            setDataLoaded(true);
            setApiOnline(true);
        } catch (err: any) { setError(err.message); setApiOnline(false); }
        finally { setLoading(false); }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setLoading(true); setError(null);
        try {
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Upload failed');
            }
            const result = await res.json();
            setDataStats(result.statistics);
            setDataSample(result.sample);
            setConfig(c => ({ ...c, population_size: result.rows }));
            setDataLoaded(true);
            setApiOnline(true);
        } catch (err: any) { setError(err.message); }
        finally { setLoading(false); }
    };

    // ─── Simulation ───
    const runSimulation = async (cfg = config) => {
        setLoading(true); setError(null);
        try {
            const res = await fetch(`${API_URL}/simulate`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cfg)
            });
            const result = await res.json();
            const projections = result.projections.map((p: any) => ({
                name: `Y${p.Year}`, revenue: p.Total_Revenue,
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
        } catch (err: any) { setError(err.message); setApiOnline(false); }
        finally { setLoading(false); }
    };

    const runMonteCarlo = async () => {
        setMcLoading(true);
        try {
            const res = await fetch(`${API_URL}/monte-carlo`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...config, population_size: 500 })
            });
            setMcData(await res.json());
        } catch (err) { setError("Monte Carlo failed"); }
        finally { setMcLoading(false); }
    };

    const runML = async () => {
        setMlLoading(true);
        try {
            const res = await fetch(`${API_URL}/ml/analysis?population_size=${config.population_size}`, { method: 'POST' });
            setMlData(await res.json());
        } catch (err) { setError("ML failed"); }
        finally { setMlLoading(false); }
    };

    const runReport = async () => {
        setReportLoading(true);
        try {
            const res = await fetch(`${API_URL}/report`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            setReport(await res.json());
        } catch (err) { setError("Report failed"); }
        finally { setReportLoading(false); }
    };

    // Auto-fetch on tab switch
    useEffect(() => {
        if (activeTab === 'overview' && data.length === 0 && dataLoaded) runSimulation();
        if (activeTab === 'solvency' && !mcData && dataLoaded) runMonteCarlo();
        if (activeTab === 'risk' && !mlData && dataLoaded) runML();
        if (activeTab === 'reports' && !report && dataLoaded) runReport();
    }, [activeTab]);

    const runAll = () => {
        setMcData(null); setMlData(null); setReport(null); setData([]);
        runSimulation();
        setActiveTab('overview');
    };

    const tabs: { id: TabId; label: string; icon: any }[] = [
        { id: 'import', label: 'Data Import', icon: <Upload size={20} /> },
        { id: 'overview', label: 'Executive Overview', icon: <LayoutDashboard size={20} /> },
        { id: 'solvency', label: 'Solvency Analytics', icon: <BarChart3 size={20} /> },
        { id: 'risk', label: 'Risk Monitoring', icon: <ShieldAlert size={20} /> },
        { id: 'actuary', label: 'Gemini Actuary', icon: <Bot size={20} /> },
        { id: 'reports', label: 'Reports', icon: <FileText size={20} /> },
        { id: 'config', label: 'System Config', icon: <Settings size={20} /> },
    ];

    return (
        <div className="flex h-screen overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 glass-card m-4 mr-0 flex flex-col p-6 shrink-0">
                <div className="mb-10">
                    <h1 className="text-xl font-bold gradient-text">UHI PORTAL</h1>
                    <p className="text-xs text-slate-400 mt-1">Actuarial Dashboard v4.0</p>
                </div>
                <nav className="flex-1 space-y-2">
                    {tabs.map((tab, i) => {
                        const disabled = tab.id !== 'import' && tab.id !== 'config' && !dataLoaded;
                        return (
                            <div key={tab.id}
                                onClick={() => !disabled && setActiveTab(tab.id)}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${disabled ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer hover:bg-white/5'} ${activeTab === tab.id ? 'bg-white/10 text-actuary-primary border-r-4 border-actuary-primary' : 'text-slate-400'}`}>
                                {tab.icon}
                                <span className="font-medium text-sm">{tab.label}</span>
                                {i === 0 && !dataLoaded && <span className="ml-auto text-xs px-2 py-0.5 bg-actuary-primary/20 text-actuary-primary rounded-full">Start</span>}
                                {i === 0 && dataLoaded && <CheckCircle size={14} className="ml-auto text-actuary-primary" />}
                            </div>
                        );
                    })}
                </nav>
            </aside>

            {/* Main */}
            <main className="flex-1 overflow-y-auto p-8">
                <header className="flex justify-between items-center mb-8">
                    <div>
                        <h2 className="text-3xl font-semibold tracking-tight">{tabs.find(t => t.id === activeTab)?.label}</h2>
                        <p className="text-slate-400">Law 2/2018 — Universal Health Insurance</p>
                    </div>
                    <div className="flex gap-4 items-center">
                        <div className="glass-card px-4 py-2 text-sm flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${apiOnline ? 'bg-actuary-primary' : 'bg-actuary-risk'} animate-pulse`}></div>
                            API: {apiOnline ? 'Online' : 'Offline'}
                        </div>
                    </div>
                </header>

                {error && (
                    <div className="glass-card p-4 mb-6 border-actuary-risk/30 bg-actuary-risk/10 text-actuary-risk text-sm">
                        ⚠️ {error} <button onClick={() => setError(null)} className="ml-4 underline">Dismiss</button>
                    </div>
                )}

                {/* ═════ TAB: Data Import ═════ */}
                {activeTab === 'import' && (
                    <div className="max-w-4xl mx-auto space-y-6">
                        {/* Upload Zone */}
                        <div className="glass-card p-8">
                            <h3 className="text-lg font-semibold mb-2 text-actuary-primary flex items-center gap-2"><Upload size={20} /> Import Population Data</h3>
                            <p className="text-sm text-slate-400 mb-6">Upload a CSV file with population data, or use the built-in sample data generator for testing.</p>

                            <input type="file" accept=".csv" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Upload CSV */}
                                <div onClick={() => fileInputRef.current?.click()}
                                    className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-actuary-primary/50 transition-all cursor-pointer group">
                                    <Upload size={40} className="mx-auto text-slate-500 group-hover:text-actuary-primary transition-colors" />
                                    <p className="text-sm font-medium mt-4">Upload CSV File</p>
                                    <p className="text-xs text-slate-500 mt-1">Drag & drop or click to browse</p>
                                </div>

                                {/* Sample Data */}
                                <div className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-actuary-secondary/50 transition-all cursor-pointer group"
                                    onClick={() => loadSampleData(config.population_size)}>
                                    <Database size={40} className="mx-auto text-slate-500 group-hover:text-actuary-secondary transition-colors" />
                                    <p className="text-sm font-medium mt-4">Use Sample Data</p>
                                    <p className="text-xs text-slate-500 mt-1">{config.population_size.toLocaleString()} simulated citizens</p>
                                </div>
                            </div>
                        </div>

                        {/* Required Format */}
                        <div className="glass-card p-6">
                            <h4 className="text-sm font-semibold mb-3 text-slate-300">📋 Required CSV Columns</h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                {['Age', 'Gender', 'EmploymentStatus', 'MonthlyWage', 'SpouseInSystem', 'ChildrenCount', 'EstimatedAnnualCost'].map(col => (
                                    <div key={col} className="bg-white/5 rounded-lg px-3 py-2 text-xs font-mono text-actuary-primary">{col}</div>
                                ))}
                            </div>
                        </div>

                        {loading && <Spinner />}

                        {/* Data Preview (after load) */}
                        {dataLoaded && dataStats && (
                            <>
                                <div className="glass-card p-6 border border-actuary-primary/20">
                                    <h4 className="text-lg font-semibold mb-4 text-actuary-primary flex items-center gap-2">
                                        <CheckCircle size={20} /> Data Loaded Successfully
                                    </h4>
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                        <MetricBox label="Population" value={`${config.population_size.toLocaleString()}`} />
                                        <MetricBox label="Avg Age" value={`${dataStats.avg_age} yrs`} />
                                        <MetricBox label="Avg Wage" value={`${Math.round(dataStats.avg_wage).toLocaleString()} EGP`} />
                                        <MetricBox label="Avg Cost" value={`${Math.round(dataStats.avg_cost).toLocaleString()} EGP`} />
                                        <MetricBox label="Gender" value={`M:${dataStats.gender_split?.Male || 0} F:${dataStats.gender_split?.Female || 0}`} />
                                    </div>
                                </div>

                                {/* Sample Table */}
                                {dataSample.length > 0 && (
                                    <div className="glass-card p-6 overflow-x-auto">
                                        <h4 className="text-sm font-semibold mb-3 text-slate-300">📊 Data Preview (First 5 Rows)</h4>
                                        <table className="w-full text-xs">
                                            <thead><tr className="text-left text-slate-400 border-b border-white/10">
                                                {Object.keys(dataSample[0]).map(k => <th key={k} className="p-2">{k}</th>)}
                                            </tr></thead>
                                            <tbody>{dataSample.map((row, i) => (
                                                <tr key={i} className="border-b border-white/5">
                                                    {Object.values(row).map((v: any, j) => <td key={j} className="p-2">{typeof v === 'number' ? v.toLocaleString() : String(v)}</td>)}
                                                </tr>
                                            ))}</tbody>
                                        </table>
                                    </div>
                                )}

                                {/* Proceed Button */}
                                <div className="flex justify-center gap-4">
                                    <button onClick={() => { runSimulation(); setActiveTab('overview'); }} className="btn-primary text-lg px-8 py-4">
                                        <Play size={20} /> Proceed to Dashboard →
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ═════ TAB: Executive Overview ═════ */}
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                            <StatCard title="Total Reserve" value={metrics.reserve} sub="EGP" trend="+12%" icon={<Coins className="text-actuary-primary" />} />
                            <StatCard title="Solvency Ratio" value={metrics.solvencyRatio} sub="x" trend={parseFloat(metrics.solvencyRatio) > 1 ? "Healthy" : "Deficit"} icon={<TrendingUp className="text-actuary-secondary" />} danger={parseFloat(metrics.solvencyRatio) < 1} />
                            <StatCard title="Active Members" value={`${(config.population_size / 1000).toFixed(0)}K`} sub="People" trend="Loaded" icon={<Users className="text-blue-400" />} />
                            <StatCard title="Risk Alerts" value={metrics.riskCount} sub="Flags" trend={metrics.riskCount > 0 ? "Action Needed" : "Stable"} icon={<AlertTriangle className="text-actuary-risk" />} danger={metrics.riskCount > 0} />
                        </div>
                        {loading && <Spinner />}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            <ChartCard title="Revenue vs Expenditure">
                                <AreaChart data={data}>
                                    <defs><linearGradient id="cR" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#10b981" stopOpacity={0.3} /><stop offset="95%" stopColor="#10b981" stopOpacity={0} /></linearGradient></defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} /><YAxis stroke="#94a3b8" fontSize={11} />
                                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} itemStyle={{ color: '#fff' }} />
                                    <Area type="monotone" dataKey="revenue" stroke="#10b981" fillOpacity={1} fill="url(#cR)" strokeWidth={3} />
                                    <Area type="monotone" dataKey="expenditure" stroke="#f43f5e" fillOpacity={0} strokeWidth={2} strokeDasharray="5 5" />
                                </AreaChart>
                            </ChartCard>
                            <ChartCard title="Reserve Accumulation">
                                <BarChart data={data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} /><YAxis stroke="#94a3b8" fontSize={11} />
                                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} />
                                    <Bar dataKey="reserve" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={40} />
                                </BarChart>
                            </ChartCard>
                        </div>
                    </div>
                )}

                {/* ═════ TAB: Solvency Analytics ═════ */}
                {activeTab === 'solvency' && (
                    <div className="space-y-6">
                        {mcLoading && <Spinner />}
                        {mcData && (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <StatCard title="Mean Reserve" value={fmt(mcData.statistics?.mean_reserve)} sub="EGP" trend="Monte Carlo" icon={<BarChart3 className="text-actuary-secondary" />} />
                                    <StatCard title="Std Deviation" value={fmt(mcData.statistics?.std_reserve)} sub="EGP" trend="Volatility" icon={<TrendingUp className="text-actuary-risk" />} />
                                    <StatCard title="P(Deficit)" value={mcData.statistics?.prob_deficit != null ? (mcData.statistics.prob_deficit * 100).toFixed(1) + "%" : "N/A"} sub="" trend="Probability" icon={<AlertTriangle className="text-yellow-400" />} danger={mcData.statistics?.prob_deficit > 0.1} />
                                </div>
                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-medium mb-4">Stochastic Range</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <MetricBox label="5th Pctl (Worst)" value={fmt(mcData.statistics?.p5_reserve)} color="text-actuary-risk" />
                                        <MetricBox label="25th Pctl" value={fmt(mcData.statistics?.p25_reserve)} color="text-yellow-400" />
                                        <MetricBox label="Median" value={fmt(mcData.statistics?.median_reserve)} color="text-actuary-secondary" />
                                        <MetricBox label="95th Pctl (Best)" value={fmt(mcData.statistics?.p95_reserve)} color="text-actuary-primary" />
                                    </div>
                                </div>
                                <div className="flex justify-center">
                                    <button onClick={() => { setMcData(null); runMonteCarlo(); }} className="btn-secondary"><RefreshCcw size={16} /> Re-run Monte Carlo</button>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ═════ TAB: Risk Monitoring ═════ */}
                {activeTab === 'risk' && (
                    <div className="space-y-6">
                        {mlLoading && <Spinner />}
                        {mlData && (
                            <>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <StatCard title="ML Engine" value={mlData.ml_status} sub="" trend="Active" icon={<ShieldAlert className="text-actuary-primary" />} />
                                    <StatCard title="High Risk" value={mlData.insights?.high_risk_count || 0} sub="members" trend="Top 10%" icon={<AlertTriangle className="text-actuary-risk" />} danger />
                                    <StatCard title="Threshold" value={mlData.insights?.high_risk_threshold ? Math.round(mlData.insights.high_risk_threshold).toLocaleString() : "N/A"} sub="EGP/yr" trend="Cost Cutoff" icon={<Coins className="text-yellow-400" />} />
                                </div>
                                <div className="glass-card p-6">
                                    <h3 className="text-lg font-medium mb-4">Risk Segments (K-Means)</h3>
                                    <div className="space-y-3">
                                        {mlData.insights?.avg_cost_by_segment && Object.entries(mlData.insights.avg_cost_by_segment).map(([seg, cost]: any) => (
                                            <div key={seg} className="flex items-center justify-between bg-white/5 rounded-xl p-4">
                                                <div>
                                                    <p className="text-sm font-medium">Segment {seg}</p>
                                                    <p className="text-xs text-slate-400">Severity: {mlData.insights.segment_severity?.[seg]?.toFixed(2)}x</p>
                                                </div>
                                                <p className="text-lg font-bold">{Math.round(cost).toLocaleString()} EGP</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="flex justify-center">
                                    <button onClick={() => { setMlData(null); runML(); }} className="btn-secondary"><RefreshCcw size={16} /> Re-run Analysis</button>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ═════ TAB: Gemini Actuary ═════ */}
                {activeTab === 'actuary' && <div className="max-w-4xl mx-auto"><ChatBox /></div>}

                {/* ═════ TAB: Reports ═════ */}
                {activeTab === 'reports' && (
                    <div className="space-y-6">
                        {reportLoading && <Spinner />}
                        {report && (
                            <>
                                <div className="glass-card p-8">
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <h3 className="text-xl font-bold gradient-text">{report.report_title}</h3>
                                            <p className="text-sm text-slate-400 mt-1">{report.legal_reference}</p>
                                        </div>
                                        <button onClick={() => {
                                            const wb = XLSX.utils.book_new();
                                            const summaryData = [['Field', 'Value'], ['Report', report.report_title], ['Reference', report.legal_reference], ['Period', report.executive_summary.assessment_period], ['Population', report.executive_summary.population_covered], ['Solvency', report.executive_summary.final_solvency_ratio], ['Reserve (EGP)', report.executive_summary.final_reserve_fund_egp], ['Compliance', report.executive_summary.compliance_status], ['Risk Flags', report.executive_summary.total_risk_flags]];
                                            XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(summaryData), 'Executive Summary');
                                            const assData = [['Assumption', 'Value'], ...Object.entries(report.assumptions)];
                                            XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(assData), 'Assumptions');
                                            const projData = [['Year', 'Revenue (EGP)', 'Expenditure (EGP)', 'Reserve (EGP)', 'Solvency Ratio', 'Risk Flags'], ...report.financial_projections.map((r: any) => [r.year, r.total_revenue, r.total_expenditure, r.reserve_fund, r.solvency_ratio, r.risk_flags.length])];
                                            XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(projData), 'Financial Projections');
                                            const recData = [['#', 'Recommendation'], ...report.recommendations.map((r: string, i: number) => [i + 1, r])];
                                            XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(recData), 'Recommendations');
                                            XLSX.writeFile(wb, 'Actuarial_Report_Law2_2018.xlsx');
                                        }} className="btn-primary"><Download size={16} /> Export Excel</button>
                                    </div>
                                </div>

                                <div className="glass-card p-6">
                                    <h4 className="text-lg font-semibold mb-4 text-actuary-primary">📋 Executive Summary</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <MetricBox label="Period" value={report.executive_summary.assessment_period} />
                                        <MetricBox label="Population" value={report.executive_summary.population_covered} />
                                        <MetricBox label="Solvency" value={report.executive_summary.final_solvency_ratio + "x"} color={report.executive_summary.final_solvency_ratio >= 1 ? 'text-actuary-primary' : 'text-actuary-risk'} />
                                        <MetricBox label="Compliance" value={report.executive_summary.compliance_status} color={report.executive_summary.compliance_status.includes('NON') ? 'text-actuary-risk' : 'text-actuary-primary'} />
                                    </div>
                                </div>

                                <div className="glass-card p-6">
                                    <h4 className="text-lg font-semibold mb-4 text-actuary-secondary">⚙️ Assumptions</h4>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        {Object.entries(report.assumptions).map(([k, v]: any) => (
                                            <MetricBox key={k} label={k.replace(/_/g, ' ')} value={v} />
                                        ))}
                                    </div>
                                </div>

                                <div className="glass-card p-6 overflow-x-auto">
                                    <h4 className="text-lg font-semibold mb-4 text-yellow-400">📊 Financial Projections</h4>
                                    <table className="w-full text-sm">
                                        <thead><tr className="text-left text-slate-400 border-b border-white/10">
                                            <th className="p-3">Year</th><th className="p-3">Revenue</th><th className="p-3">Expenditure</th><th className="p-3">Reserve</th><th className="p-3">Solvency</th><th className="p-3">Flags</th>
                                        </tr></thead>
                                        <tbody>{report.financial_projections.map((r: any) => (
                                            <tr key={r.year} className="border-b border-white/5 hover:bg-white/5">
                                                <td className="p-3 font-medium">{r.year}</td>
                                                <td className="p-3 text-actuary-primary">{r.total_revenue.toLocaleString()}</td>
                                                <td className="p-3 text-actuary-risk">{r.total_expenditure.toLocaleString()}</td>
                                                <td className="p-3">{r.reserve_fund.toLocaleString()}</td>
                                                <td className={`p-3 font-bold ${r.solvency_ratio >= 1 ? 'text-actuary-primary' : 'text-actuary-risk'}`}>{r.solvency_ratio}x</td>
                                                <td className="p-3">{r.risk_flags.length > 0 ? `⚠️ ${r.risk_flags.length}` : '✅'}</td>
                                            </tr>
                                        ))}</tbody>
                                    </table>
                                </div>

                                <div className="glass-card p-6">
                                    <h4 className="text-lg font-semibold mb-4 text-blue-400">📝 Narrative</h4>
                                    <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{report.narrative_explanation}</p>
                                </div>

                                {report.agentic_audit && (
                                    <div className="glass-card p-6">
                                        <h4 className="text-lg font-semibold mb-4 text-purple-400">🤖 AI Audit</h4>
                                        <pre className="text-xs text-slate-300 bg-white/5 p-4 rounded-xl overflow-auto max-h-64">{JSON.stringify(report.agentic_audit, null, 2)}</pre>
                                    </div>
                                )}

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

                                <div className="flex justify-center">
                                    <button onClick={() => { setReport(null); runReport(); }} className="btn-secondary"><RefreshCcw size={16} /> Regenerate</button>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* ═════ TAB: System Config ═════ */}
                {activeTab === 'config' && (
                    <div className="max-w-3xl mx-auto space-y-6">
                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-2 text-actuary-primary">⚙️ Actuarial Assumptions</h3>
                            <p className="text-sm text-slate-400 mb-6">Adjust per Law 2/2018 Articles 40-44, then run scenarios.</p>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <SliderInput label="Wage Inflation" value={config.wage_inflation} min={0.01} max={0.20} step={0.01} onChange={(v) => setConfig({ ...config, wage_inflation: v })} />
                                <SliderInput label="Medical Inflation" value={config.medical_inflation} min={0.01} max={0.30} step={0.01} onChange={(v) => setConfig({ ...config, medical_inflation: v })} />
                                <SliderInput label="Investment Return" value={config.investment_return_rate} min={0.01} max={0.20} step={0.01} onChange={(v) => setConfig({ ...config, investment_return_rate: v })} />
                                <SliderInput label="Admin Expense" value={config.admin_expense_pct} min={0.01} max={0.10} step={0.005} onChange={(v) => setConfig({ ...config, admin_expense_pct: v })} />
                                <div>
                                    <label className="text-sm text-slate-400 block mb-2">Projection Years</label>
                                    <select value={config.projection_years} onChange={(e) => setConfig({ ...config, projection_years: parseInt(e.target.value) })}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-actuary-primary">
                                        {[5, 10, 15, 20, 25, 30].map(y => <option key={y} value={y}>{y} Years</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-sm text-slate-400 block mb-2">Population Size</label>
                                    <select value={config.population_size} onChange={(e) => setConfig({ ...config, population_size: parseInt(e.target.value) })}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-actuary-primary">
                                        {[500, 1000, 2000, 5000, 10000].map(s => <option key={s} value={s}>{s.toLocaleString()}</option>)}
                                    </select>
                                </div>
                            </div>
                        </div>

                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4 text-actuary-secondary">🎬 Run Scenarios</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <button onClick={runAll} className="btn-primary w-full justify-center"><Play size={16} /> Run Full Analysis</button>
                                <button onClick={() => { setMcData(null); runMonteCarlo(); setActiveTab('solvency'); }} className="btn-secondary w-full justify-center"><BarChart3 size={16} /> Monte Carlo</button>
                                <button onClick={() => { setReport(null); runReport(); setActiveTab('reports'); }} className="btn-secondary w-full justify-center"><FileText size={16} /> Generate Report</button>
                            </div>
                        </div>

                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4 text-yellow-400">📌 Preset Scenarios</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <button onClick={() => setConfig({ ...DEFAULT_CONFIG })} className="bg-white/5 rounded-xl p-4 text-left hover:bg-white/10 transition-all border border-transparent hover:border-actuary-primary/30">
                                    <p className="text-sm font-medium text-actuary-primary">🟢 Base Case</p><p className="text-xs text-slate-400 mt-1">Default assumptions per Article 40</p>
                                </button>
                                <button onClick={() => setConfig({ ...DEFAULT_CONFIG, medical_inflation: 0.20, wage_inflation: 0.05 })} className="bg-white/5 rounded-xl p-4 text-left hover:bg-white/10 transition-all border border-transparent hover:border-actuary-risk/30">
                                    <p className="text-sm font-medium text-actuary-risk">🔴 Stress Test</p><p className="text-xs text-slate-400 mt-1">High medical inflation (20%), low wages (5%)</p>
                                </button>
                                <button onClick={() => setConfig({ ...DEFAULT_CONFIG, investment_return_rate: 0.15, admin_expense_pct: 0.02 })} className="bg-white/5 rounded-xl p-4 text-left hover:bg-white/10 transition-all border border-transparent hover:border-actuary-primary/30">
                                    <p className="text-sm font-medium text-blue-400">🔵 Optimistic</p><p className="text-xs text-slate-400 mt-1">High returns (15%), low admin (2%)</p>
                                </button>
                                <button onClick={() => setConfig({ ...DEFAULT_CONFIG, projection_years: 30, population_size: 5000 })} className="bg-white/5 rounded-xl p-4 text-left hover:bg-white/10 transition-all border border-transparent hover:border-yellow-400/30">
                                    <p className="text-sm font-medium text-yellow-400">🟡 Long Term</p><p className="text-xs text-slate-400 mt-1">30-year projection, 5K population</p>
                                </button>
                            </div>
                        </div>

                        <div className="glass-card p-6">
                            <h3 className="text-lg font-semibold mb-4 text-slate-300">📋 Active Config</h3>
                            <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                                <MetricBox label="Wage" value={`${(config.wage_inflation * 100).toFixed(0)}%`} />
                                <MetricBox label="Medical" value={`${(config.medical_inflation * 100).toFixed(0)}%`} />
                                <MetricBox label="Return" value={`${(config.investment_return_rate * 100).toFixed(0)}%`} />
                                <MetricBox label="Admin" value={`${(config.admin_expense_pct * 100).toFixed(1)}%`} />
                                <MetricBox label="Years" value={`${config.projection_years}`} />
                                <MetricBox label="Pop." value={`${config.population_size.toLocaleString()}`} />
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    )
}

// ─── Shared Components ───

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

function ChartCard({ title, children }: { title: string; children: any }) {
    return (
        <div className="glass-card p-6 h-96">
            <h3 className="text-lg font-medium mb-4">{title}</h3>
            <ResponsiveContainer width="100%" height="85%">{children}</ResponsiveContainer>
        </div>
    )
}

function MetricBox({ label, value, color = "text-white" }: { label: string; value: string; color?: string }) {
    return (
        <div className="bg-white/5 rounded-xl p-3">
            <p className="text-xs text-slate-400">{label}</p>
            <p className={`text-sm font-bold mt-1 ${color}`}>{value}</p>
        </div>
    )
}

function Spinner() {
    return <div className="flex justify-center p-12"><RefreshCcw className="animate-spin text-actuary-primary" size={32} /></div>;
}

function SliderInput({ label, value, min, max, step, onChange }: { label: string; value: number; min: number; max: number; step: number; onChange: (v: number) => void }) {
    return (
        <div>
            <div className="flex justify-between items-center mb-2">
                <label className="text-sm text-slate-400">{label}</label>
                <span className="text-sm font-bold text-actuary-primary">{(value * 100).toFixed(1)}%</span>
            </div>
            <input type="range" min={min} max={max} step={step} value={value}
                onChange={(e) => onChange(parseFloat(e.target.value))}
                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-actuary-primary" />
            <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>{(min * 100).toFixed(0)}%</span><span>{(max * 100).toFixed(0)}%</span>
            </div>
        </div>
    )
}

function fmt(n: any): string { return n == null ? "N/A" : (n / 1e9).toFixed(2) + "B"; }
