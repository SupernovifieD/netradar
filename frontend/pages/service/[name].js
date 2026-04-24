import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import Head from 'next/head';
import Header from '../../components/Header';
import Footer from '../../components/Footer';

export default function ServiceDetail() {
  const router = useRouter();
  const { name } = router.query;
  const [service, setService] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!name) return;

    const fetchData = async () => {
      try {
        const [statusRes, historyRes] = await Promise.all([
          fetch(`http://localhost:5001/api/status`),
          fetch(`http://localhost:5001/api/service/${encodeURIComponent(name)}`)
        ]);

        const statusData = await statusRes.json();
        const historyData = await historyRes.json();

        // Find the current service from status endpoint
        const currentService = statusData.data?.find(s => s.service === name);
        
        if (currentService) {
          setService({
            name: currentService.service,
            dns_status: currentService.dns,
            tcp_status: currentService.tcp,
            ping_status: currentService.latency !== 'na',
            ping_time: currentService.latency !== 'na' ? parseFloat(currentService.latency) : null
          });
        }

        // Transform history data
        if (historyData.data) {
          const formattedHistory = historyData.data.map(record => ({
            timestamp: record.timestamp,
            dns_status: record.dns,
            tcp_status: record.tcp,
            ping_status: record.latency !== 'na',
            ping_time: record.latency !== 'na' ? parseFloat(record.latency) : null
          }));
          setHistory(formattedHistory);
        }
      } catch (error) {
        console.error('Error fetching service data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [name]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <p>در حال بارگذاری...</p>
      </div>
    );
  }

  if (!service) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100">
        <Header />
        <main className="container mx-auto px-4 py-8 text-center">
          <p className="text-red-400">سرویس یافت نشد</p>
        </main>
        <Footer />
      </div>
    );
  }

  const getStatusColor = (status) => {
    return status ? 'text-green-400' : 'text-red-400';
  };

  const getStatusText = (status) => {
    return status ? '✓ فعال' : '✗ غیرفعال';
  };

  return (
    <>
      <Head>
        <title>{service.name} - نت رادار</title>
      </Head>
      <div className="min-h-screen bg-gray-900 text-gray-100">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <h1 className="text-3xl font-bold mb-6 border-b-2 border-blue-500 pb-2">{service.name}</h1>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="border border-gray-700 p-4 rounded bg-gray-800">
                <div className="text-sm text-gray-400 mb-1">DNS</div>
                <div className={`text-lg font-bold ${getStatusColor(service.dns_status)}`}>
                  {getStatusText(service.dns_status)}
                </div>
              </div>
              <div className="border border-gray-700 p-4 rounded bg-gray-800">
                <div className="text-sm text-gray-400 mb-1">TCP</div>
                <div className={`text-lg font-bold ${getStatusColor(service.tcp_status)}`}>
                  {getStatusText(service.tcp_status)}
                </div>
              </div>
              <div className="border border-gray-700 p-4 rounded bg-gray-800">
                <div className="text-sm text-gray-400 mb-1">Ping</div>
                <div className={`text-lg font-bold ${getStatusColor(service.ping_status)}`}>
                  {service.ping_time ? `${service.ping_time} ms` : getStatusText(false)}
                </div>
              </div>
            </div>

            <h2 className="text-2xl font-bold mb-4">تاریخچه (۵۰ رکورد اخیر)</h2>
            <div className="border border-gray-700 rounded bg-gray-800 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-2 text-right">زمان</th>
                      <th className="px-4 py-2 text-center">DNS</th>
                      <th className="px-4 py-2 text-center">TCP</th>
                      <th className="px-4 py-2 text-center">Ping</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((record, idx) => (
                      <tr key={idx} className="border-t border-gray-700 hover:bg-gray-750">
                        <td className="px-4 py-2">{new Date(record.timestamp).toLocaleString('fa-IR')}</td>
                        <td className={`px-4 py-2 text-center ${getStatusColor(record.dns_status)}`}>
                          {getStatusText(record.dns_status)}
                        </td>
                        <td className={`px-4 py-2 text-center ${getStatusColor(record.tcp_status)}`}>
                          {getStatusText(record.tcp_status)}
                        </td>
                        <td className={`px-4 py-2 text-center ${getStatusColor(record.ping_status)}`}>
                          {record.ping_time ? `${record.ping_time} ms` : getStatusText(false)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </>
  );
}
