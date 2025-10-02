import React, { useMemo } from 'react';
import { BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, Bar } from 'recharts';

interface FinancialChartProps {
    data: string; // JSON string
}

const formatYAxis = (value: number) => {
    if (value === 0) return '0';
    const absValue = Math.abs(value);
    if (absValue >= 1e6) {
        return (value / 1e6).toFixed(0) + 'M';
    }
    if (absValue >= 1e3) {
        return (value / 1e3).toFixed(0) + 'K';
    }
    return value.toString();
};

const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-gray-700/80 backdrop-blur-sm p-3 border border-gray-600 rounded-md shadow-lg">
                <p className="label font-bold text-white">{label}</p>
                {payload.map((pld: any, index: number) => (
                    <p key={index} style={{ color: pld.fill }}>
                        {`${pld.name}: ${formatYAxis(pld.value)}`}
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

export const FinancialChart: React.FC<FinancialChartProps> = ({ data: jsonData }) => {

    const chartData = useMemo(() => {
        try {
            const parsed = JSON.parse(jsonData);
            const { labels, datasets } = parsed;

            return labels.map((label: string, index: number) => {
                const dataPoint: { [key: string]: string | number } = { name: label };
                datasets.forEach((dataset: any) => {
                    dataPoint[dataset.label] = Number(dataset.data[index]);
                });
                return dataPoint;
            });
        } catch (e) {
            console.error("Failed to parse chart data", e);
            return [];
        }
    }, [jsonData]);

    if (!chartData.length) {
        return <div className="text-center text-red-400">Failed to load chart data.</div>;
    }

    const netProfitLabel = "רווח נקי";
    const cashFlowLabel = "תזרים מזומנים תפעולי";

    return (
        <BarChart
            width={730}
            height={250}
            data={chartData}
            margin={{
                top: 5,
                right: 10,
                left: 10,
                bottom: 5,
            }}
        >
            <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
            <XAxis dataKey="name" tick={{ fill: '#A0AEC0', fontSize: 12 }} />
            <YAxis tickFormatter={formatYAxis} tick={{ fill: '#A0AEC0', fontSize: 12 }} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(113, 128, 150, 0.1)' }} />
            <Legend wrapperStyle={{ fontSize: '12px', direction: 'rtl' }} />
            <Bar dataKey={netProfitLabel} fill="#2DD4BF" />
            <Bar dataKey={cashFlowLabel} fill="#F97316" />
        </BarChart>
    );
};