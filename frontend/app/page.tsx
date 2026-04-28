import Header from "./components/Header";
import Footer from "./components/Footer";
import ServiceCard from "./components/ServiceCard";
import { getServiceBuckets } from "@/lib/api";

export default async function Home() {

  const services = await getServiceBuckets();

  return (
    <main className="container">

      <Header/>

      <hr/>

      {services.map(s => (
        <ServiceCard
          key={s.service}
          name={s.service}
          buckets={s.buckets}
        />
      ))}

      <Footer/>

    </main>
  );
}
