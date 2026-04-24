import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';

export default function ServiceCard({ service }) {
  const router = useRouter();
  const [hourlyData, setHourlyData] = useState([]);

  useEffect(() => {
    fetchHourlyData();
  }, [service.name]);

  const fetchHourlyData = async () => {
    try {
      const res = await fetch(`http://localhost:5001/api/service/${encodeURIComponent(service.name)}`);
      const data = await res.json();
      
      if (data.data) {
        // Group by hour and calculate averages
        const hourlyMap = {};
        data.data.forEach(record => {
          const hour = new Date(record.timestamp).toISOString().slice(0, 13); // YYYY-MM-DDTHH
          if (!hourlyMap[hour]) {
            hourlyMap[hour] = { latencies: [], count: 0 };
          }
          if (record.latency !== 'na') {
            hourlyMap[hour].latencies.push(parseFloat(record.latency));
          }
          hourlyMap[hour].count++;
        });

        // Convert to array and calculate averages
        const hourly = Object.entries(hourlyMap)
          .map(([hour, data]) => ({
            hour,
            avg_latency: data.latencies.length > 0 
              ? data.latencies.reduce((a, b) => a + b, 0) / data.latencies.length 
              : null
          }))
          .sort((a, b) => a.hour.localeCompare(b.hour));

        setHourlyData(hourly);
      }
    } catch (error) {
      console.error('Error fetching hourly data:', error);
    }
  };

  const getBarColor = (latency) => {
    if (latency === null) return 'bg-red-600';
    if (latency < 40) return 'bg-green-500';
    if (latency < 100) return 'bg-yellow-500';
    if (latency < 200) return 'bg-orange-500';
    return 'bg-red-500';
  };

  const consecutiveDownHours = () => {
    let count = 0;
    for (let i = hourlyData.length - 1; i >= 0; i--) {
      if (hourlyData[i].avg_latency === null) count++;
      else break;
    }
    return count;
  };

  const isLongDown = consecutiveDownHours() >= 10;

  return (
    <div
      onClick={() => router.push(`/service/${encodeURIComponent(service.name)}`)}
      className="bg-gray-800 border border-gray-700 rounded-lg p-4 cursor-pointer hover:border-gray-600 transition-colors"
    >
      <div className="text-right mb-3 font-semibold">{service.name}</div>
      
      {isLongDown ? (
        <div className="text-center py-8 text-red-400">خارج از دسترس</div>
      ) : (
        <div className="flex gap-1 h-20 items-end">
          {hourlyData.slice(-24).map((hour, idx) => (
            <div
              key={idx}
              className={`flex-1 ${getBarColor(hour.avg_latency)} rounded-sm`}
              style={{ height: hour.avg_latency ? `${Math.min(100, (hour.avg_latency / 200) * 100)}%` : '100%' }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
