import { useState, useEffect } from 'react';
import axios from 'axios';
import Header from '../components/Header';
import CategoryFilter from '../components/CategoryFilter';
import ServiceCard from '../components/ServiceCard';
import Footer from '../components/Footer';

export default function Home() {
  const [services, setServices] = useState([]);
  const [filter, setFilter] = useState('همه');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchServices();
    const interval = setInterval(fetchServices, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchServices = async () => {
    try {
      const res = await axios.get('http://localhost:5001/api/status');
      const servicesData = res.data.data || [];
      
      const formattedServices = servicesData.map(item => ({
        name: item.service,
        status: item.status,
        dns_status: item.dns,
        tcp_status: item.tcp,
        ping_time: item.latency !== 'na' ? parseFloat(item.latency) : null,
        category: getServiceCategory(item.service)
      }));
      
      setServices(formattedServices);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching services:', error);
      setLoading(false);
    }
  };

  const getServiceCategory = (serviceName) => {
    const externalGeneral = ['google.com', 'gmail.google.com', 'googleapis.com', 'drive.google.com', 'docs.google.com', 'maps.google.com', 'accounts.google.com', 'calendar.google.com', 'fonts.googleapis.com', 'storage.googleapis.com', 'photos.google.com', 'youtube.com', 'ytimg.com', 'googlevideo.com', 'gstatic.com', 'cloudflare.com', '1.1.1.1', 'npmjs.com', 'nodejs.org', 'python.org', 'pypi.org', 'docker.com', 'hub.docker.com', 'cloudfront.net', 'akamai.com', 'openai.com', 'api.openai.com', 'azure.com', 'aws.amazon.com', 's3.amazonaws.com'];
    const internalGeneral = ['arvancloud.ir', 'snap.ir', 'snapp.ir', 'snappfood.ir', 'tapsi.ir', 'digikala.com', 'divar.ir', 'filimo.com', 'namava.ir', 'aparat.com', 'torob.com', 'zoomit.ir', 'shaparak.ir'];
    const externalSpecialized = ['github.com', 'raw.githubusercontent.com', 'api.github.com', 'wikipedia.org', 'yahoo.com', 'bing.com', 'duckduckgo.com', 'stackpathdns.com'];
    const internalSpecialized = ['bankmelli.ir', 'bankmellat.ir', 'sb24.ir', 'refah-bank.ir', 'postbank.ir'];

    if (externalGeneral.includes(serviceName)) return 'عمومی خارجی';
    if (internalGeneral.includes(serviceName)) return 'عمومی داخلی';
    if (externalSpecialized.includes(serviceName)) return 'تخصصی خارجی';
    if (internalSpecialized.includes(serviceName)) return 'تخصصی داخلی';
    return 'دیگر';
  };

  const filteredServices = services.filter(service => {
    if (filter === 'همه') return true;
    return service.category === filter;
  });

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-4">نت رادار - وضعیت برقراری سرویس‌های پر استفاده در ایران</h1>
          <p className="text-gray-400">نت رادار وضعیت دسترسی به برخی از سرویس‌های داخلی و خارجی را نشان می‌دهد. برای دریافت اطلاعات بیشتر در مورد هر سرویس، روی آن کلیک کنید.</p>
        </div>

        <CategoryFilter selected={filter} onSelect={setFilter} />

        {loading ? (
          <div className="text-center py-12">در حال بارگذاری...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredServices.map(service => (
              <ServiceCard key={service.name} service={service} />
            ))}
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
